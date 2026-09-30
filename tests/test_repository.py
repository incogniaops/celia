from datetime import datetime, timedelta

from sqlalchemy import func, select

from app.models import GlucoseReading
from app.repository import insert_glucose_readings


def _reading(ts: datetime, record_type: int, glucose: float) -> dict:
    return {
        "device_timestamp": ts,
        "record_type": record_type,
        "historic_glucose_mgdl": glucose,
        "source": "libreview_csv",
        "raw_row": {"glucose": glucose},
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
