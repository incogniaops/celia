import pytest
from fastapi.testclient import TestClient

from app.main import app
from test_wyze_parser import FULL_ROW, QUICK_WEIGH_ROW, _export


@pytest.fixture
def client(db_session):
    return TestClient(app)


def test_get_wyze_upload_form_renders(client):
    response = client.get("/uploads/wyze")

    assert response.status_code == 200
    assert "Upload a Wyze body-composition export" in response.text


def test_upload_valid_export_stores_all_fields(client):
    content = _export([FULL_ROW], second_sheet_weight=None)

    response = client.post(
        "/uploads/wyze",
        files={
            "file": (
                "scaledata.xlsx",
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    text = " ".join(response.text.split())
    assert "Stored 15 new data points out of 15 parsed" in text


def test_reuploading_export_produces_no_duplicates(client):
    content = _export([FULL_ROW], second_sheet_weight=None)
    client.post("/uploads/wyze", files={"file": ("scaledata.xlsx", content, "application/octet-stream")})

    second = client.post(
        "/uploads/wyze", files={"file": ("scaledata.xlsx", content, "application/octet-stream")}
    )

    assert second.status_code == 200
    assert "Stored 0 new data points out of 15 parsed" in " ".join(second.text.split())


def test_upload_quick_weigh_row_only_stores_weight_and_bmi(client):
    content = _export([QUICK_WEIGH_ROW], second_sheet_weight=None)

    response = client.post(
        "/uploads/wyze", files={"file": ("scaledata.xlsx", content, "application/octet-stream")}
    )

    assert response.status_code == 200
    assert "Stored 2 new data points out of 2 parsed" in " ".join(response.text.split())


def test_upload_unrecognised_file_is_rejected(client):
    response = client.post(
        "/uploads/wyze",
        files={"file": ("not_wyze.txt", b"this is not a wyze export", "text/plain")},
    )

    assert response.status_code == 400
    assert "Could not read" in response.json()["detail"]
