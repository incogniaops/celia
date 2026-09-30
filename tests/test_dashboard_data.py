from datetime import date, datetime

from app.dashboard_data import (
    get_current_biometric_profile,
    get_glucose_trend,
    get_insulin_carb_markers,
    get_medication_adherence_calendar,
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


def test_medication_adherence_calendar_all_confirmed_doses_same_day_shown_confirmed(db_session):
    db_session.add_all(
        [
            MedicationDose(
                actual_date=datetime(2026, 8, 5, 8), type="drug", name="A", status="confirmed"
            ),
            MedicationDose(
                actual_date=datetime(2026, 8, 5, 20), type="drug", name="A", status="confirmed"
            ),
        ]
    )
    db_session.commit()

    days, rows = get_medication_adherence_calendar(db_session, _START, _END)

    assert days[4] == date(2026, 8, 5)
    row_a = next(r for r in rows if r["name"] == "A")
    assert row_a["cells"][4] == "confirmed"


def test_medication_adherence_calendar_any_rejected_dose_same_day_wins(db_session):
    db_session.add_all(
        [
            MedicationDose(
                actual_date=datetime(2026, 8, 5, 8), type="drug", name="A", status="confirmed"
            ),
            MedicationDose(
                actual_date=datetime(2026, 8, 5, 20), type="drug", name="A", status="rejected"
            ),
        ]
    )
    db_session.commit()

    _days, rows = get_medication_adherence_calendar(db_session, _START, _END)

    row_a = next(r for r in rows if r["name"] == "A")
    assert row_a["cells"][4] == "rejected"


def test_medication_adherence_calendar_day_with_no_dose_is_none(db_session):
    db_session.add(
        MedicationDose(actual_date=datetime(2026, 8, 5), type="drug", name="A", status="confirmed")
    )
    db_session.commit()

    _days, rows = get_medication_adherence_calendar(db_session, _START, _END)

    row_a = next(r for r in rows if r["name"] == "A")
    assert row_a["cells"][9] is None  # Aug 10 -- no dose recorded that day


def test_medication_adherence_calendar_excludes_medication_with_doses_only_outside_range(db_session):
    db_session.add(
        MedicationDose(actual_date=datetime(2026, 7, 1), type="drug", name="OutOfRange", status="confirmed")
    )
    db_session.commit()

    _days, rows = get_medication_adherence_calendar(db_session, _START, _END)

    assert all(r["name"] != "OutOfRange" for r in rows)


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
