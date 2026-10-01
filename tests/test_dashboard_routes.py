from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import GlucoseReading, HealthMetric, MedicationDose
from app.routers.dashboard import _active_preset, _resolve_range
from app.timezone import MEXICO_CITY


@pytest.fixture
def client(db_session):
    return TestClient(app)


def _seed(db_session):
    db_session.add_all(
        [
            GlucoseReading(
                device_timestamp=datetime(2026, 8, 10),
                record_type=0,
                historic_glucose_mgdl=120,
                source="libreview_csv",
                raw_row={},
            ),
            GlucoseReading(
                device_timestamp=datetime(2026, 8, 11),
                record_type=5,
                carbohydrates_grams=45,
                source="libreview_csv",
                raw_row={},
            ),
            MedicationDose(
                actual_date=datetime(2026, 8, 10),
                type="drug",
                name="Metformina tabletas",
                status="confirmed",
            ),
            HealthMetric(
                metric_type="weight", recorded_at=datetime(2026, 8, 10), value=113.0, unit="kg", raw_json={}
            ),
            HealthMetric(
                metric_type="body_fat", recorded_at=datetime(2026, 8, 10), value=34.4, unit="%", raw_json={}
            ),
            HealthMetric(
                metric_type="muscle_mass", recorded_at=datetime(2026, 8, 10), value=69.5, unit="kg", raw_json={}
            ),
            HealthMetric(
                metric_type="metabolic_age", recorded_at=datetime(2026, 8, 10), value=44, unit="years", raw_json={}
            ),
        ]
    )
    db_session.commit()


def test_resolve_range_default_today_uses_mexico_city_not_utc():
    # Regression test: this used to be datetime.utcnow(), so opening the
    # dashboard late in the CST evening (already past midnight UTC) would
    # show UTC's next calendar day as "today" (see
    # mexico-city-local-time's design.md).
    _start, end = _resolve_range(None, None)

    assert end.date() == datetime.now(MEXICO_CITY).date()


@pytest.mark.parametrize("days", [7, 14, 30, 90])
def test_active_preset_detects_each_preset_ending_today(days):
    today = datetime.now(MEXICO_CITY).replace(tzinfo=None)
    start_dt = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    end_dt = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    assert _active_preset(start_dt, end_dt) == days


def test_active_preset_is_none_when_end_is_not_today():
    today = datetime.now(MEXICO_CITY).replace(tzinfo=None)
    start_dt = today - timedelta(days=36)
    end_dt = today - timedelta(days=7)

    assert _active_preset(start_dt, end_dt) is None


def test_active_preset_is_none_when_span_matches_no_preset():
    today = datetime.now(MEXICO_CITY).replace(tzinfo=None)
    start_dt = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=9)
    end_dt = today.replace(hour=23, minute=59, second=59, microsecond=999999)

    assert _active_preset(start_dt, end_dt) is None


def test_dashboard_default_range_checks_30_day_radio(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'value="30" onchange="celiaSelectRange(30)" checked' in response.text


def test_dashboard_preset_range_checks_matching_radio(client, db_session):
    _seed(db_session)
    today = datetime.now(MEXICO_CITY).date()
    start = today - timedelta(days=6)

    response = client.get("/dashboard", params={"start": start.isoformat(), "end": today.isoformat()})

    assert response.status_code == 200
    assert 'value="7" onchange="celiaSelectRange(7)" checked' in response.text


def test_dashboard_non_preset_range_checks_no_radio(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "checked" not in response.text


def test_dashboard_shows_empty_state_when_nothing_ingested(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Nothing here yet" in response.text


def test_dashboard_renders_with_real_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Metformina tabletas" in response.text
    assert "113.0" in response.text
    assert "glucose-chart" in response.text


def test_dashboard_shows_adherence_calendar_with_confirmed_status(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Medication adherence" in response.text
    assert "✅" in response.text


def test_dashboard_no_longer_shows_muscle_mass_card(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Muscle Mass" not in response.text


def test_dashboard_shows_bmi_card_after_body_fat(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "<header>BMI</header>" in response.text
    assert "34.9" in response.text  # 113.0 / PROFILE_HEIGHT_M (test default 1.80)**2, rounded
    assert response.text.index("<header>Body Fat</header>") < response.text.index("<header>BMI</header>")


def test_dashboard_shows_age_comparison_delta_not_real_age(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Metabolic age delta" in response.text
    # metabolic_age (44, seeded) - real_age (computed from PROFILE_BIRTH_DATE
    # test default 2000-01-01) -- only the delta appears, never a standalone
    # real-age figure.
    today = datetime.now(MEXICO_CITY).date()
    real_age = today.year - 2000 - ((today.month, today.day) < (1, 1))
    expected_delta = 44 - real_age
    assert f"{expected_delta:+d}" in response.text


def test_dashboard_no_longer_shows_heart_rate_cards(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Heart Rate" not in response.text
    assert "Daily Resting Heart Rate" not in response.text


def test_dashboard_shows_glucose_average_cv_card_and_no_longer_repeats_in_time_in_range(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "<header>Glucose average / CV</header>" in response.text
    assert "Average: <strong>" not in response.text


def test_dashboard_shows_a1c_card_with_glucose_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "A1C (estimated)" in response.text
    assert "Glucose Management Indicator (GMI)" in response.text
    assert "mmol/mol" in response.text
    assert "Data spans" in response.text


def test_dashboard_omits_a1c_card_without_glucose_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-01-01", "end": "2026-01-31"})

    assert response.status_code == 200
    assert "A1C (estimated)" not in response.text


def test_dashboard_shows_time_in_range_summary_with_real_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Time in range" in response.text
    assert "In range (70-180 mg/dL)" in response.text
    assert "CV" in response.text


def test_dashboard_omits_time_in_range_summary_when_no_glucose_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-01-01", "end": "2026-01-31"})

    assert response.status_code == 200
    assert "No glucose readings in this range" in response.text


def test_dashboard_shows_agp_chart_with_multi_day_data(client, db_session):
    db_session.add_all(
        [
            GlucoseReading(
                device_timestamp=datetime(2026, 8, 10, 8),
                record_type=0,
                historic_glucose_mgdl=110,
                source="libreview_csv",
                raw_row={},
            ),
            GlucoseReading(
                device_timestamp=datetime(2026, 8, 11, 8),
                record_type=0,
                historic_glucose_mgdl=130,
                source="libreview_csv",
                raw_row={},
            ),
        ]
    )
    db_session.commit()

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "agp-chart" in response.text


def test_dashboard_omits_agp_chart_with_single_day_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Need at least two days of glucose readings" in response.text


def test_dashboard_shows_monthly_glucose_calendar(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Monthly glucose calendar" in response.text
    assert "120" in response.text


def test_dashboard_range_filters_data(client, db_session):
    _seed(db_session)

    in_range = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})
    out_of_range = client.get("/dashboard", params={"start": "2026-01-01", "end": "2026-01-31"})

    assert "Metformina tabletas" in in_range.text
    assert "Metformina tabletas" not in out_of_range.text
    assert "No medication doses in this range" in out_of_range.text


def test_dashboard_hx_request_returns_fragment_only(client, db_session):
    _seed(db_session)

    response = client.get(
        "/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert "<html" not in response.text
    assert "Metformina tabletas" in response.text


def test_dashboard_malformed_date_falls_back_to_default(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "not-a-date"})

    assert response.status_code == 200
