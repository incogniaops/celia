from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import GlucoseReading, MedicationDose

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
