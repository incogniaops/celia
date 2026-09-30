from sqlalchemy import UniqueConstraint

from app.models import GlucoseReading, GoogleHealthCredential, HealthMetric, MedicationDose


def test_glucose_reading_has_timestamp_and_type_unique_constraint():
    unique_constraints = [
        c for c in GlucoseReading.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    columns = {col.name for col in unique_constraints[0].columns}
    assert columns == {"device_timestamp", "record_type"}


def test_medication_dose_has_date_type_name_unique_constraint():
    unique_constraints = [
        c for c in MedicationDose.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    columns = {col.name for col in unique_constraints[0].columns}
    assert columns == {"actual_date", "type", "name"}


def test_health_metric_has_type_and_recorded_at_unique_constraint():
    unique_constraints = [
        c for c in HealthMetric.__table__.constraints if isinstance(c, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    columns = {col.name for col in unique_constraints[0].columns}
    assert columns == {"metric_type", "recorded_at"}


def test_google_health_credential_columns_present():
    columns = {c.name for c in GoogleHealthCredential.__table__.columns}
    assert {
        "access_token",
        "refresh_token",
        "access_token_expires_at",
        "last_synced_at",
        "last_sync_status",
        "last_sync_error",
    }.issubset(columns)
