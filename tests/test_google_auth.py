from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.auth.google import (
    SCOPES,
    NotAuthorisedError,
    TokenExchangeError,
    build_authorization_url,
    ensure_valid_access_token,
    exchange_code_for_tokens,
    refresh_access_token,
)
from app.config import Settings
from app.repository import save_google_health_tokens


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict:
        return self._payload


_SETTINGS = Settings(
    database_url="unused",
    google_client_id="cid",
    google_client_secret="secret",
    profile_height_m=1.80,
    profile_birth_date=date(2000, 1, 1),
    profile_name="Test User",
)


def test_build_authorization_url_contains_client_id_and_scopes():
    url = build_authorization_url("cid.apps.googleusercontent.com", "http://localhost:8000/auth/google/callback")

    query = parse_qs(urlparse(url).query)
    assert query["client_id"] == ["cid.apps.googleusercontent.com"]
    assert query["redirect_uri"] == ["http://localhost:8000/auth/google/callback"]
    assert query["scope"][0].split(" ") == SCOPES
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]


def test_exchange_code_for_tokens_success(monkeypatch):
    monkeypatch.setattr(
        "app.auth.google.httpx.post",
        lambda *a, **k: _FakeResponse(200, {"access_token": "AT", "refresh_token": "RT", "expires_in": 3599}),
    )

    tokens = exchange_code_for_tokens("the-code", "cid", "secret", "http://x/callback")

    assert tokens == {"access_token": "AT", "refresh_token": "RT", "expires_in": 3599}


def test_exchange_code_for_tokens_failure_raises(monkeypatch):
    monkeypatch.setattr(
        "app.auth.google.httpx.post", lambda *a, **k: _FakeResponse(400, {"error": "invalid_grant"})
    )

    with pytest.raises(TokenExchangeError):
        exchange_code_for_tokens("bad-code", "cid", "secret", "http://x/callback")


def test_refresh_access_token_success(monkeypatch):
    monkeypatch.setattr(
        "app.auth.google.httpx.post",
        lambda *a, **k: _FakeResponse(200, {"access_token": "NEW_AT", "expires_in": 3599}),
    )

    tokens = refresh_access_token("RT", "cid", "secret")

    assert tokens["access_token"] == "NEW_AT"


def test_ensure_valid_access_token_returns_stored_token_without_refreshing(db_session, monkeypatch):
    save_google_health_tokens(
        db_session,
        access_token="AT",
        refresh_token="RT",
        access_token_expires_at=datetime.utcnow() + timedelta(minutes=30),
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("refresh_access_token should not be called when the token is still valid")

    monkeypatch.setattr("app.auth.google.httpx.post", fail_if_called)

    token = ensure_valid_access_token(db_session, _SETTINGS)

    assert token == "AT"


def test_ensure_valid_access_token_refreshes_when_expired(db_session, monkeypatch):
    save_google_health_tokens(
        db_session,
        access_token="OLD_AT",
        refresh_token="RT",
        access_token_expires_at=datetime.utcnow() - timedelta(minutes=5),
    )
    monkeypatch.setattr(
        "app.auth.google.httpx.post",
        lambda *a, **k: _FakeResponse(200, {"access_token": "NEW_AT", "expires_in": 3599}),
    )

    token = ensure_valid_access_token(db_session, _SETTINGS)

    assert token == "NEW_AT"


def test_ensure_valid_access_token_raises_without_any_stored_credential(db_session):
    with pytest.raises(NotAuthorisedError):
        ensure_valid_access_token(db_session, _SETTINGS)


def test_ensure_valid_access_token_propagates_rejected_refresh_token(db_session, monkeypatch):
    # This is the failure path task 2.4 covers at this layer: a rejected
    # refresh token must raise, not silently return a stale/empty token,
    # so the sync routine (group 3) never proceeds to fetch or store data.
    save_google_health_tokens(
        db_session,
        access_token="OLD_AT",
        refresh_token="REVOKED_RT",
        access_token_expires_at=datetime.utcnow() - timedelta(minutes=5),
    )
    monkeypatch.setattr(
        "app.auth.google.httpx.post", lambda *a, **k: _FakeResponse(400, {"error": "invalid_grant"})
    )

    with pytest.raises(TokenExchangeError):
        ensure_valid_access_token(db_session, _SETTINGS)
