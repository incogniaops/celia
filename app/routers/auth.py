from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.google import TokenExchangeError, build_authorization_url, exchange_code_for_tokens
from app.config import Settings, get_settings
from app.database import get_db
from app.repository import save_google_health_tokens

router = APIRouter(prefix="/auth/google", tags=["auth"])


@router.get("/login")
def login(request: Request, settings: Settings = Depends(get_settings)) -> RedirectResponse:
    redirect_uri = str(request.url_for("google_auth_callback"))
    url = build_authorization_url(settings.google_client_id, redirect_uri)
    return RedirectResponse(url)


@router.get("/callback", name="google_auth_callback")
def callback(
    request: Request,
    code: str,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> dict:
    redirect_uri = str(request.url_for("google_auth_callback"))

    try:
        tokens = exchange_code_for_tokens(
            code, settings.google_client_id, settings.google_client_secret, redirect_uri
        )
    except TokenExchangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail=(
                "Google did not return a refresh token. Revoke celia's access at "
                "https://myaccount.google.com/permissions and try /auth/google/login again."
            ),
        )

    expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
    save_google_health_tokens(
        db,
        access_token=tokens["access_token"],
        refresh_token=refresh_token,
        access_token_expires_at=expires_at,
    )

    return {"status": "authorised"}
