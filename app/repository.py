from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import GlucoseReading, GoogleHealthCredential, HealthMetric, MedicationDose, SensorLogEntry


class SensorLogOverlapError(Exception):
    """Raised when a new sensor-log entry's date range would overlap an
    existing one (sensor-log's "No overlapping sensor periods" requirement).
    Carries the conflicting entry so callers can name it to the user.
    """

    def __init__(self, conflicting_entry: SensorLogEntry) -> None:
        self.conflicting_entry = conflicting_entry
        super().__init__(
            f"Overlaps existing entry for serial {conflicting_entry.serial!r} "
            f"starting {conflicting_entry.start_date}"
        )


# Single-row convention for the single-user MVP's Google OAuth credential.
_CREDENTIAL_ROW_ID = 1

# Postgres caps a single query at 65535 bound parameters. GlucoseReading has
# 9 insertable columns, so batch well under floor(65535 / 9) = 7281 rows per
# statement. A real LibreView export (~9,000 rows) exceeds the limit in one
# statement -- discovered running this against the full sample export, not
# by the smaller unit/integration test fixtures.
_MAX_ROWS_PER_BATCH = 2000


def insert_glucose_readings(db: Session, readings: list[dict]) -> int:
    """Insert parsed glucose readings, skipping any that duplicate an
    existing (device_timestamp, record_type) pair.

    Returns the number of rows actually inserted (duplicates excluded).
    """
    total_inserted = 0
    for start in range(0, len(readings), _MAX_ROWS_PER_BATCH):
        batch = readings[start : start + _MAX_ROWS_PER_BATCH]
        stmt = pg_insert(GlucoseReading).values(batch)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_glucose_reading_timestamp_type"
        ).returning(GlucoseReading.id)

        result = db.execute(stmt)
        total_inserted += len(result.scalars().all())

    db.commit()
    return total_inserted


def upsert_medication_doses(db: Session, doses: list[dict]) -> int:
    """Insert or update medication doses, keyed on (actual_date, type, name).

    Unlike glucose readings, a re-uploaded MyTherapy export must replace a
    changed row (e.g. a corrected status) rather than skip it, per this
    capability's spec delta -- so this upserts (ON CONFLICT DO UPDATE)
    instead of ignoring conflicts.

    Returns the number of rows processed (inserted or updated).
    """
    # Postgres rejects a single ON CONFLICT DO UPDATE statement that would
    # affect the same conflict-target row twice ("CardinalityViolation") --
    # discovered in the real export, which has 3 rows sharing the same
    # (actual_date, type, name) key (the same dose logged twice at the same
    # second). Deduplicate first, keeping the last occurrence per key, since
    # a later row in the file represents the more current state.
    deduplicated = {(d["actual_date"], d["type"], d["name"]): d for d in doses}
    doses = list(deduplicated.values())

    total_processed = 0
    for start in range(0, len(doses), _MAX_ROWS_PER_BATCH):
        batch = doses[start : start + _MAX_ROWS_PER_BATCH]
        stmt = pg_insert(MedicationDose).values(batch)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_medication_dose_date_type_name",
            set_={
                "value": stmt.excluded.value,
                "unit": stmt.excluded.unit,
                "status": stmt.excluded.status,
                "note": stmt.excluded.note,
            },
        ).returning(MedicationDose.id)

        result = db.execute(stmt)
        total_processed += len(result.scalars().all())

    db.commit()
    return total_processed


def get_google_health_credential(db: Session) -> GoogleHealthCredential | None:
    return db.get(GoogleHealthCredential, _CREDENTIAL_ROW_ID)


def save_google_health_tokens(
    db: Session, access_token: str, refresh_token: str, access_token_expires_at: datetime
) -> GoogleHealthCredential:
    """Store (or update) the single-row Google OAuth credential.

    A fresh authorisation may omit refresh_token if Google decides not to
    reissue one (e.g. a repeat consent without prompt=consent) -- callers
    should only pass a refresh_token they actually received.
    """
    credential = db.get(GoogleHealthCredential, _CREDENTIAL_ROW_ID)
    if credential is None:
        credential = GoogleHealthCredential(id=_CREDENTIAL_ROW_ID, refresh_token=refresh_token)
        db.add(credential)

    credential.access_token = access_token
    credential.refresh_token = refresh_token
    credential.access_token_expires_at = access_token_expires_at
    db.commit()
    db.refresh(credential)
    return credential


def record_sync_result(
    db: Session, status: str, error: str | None, synced_at: datetime
) -> None:
    credential = db.get(GoogleHealthCredential, _CREDENTIAL_ROW_ID)
    if credential is None:
        return
    credential.last_synced_at = synced_at
    credential.last_sync_status = status
    credential.last_sync_error = error
    db.commit()


def insert_health_metrics(db: Session, metrics: list[dict]) -> int:
    """Insert synced health metrics, skipping any that duplicate an existing
    (metric_type, recorded_at) pair -- these are Google's own sensor/device
    readings, so, like glucose readings, the first value stored wins.

    Returns the number of rows actually inserted (duplicates excluded).
    """
    total_inserted = 0
    for start in range(0, len(metrics), _MAX_ROWS_PER_BATCH):
        batch = metrics[start : start + _MAX_ROWS_PER_BATCH]
        stmt = pg_insert(HealthMetric).values(batch)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_health_metric_type_recorded_at"
        ).returning(HealthMetric.id)

        result = db.execute(stmt)
        total_inserted += len(result.scalars().all())

    db.commit()
    return total_inserted


def _sensor_log_overlaps(a_start: date, a_end: date | None, b_start: date, b_end: date | None) -> bool:
    """A null end treats the period as open-ended ([start, +inf)), per
    sensor-log's design.md -- two open entries always satisfy this, which is
    what already guarantees at most one open entry can exist at a time,
    without a separate rule for it.
    """
    a_end_or_inf = a_end or date.max
    b_end_or_inf = b_end or date.max
    return a_start <= b_end_or_inf and b_start <= a_end_or_inf


def insert_sensor_log_entry(
    db: Session, serial: str, start_date: date, start_status_code: str
) -> SensorLogEntry:
    """Insert a new open-ended sensor-log entry, after checking it doesn't
    overlap an existing one (checked only on insert -- see design.md for why
    closing an entry never needs this same check).
    """
    existing = db.execute(select(SensorLogEntry)).scalars().all()
    for entry in existing:
        if _sensor_log_overlaps(start_date, None, entry.start_date, entry.end_date):
            raise SensorLogOverlapError(entry)

    new_entry = SensorLogEntry(serial=serial, start_date=start_date, start_status_code=start_status_code)
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry


def close_sensor_log_entry(
    db: Session, entry_id: int, end_date: date, end_status_code: str | None
) -> SensorLogEntry | None:
    """Close an open sensor-log entry. Returns None if entry_id doesn't
    exist; the caller decides how to surface that (e.g. a 404).
    """
    entry = db.get(SensorLogEntry, entry_id)
    if entry is None:
        return None
    entry.end_date = end_date
    entry.end_status_code = end_status_code
    db.commit()
    db.refresh(entry)
    return entry


def get_sensor_log_entries(db: Session) -> list[SensorLogEntry]:
    """All sensor-log entries, most recently started first."""
    stmt = select(SensorLogEntry).order_by(SensorLogEntry.start_date.desc())
    return list(db.execute(stmt).scalars().all())
