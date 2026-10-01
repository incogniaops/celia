from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import GlucoseReading, HealthMetric, MedicationDose


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
                metric_type="muscle_mass", recorded_at=datetime(2026, 8, 10), value=69.5, unit="kg", raw_json={}
            ),
        ]
    )
    db_session.commit()


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


def test_dashboard_shows_muscle_mass_card_with_real_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "Muscle Mass" in response.text
    assert "69.5" in response.text


def test_dashboard_shows_a1c_card_with_glucose_data(client, db_session):
    _seed(db_session)

    response = client.get("/dashboard", params={"start": "2026-08-01", "end": "2026-08-31"})

    assert response.status_code == 200
    assert "A1C (estimated)" in response.text
    assert "Glucose Management Indicator (GMI)" in response.text


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
