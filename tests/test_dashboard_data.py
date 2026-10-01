from datetime import date, datetime

import pytest

from app.dashboard_data import (
    get_age_comparison,
    get_agp_percentile_bands,
    get_bmi,
    get_current_biometric_profile,
    get_glucose_summary_stats,
    get_glucose_trend,
    get_insulin_carb_markers,
    get_medication_adherence_calendar,
    get_medication_doses_in_range,
    get_monthly_glucose_calendar,
    has_any_data,
)
from app.models import GlucoseReading, HealthMetric, MedicationDose
from app.timezone import MEXICO_CITY

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


def test_glucose_summary_stats_is_none_when_no_readings(db_session):
    assert get_glucose_summary_stats(db_session, _START, _END) is None


def test_glucose_summary_stats_bands_at_boundary_values(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5, 0), 0, historic_glucose_mgdl=53),  # very_low
            _glucose_reading(datetime(2026, 8, 5, 1), 0, historic_glucose_mgdl=54),  # low
            _glucose_reading(datetime(2026, 8, 5, 2), 0, historic_glucose_mgdl=69),  # low
            _glucose_reading(datetime(2026, 8, 5, 3), 0, historic_glucose_mgdl=70),  # in_range
            _glucose_reading(datetime(2026, 8, 5, 4), 0, historic_glucose_mgdl=180),  # in_range
            _glucose_reading(datetime(2026, 8, 5, 5), 0, historic_glucose_mgdl=181),  # high
            _glucose_reading(datetime(2026, 8, 5, 6), 0, historic_glucose_mgdl=250),  # high
            _glucose_reading(datetime(2026, 8, 5, 7), 0, historic_glucose_mgdl=251),  # very_high
        ]
    )
    db_session.commit()

    stats = get_glucose_summary_stats(db_session, _START, _END)

    counts = {band: round(pct / 100 * 8) for band, pct in stats["band_percentages"].items()}
    assert counts == {"very_low": 1, "low": 2, "in_range": 2, "high": 2, "very_high": 1}


def test_glucose_summary_stats_gmi_matches_libreview_worked_example(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5, 0), 0, historic_glucose_mgdl=112),
            _glucose_reading(datetime(2026, 8, 5, 1), 0, historic_glucose_mgdl=112),
        ]
    )
    db_session.commit()

    stats = get_glucose_summary_stats(db_session, _START, _END)

    assert stats["average_mgdl"] == 112
    assert round(stats["gmi_percent"], 1) == 6.0
    assert round(stats["gmi_mmol_mol"]) == 42


def test_glucose_summary_stats_days_with_data_counts_distinct_calendar_days(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5, 0), 0, historic_glucose_mgdl=100),
            _glucose_reading(datetime(2026, 8, 5, 12), 0, historic_glucose_mgdl=110),
            _glucose_reading(datetime(2026, 8, 10, 0), 0, historic_glucose_mgdl=120),
        ]
    )
    db_session.commit()

    stats = get_glucose_summary_stats(db_session, _START, _END)

    assert stats["days_with_data"] == 2  # Aug 5 (two readings) and Aug 10
    assert stats["days_in_range"] == 31  # _START = Aug 1, _END = Aug 31 inclusive


def test_glucose_summary_stats_cv_percent(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5, 0), 0, historic_glucose_mgdl=100),
            _glucose_reading(datetime(2026, 8, 5, 1), 0, historic_glucose_mgdl=120),
        ]
    )
    db_session.commit()

    stats = get_glucose_summary_stats(db_session, _START, _END)

    assert round(stats["cv_percent"], 2) == 12.86


def test_agp_percentile_bands_none_when_fewer_than_two_days(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5, 8), 0, historic_glucose_mgdl=100),
            _glucose_reading(datetime(2026, 8, 5, 9), 0, historic_glucose_mgdl=110),
        ]
    )
    db_session.commit()

    assert get_agp_percentile_bands(db_session, _START, _END) is None


def test_agp_percentile_bands_computes_percentiles_and_skips_sparse_buckets(db_session):
    db_session.add_all(
        [
            _glucose_reading(datetime(2026, 8, 5, 8, 0), 0, historic_glucose_mgdl=100),
            _glucose_reading(datetime(2026, 8, 6, 8, 0), 0, historic_glucose_mgdl=120),
            _glucose_reading(datetime(2026, 8, 7, 8, 0), 0, historic_glucose_mgdl=140),
            _glucose_reading(datetime(2026, 8, 5, 9, 0), 0, historic_glucose_mgdl=200),
        ]
    )
    db_session.commit()

    bands = get_agp_percentile_bands(db_session, _START, _END)

    assert len(bands) == 96
    by_minute = {b["minute_of_day"]: b for b in bands}
    assert by_minute[8 * 60]["median"] == 120
    assert by_minute[8 * 60]["p5"] is not None
    assert by_minute[9 * 60]["median"] is None  # only one value that time of day


def test_monthly_glucose_calendar_week_alignment_and_empty_cells(db_session):
    start = datetime(2026, 8, 3)
    end = datetime(2026, 8, 5)
    db_session.add(_glucose_reading(datetime(2026, 8, 3, 8), 0, historic_glucose_mgdl=100))
    db_session.commit()

    weeks = get_monthly_glucose_calendar(db_session, start, end)

    assert all(len(week) == 7 for week in weeks)
    for week in weeks:
        for column, slot in enumerate(week):
            if slot is not None:
                assert slot["date"].weekday() == column  # column 0 = Monday ... 6 = Sunday

    by_date = {slot["date"]: slot for week in weeks for slot in week if slot is not None}
    assert set(by_date) == {date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)}
    assert by_date[date(2026, 8, 3)]["average_mgdl"] == 100
    assert by_date[date(2026, 8, 3)]["band"] == "in_range"
    assert by_date[date(2026, 8, 4)]["average_mgdl"] is None
    assert by_date[date(2026, 8, 4)]["band"] is None


def test_get_current_biometric_profile_returns_most_recent_per_type_and_ignores_steps_sleep(db_session):
    db_session.add_all(
        [
            HealthMetric(metric_type="weight", recorded_at=datetime(2026, 8, 1), value=112, raw_json={}),
            HealthMetric(metric_type="weight", recorded_at=datetime(2026, 8, 20), value=113, raw_json={}),
            HealthMetric(metric_type="body_fat", recorded_at=datetime(2026, 8, 15), value=30, raw_json={}),
            HealthMetric(metric_type="heart_rate", recorded_at=datetime(2026, 8, 15), value=70, raw_json={}),
            HealthMetric(metric_type="steps", recorded_at=datetime(2026, 8, 20), value=5000, raw_json={}),
        ]
    )
    db_session.commit()

    profile = get_current_biometric_profile(db_session)

    # heart_rate is synced but no longer shown on the dashboard (see
    # biometric-cards-redesign's design.md); steps never was.
    assert set(profile.keys()) == {"weight", "body_fat"}
    assert profile["weight"].value == 113


def test_get_bmi_computes_from_weight_and_given_height(db_session):
    profile = {"weight": HealthMetric(metric_type="weight", recorded_at=datetime(2026, 8, 20), value=90, raw_json={})}

    assert get_bmi(profile, height_m=1.80) == pytest.approx(90 / (1.80**2))


def test_get_bmi_is_none_without_weight():
    assert get_bmi({}, height_m=1.80) is None


def test_get_age_comparison_includes_metabolic_age_when_present():
    profile = {
        "metabolic_age": HealthMetric(
            metric_type="metabolic_age", recorded_at=datetime(2026, 8, 20), value=44, raw_json={}
        )
    }
    birth_date = date(1990, 6, 15)

    comparison = get_age_comparison(profile, birth_date)

    today = datetime.now(MEXICO_CITY).date()
    assert comparison["metabolic_age"] == 44.0
    assert comparison["real_age"] == today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )


def test_get_age_comparison_metabolic_age_none_when_absent():
    comparison = get_age_comparison({}, date(1990, 6, 15))

    assert comparison["metabolic_age"] is None
    assert isinstance(comparison["real_age"], int)


def test_has_any_data_false_when_all_tables_empty(db_session):
    assert has_any_data(db_session) is False


def test_has_any_data_true_when_only_one_table_has_rows(db_session):
    db_session.add(MedicationDose(actual_date=datetime(2026, 8, 1), type="drug", name="A", status="confirmed"))
    db_session.commit()

    assert has_any_data(db_session) is True
