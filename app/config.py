import os
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Settings:
    database_url: str
    google_client_id: str
    google_client_secret: str
    profile_height_m: float
    profile_birth_date: date


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

    profile_height_m = os.environ.get("PROFILE_HEIGHT_M")
    if not profile_height_m:
        raise RuntimeError("PROFILE_HEIGHT_M environment variable is not set")

    profile_birth_date = os.environ.get("PROFILE_BIRTH_DATE")
    if not profile_birth_date:
        raise RuntimeError("PROFILE_BIRTH_DATE environment variable is not set")

    return Settings(
        database_url=database_url,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        profile_height_m=float(profile_height_m),
        profile_birth_date=date.fromisoformat(profile_birth_date),
    )
