from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(db_session):
    # db_session fixture truncates glucose_readings before yielding; the
    # TestClient's requests use their own DB session (via get_db), but both
    # talk to the same Postgres instance, so the truncation still applies.
    return TestClient(app)


def test_get_upload_form_renders(client):
    response = client.get("/uploads/libre")

    assert response.status_code == 200
    assert "Upload a FreeStyle Libre export" in response.text


def test_upload_valid_csv_stores_readings(client):
    content = (FIXTURES / "libre_sample.csv").read_bytes()

    response = client.post(
        "/uploads/libre", files={"file": ("libre_sample.csv", content, "text/csv")}
    )

    assert response.status_code == 200
    text = " ".join(response.text.split())
    assert "Stored 7 new readings out of 7 parsed" in text
    assert "Skipped 1 malformed row" in text


def test_reuploading_same_export_creates_no_duplicates(client):
    content = (FIXTURES / "libre_sample.csv").read_bytes()

    first = client.post(
        "/uploads/libre", files={"file": ("libre_sample.csv", content, "text/csv")}
    )
    second = client.post(
        "/uploads/libre", files={"file": ("libre_sample.csv", content, "text/csv")}
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert "Stored 0 new readings out of 7 parsed" in " ".join(second.text.split())


def test_upload_unrecognised_file_is_rejected(client):
    response = client.post(
        "/uploads/libre",
        files={"file": ("not_libre.txt", b"this is not a libreview export", "text/plain")},
    )

    assert response.status_code == 400
    assert "could not be recognised" in response.json()["detail"]
