from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.google import NotAuthorisedError, TokenExchangeError
from app.config import Settings, get_settings
from app.database import get_db
from app.health_metrics_sync import GoogleHealthApiError, sync_health_metrics

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/google-health")
def sync_google_health(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> dict:
    try:
        return sync_health_metrics(db, settings)
    except NotAuthorisedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except TokenExchangeError as exc:
        raise HTTPException(
            status_code=401,
            detail=f"{exc} Visit /auth/google/login to re-authorise.",
        ) from exc
    except GoogleHealthApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
