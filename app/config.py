import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    google_client_id: str
    google_client_secret: str


def get_settings() -> Settings:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    google_client_id = os.environ.get("GOOGLE_CLIENT_ID")
    if not google_client_id:
        raise RuntimeError("GOOGLE_CLIENT_ID environment variable is not set")

    google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not google_client_secret:
        raise RuntimeError("GOOGLE_CLIENT_SECRET environment variable is not set")

    return Settings(
        database_url=database_url,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
    )
