from datetime import datetime

from app.dashboard_data import (
    get_current_biometric_profile,
    get_glucose_trend,
    get_insulin_carb_markers,
    get_medication_doses_in_range,
    has_any_data,
)
from app.models import GlucoseReading, HealthMetric, MedicationDose

_START = datetime(2026, 8, 1)
_END = datetime(2026, 8, 31)


def _glucose_reading(ts: datetime, record_type: int, **kwargs) -> GlucoseReading:
    return GlucoseReading(
        device_timestamp=ts,
        record_type=record_type,
        source="libreview_csv",
        raw_row={},
        **kwargs,
    )


def test_get_glucose_trend_includes_only_historic_and_scan_types(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5), 0, historic_glucose_mgdl=120),
            _glucose_reading(datetime(2026, 8, 6), 1, scan_glucose_mgdl=130),
            _glucose_reading(datetime(2026, 8, 7), 5, carbohydrates_grams=40),
            _glucose_reading(datetime(2026, 8, 8), 6),
            _glucose_reading(datetime(2026, 7, 1), 0, historic_glucose_mgdl=99),  # out of range
        ]
    )
    db_session.commit()

    trend = get_glucose_trend(db_session, _START, _END)

    assert [r.record_type for r in trend] == [0, 1]
    assert trend[0].device_timestamp < trend[1].device_timestamp


def test_get_insulin_carb_markers_excludes_plain_glucose_rows(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5), 0, historic_glucose_mgdl=120),
            _glucose_reading(datetime(2026, 8, 6), 5, rapid_acting_insulin_units=3.0),
            _glucose_reading(datetime(2026, 8, 7), 5, carbohydrates_grams=45),
        ]
    )
    db_session.commit()

    markers = get_insulin_carb_markers(db_session, _START, _END)

    assert len(markers) == 2
    assert all(m.rapid_acting_insulin_units is not None or m.carbohydrates_grams is not None for m in markers)


def test_get_medication_doses_in_range_orders_by_date_descending(db_session):
    db_session.add_all(
        [
            MedicationDose(actual_date=datetime(2026, 8, 5), type="drug", name="A", status="confirmed"),
            MedicationDose(actual_date=datetime(2026, 8, 10), type="drug", name="B", status="confirmed"),
            MedicationDose(actual_date=datetime(2026, 7, 1), type="drug", name="C", status="confirmed"),
        ]
    )
    db_session.commit()

    doses = get_medication_doses_in_range(db_session, _START, _END)

    assert [d.name for d in doses] == ["B", "A"]


def test_get_current_biometric_profile_returns_most_recent_per_type_and_ignores_steps_sleep(db_session):
    db_session.add_all(
        [
            HealthMetric(metric_type="weight", recorded_at=datetime(2026, 8, 1), value=112, raw_json={}),
            HealthMetric(metric_type="weight", recorded_at=datetime(2026, 8, 20), value=113, raw_json={}),
            HealthMetric(metric_type="heart_rate", recorded_at=datetime(2026, 8, 15), value=70, raw_json={}),
            HealthMetric(metric_type="steps", recorded_at=datetime(2026, 8, 20), value=5000, raw_json={}),
        ]
    )
    db_session.commit()

    profile = get_current_biometric_profile(db_session)

    assert set(profile.keys()) == {"weight", "heart_rate"}
    assert profile["weight"].value == 113


def test_has_any_data_false_when_all_tables_empty(db_session):
    assert has_any_data(db_session) is False


def test_has_any_data_true_when_only_one_table_has_rows(db_session):
    db_session.add(MedicationDose(actual_date=datetime(2026, 8, 1), type="drug", name="A", status="confirmed"))
    db_session.commit()

    assert has_any_data(db_session) is True
