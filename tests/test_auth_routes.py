from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import GoogleHealthCredential


@pytest.fixture
def client(db_session):
    return TestClient(app)


def test_login_redirects_to_google(client):
    response = client.get("/auth/google/login", follow_redirects=False)

    assert response.status_code in (302, 307)
    assert response.headers["location"].startswith("https://accounts.google.com/o/oauth2/v2/auth")


def test_callback_stores_tokens(client, db_session, monkeypatch):
    monkeypatch.setattr(
        "app.routers.auth.exchange_code_for_tokens",
        lambda *a, **k: {"access_token": "AT", "refresh_token": "RT", "expires_in": 3599},
    )

    response = client.get("/auth/google/callback", params={"code": "abc"})

    assert response.status_code == 200
    stored = db_session.execute(select(GoogleHealthCredential)).scalar_one()
    assert stored.access_token == "AT"
    assert stored.refresh_token == "RT"
    assert stored.access_token_expires_at > datetime.utcnow()


def test_callback_rejects_missing_refresh_token(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.auth.exchange_code_for_tokens",
        lambda *a, **k: {"access_token": "AT", "expires_in": 3599},
    )

    response = client.get("/auth/google/callback", params={"code": "abc"})

    assert response.status_code == 400
    assert "refresh token" in response.json()["detail"]
