from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(db_session):
    return TestClient(app)


def test_get_mytherapy_upload_form_renders(client):
    response = client.get("/uploads/mytherapy")

    assert response.status_code == 200
    assert "Upload a MyTherapy export" in response.text


def test_upload_valid_csv_stores_drug_rows_only(client):
    content = (FIXTURES / "mytherapy_sample.csv").read_bytes()

    response = client.post(
        "/uploads/mytherapy", files={"file": ("mytherapy_sample.csv", content, "text/csv")}
    )

    assert response.status_code == 200
    text = " ".join(response.text.split())
    assert "Processed 6 medication doses out of 6 parsed" in text
    assert "Ignored 2 activity/measurement rows" in text
    assert "Skipped 1 malformed row" in text


def test_reuploading_export_with_changed_status_updates_existing_dose(client):
    content = (FIXTURES / "mytherapy_sample.csv").read_bytes()
    client.post("/uploads/mytherapy", files={"file": ("mytherapy_sample.csv", content, "text/csv")})

    # Same file, but with one status corrected: confirmed -> rejected.
    updated_content = content.replace(
        "2026-08-18 08:00:00,2026-08-18 08:00:00,drug,Losartán tabletas,1.00,comprimido(s),confirmed,".encode(),
        "2026-08-18 08:00:00,2026-08-18 08:00:00,drug,Losartán tabletas,1.00,comprimido(s),rejected,Cambio de medicamento".encode(),
    )
    assert updated_content != content  # sanity: the replacement actually matched

    second = client.post(
        "/uploads/mytherapy", files={"file": ("mytherapy_sample.csv", updated_content, "text/csv")}
    )

    assert second.status_code == 200
    # Same 6 drug rows processed (upsert), not 12 -- no duplication.
    assert "Processed 6 medication doses out of 6 parsed" in " ".join(second.text.split())


def test_upload_unrecognised_file_is_rejected(client):
    response = client.post(
        "/uploads/mytherapy",
        files={"file": ("not_mytherapy.txt", b"this is not a mytherapy export", "text/plain")},
    )

    assert response.status_code == 400
    assert "could not be recognised" in response.json()["detail"]
