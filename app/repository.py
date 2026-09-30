from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import GlucoseReading

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
