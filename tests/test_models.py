from sqlalchemy import UniqueConstraint

from app.models import GlucoseReading


def test_glucose_reading_has_timestamp_and_type_unique_constraint():
    unique_constraints = [
        c for c in GlucoseReading.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    columns = {col.name for col in unique_constraints[0].columns}
    assert columns == {"device_timestamp", "record_type"}
