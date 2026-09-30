import pytest

from app.config import get_settings


def test_get_settings_returns_configured_values(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:x@localhost/x")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "shh")

    settings = get_settings()

    assert settings.google_client_id == "abc.apps.googleusercontent.com"
    assert settings.google_client_secret == "shh"


def test_get_settings_fails_fast_without_google_client_id(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_CLIENT_ID"):
        get_settings()


def test_get_settings_fails_fast_without_google_client_secret(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_CLIENT_SECRET"):
        get_settings()
