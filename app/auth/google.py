from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.config import Settings
from app.repository import get_google_health_credential, save_google_health_tokens

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Refresh a little before actual expiry so a sync in progress doesn't get
# cut off mid-call by the token expiring under it.
_EXPIRY_SAFETY_MARGIN = timedelta(minutes=2)

# Confirmed working live during the hackathon (docs/PS-CELIA-001-...md, US-03):
# health_metrics_and_measurements covers weight/body-fat/heart-rate/daily-
# resting-heart-rate; activity_and_fitness covers steps; sleep covers sleep.
SCOPES = [
    "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
    "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
    "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
]


class TokenExchangeError(Exception):
    """Raised when Google rejects a code/refresh-token exchange."""


def build_authorization_url(client_id: str, redirect_uri: str) -> str:
    """Build the URL the user visits to grant celia access.

    access_type=offline and prompt=consent are both required to reliably
    get a refresh_token back -- without them Google may omit it on a
    repeat authorisation (e.g. if the user already granted access once).
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"


def exchange_code_for_tokens(
    code: str, client_id: str, client_secret: str, redirect_uri: str
) -> dict:
    """Exchange an authorization code for an access + refresh token pair."""
    response = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    if response.status_code != 200:
        raise TokenExchangeError(f"Google rejected the authorization code: {response.text}")
    return response.json()


def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> dict:
    """Exchange a refresh token for a new access token.

    Raises TokenExchangeError if Google rejects the refresh token (e.g.
    revoked) -- the caller is responsible for surfacing this as a failed
    sync pointing the user back at the authorisation flow.
    """
    response = httpx.post(
        TOKEN_ENDPOINT,
        data={
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
        },
    )
    if response.status_code != 200:
        raise TokenExchangeError(f"Google rejected the refresh token: {response.text}")
    return response.json()


class NotAuthorisedError(Exception):
    """Raised when a sync is attempted with no stored credential at all."""


def ensure_valid_access_token(db: Session, settings: Settings) -> str:
    """Return a valid access token, refreshing it first if expired.

    Raises NotAuthorisedError if the user has never completed the
    authorisation flow, and TokenExchangeError if the stored refresh
    token is no longer valid -- both are the caller's cue to surface a
    failed sync pointing at /auth/google/login.
    """
    credential = get_google_health_credential(db)
    if credential is None:
        raise NotAuthorisedError("No Google Health credential on file; visit /auth/google/login first.")

    if credential.access_token_expires_at - _EXPIRY_SAFETY_MARGIN > datetime.utcnow():
        return credential.access_token

    tokens = refresh_access_token(
        credential.refresh_token, settings.google_client_id, settings.google_client_secret
    )
    expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
    updated = save_google_health_tokens(
        db,
        access_token=tokens["access_token"],
        refresh_token=credential.refresh_token,
        access_token_expires_at=expires_at,
    )
    return updated.access_token
