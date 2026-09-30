from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.models import GlucoseReading, MedicationDose
from app.repository import insert_glucose_readings, upsert_medication_doses


def _reading(ts: datetime, record_type: int, glucose: float) -> dict:
    return {
        "device_timestamp": ts,
        "record_type": record_type,
        "historic_glucose_mgdl": glucose,
        "source": "libreview_csv",
        "raw_row": {"glucose": glucose},
    }


def _dose(ts: datetime, name: str, status: str, note: str | None = None) -> dict:
    return {
        "actual_date": ts,
        "scheduled_date": ts,
        "type": "drug",
        "name": name,
        "value": 1.0,
        "unit": "comprimido(s)",
        "status": status,
        "note": note,
    }


def test_insert_new_readings(db_session):
    readings = [
        _reading(datetime(2026, 8, 1, 0, 5), 0, 240),
        _reading(datetime(2026, 8, 1, 0, 20), 0, 233),
    ]

    inserted = insert_glucose_readings(db_session, readings)

    assert inserted == 2
    stored = db_session.execute(select(GlucoseReading)).scalars().all()
    assert len(stored) == 2


def test_duplicate_timestamp_and_type_is_not_inserted_twice(db_session):
    ts = datetime(2026, 8, 1, 0, 5)
    insert_glucose_readings(db_session, [_reading(ts, 0, 240)])

    # Same (timestamp, record_type) with a different value: should be skipped, not overwritten.
    inserted = insert_glucose_readings(db_session, [_reading(ts, 0, 999)])

    assert inserted == 0
    stored = db_session.execute(select(GlucoseReading)).scalars().all()
    assert len(stored) == 1
    assert float(stored[0].historic_glucose_mgdl) == 240


def test_insert_batches_beyond_a_single_statements_parameter_limit(db_session):
    # Regression test: a single multi-row INSERT for a batch this size would
    # exceed Postgres's 65535-bound-parameter limit before the repository
    # started chunking inserts (discovered uploading the real ~9,000-row
    # LibreView export end-to-end).
    base = datetime(2026, 1, 1)
    readings = [_reading(base + timedelta(minutes=i), 0, 100 + (i % 50)) for i in range(4500)]

    inserted = insert_glucose_readings(db_session, readings)

    assert inserted == 4500
    count = db_session.execute(select(func.count()).select_from(GlucoseReading)).scalar_one()
    assert count == 4500


def test_upsert_medication_dose_inserts_new_rows(db_session):
    ts = datetime(2026, 8, 18, 8, 0)

    processed = upsert_medication_doses(db_session, [_dose(ts, "Metformina tabletas", "confirmed")])

    assert processed == 1
    stored = db_session.execute(select(MedicationDose)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "confirmed"


def test_upsert_medication_dose_deduplicates_same_key_within_one_batch(db_session):
    # Regression test: Postgres rejects an ON CONFLICT DO UPDATE statement
    # that affects the same row twice ("CardinalityViolation"), which a
    # naive upsert hits when the same (actual_date, type, name) appears
    # twice in a single upload -- discovered in the real MyTherapy export,
    # which has 3 such duplicate keys (the same dose logged twice).
    ts = datetime(2026, 9, 28, 20, 0)
    processed = upsert_medication_doses(
        db_session,
        [
            _dose(ts, "Metformina tabletas", "confirmed"),
            _dose(ts, "Metformina tabletas", "rejected", note="duplicate log entry"),
        ],
    )

    assert processed == 1
    stored = db_session.execute(select(MedicationDose)).scalars().all()
    assert len(stored) == 1
    # Last occurrence in the batch wins.
    assert stored[0].status == "rejected"
    assert stored[0].note == "duplicate log entry"


def test_upsert_medication_dose_replaces_changed_status_on_same_key(db_session):
    ts = datetime(2026, 9, 8, 20, 0)
    upsert_medication_doses(db_session, [_dose(ts, "Linagliptin tabletas", "confirmed")])

    # Same (actual_date, type, name), status corrected with a reason -- must
    # update the existing row, not create a second one (this capability's
    # spec delta: unlike glucose readings, MyTherapy data can be corrected).
    processed = upsert_medication_doses(
        db_session, [_dose(ts, "Linagliptin tabletas", "rejected", note="Agotado")]
    )

    assert processed == 1
    stored = db_session.execute(select(MedicationDose)).scalars().all()
    assert len(stored) == 1
    assert stored[0].status == "rejected"
    assert stored[0].note == "Agotado"
