from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.dashboard_data import (
    get_agp_percentile_bands,
    get_current_biometric_profile,
    get_glucose_summary_stats,
    get_glucose_trend,
    get_insulin_carb_markers,
    get_medication_adherence_calendar,
    get_monthly_glucose_calendar,
    glucose_value,
    has_any_data,
)
from app.database import get_db
from app.timezone import MEXICO_CITY

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

_DEFAULT_RANGE_DAYS = 30
_PRESET_RANGE_DAYS = (7, 14, 30, 90)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _resolve_range(start: str | None, end: str | None) -> tuple[datetime, datetime]:
    # Mexico_City, not UTC, so the default range's boundary matches the
    # user's own calendar day regardless of time of day (see
    # mexico-city-local-time's design.md).
    today = datetime.now(MEXICO_CITY).replace(tzinfo=None)
    end_dt = _parse_date(end) or today
    # -1: _DEFAULT_RANGE_DAYS inclusive calendar days ending on end_dt, not
    # end_dt minus a 30-day timedelta (which spans 31 calendar days) --
    # matches how range-preset-buttons' client-side JS computes each
    # preset's start, so the default range's span equals the "30 days"
    # preset's span exactly (see design.md).
    start_dt = _parse_date(start) or (end_dt - timedelta(days=_DEFAULT_RANGE_DAYS - 1))
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
    # Malformed/missing input falls back silently (see design.md) -- this is
    # a convenience control, not an API contract worth rejecting input on.
    end_dt_inclusive = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_dt, end_dt_inclusive


def _active_preset(start_dt: datetime, end_dt: datetime) -> int | None:
    """Which of the four range presets (see range-preset-buttons' design.md)
    the resolved range matches, so the matching radio button renders
    pre-selected -- None if the range was reached by a non-preset
    start/end (e.g. a direct URL), not an error case.
    """
    today = datetime.now(MEXICO_CITY).replace(tzinfo=None).date()
    if end_dt.date() != today:
        return None
    span_days = (end_dt.date() - start_dt.date()).days + 1
    return span_days if span_days in _PRESET_RANGE_DAYS else None


def _dashboard_context(db: Session, start: str | None, end: str | None) -> dict:
    start_dt, end_dt = _resolve_range(start, end)

    glucose_trend = get_glucose_trend(db, start_dt, end_dt)
    glucose_points = [
        {"timestamp": reading.device_timestamp.isoformat(), "value": glucose_value(reading)}
        for reading in glucose_trend
    ]

    medication_calendar_days, medication_calendar_rows = get_medication_adherence_calendar(
        db, start_dt, end_dt
    )

    return {
        "start": start_dt.date().isoformat(),
        "end": end_dt.date().isoformat(),
        "active_range_days": _active_preset(start_dt, end_dt),
        "glucose_points": glucose_points,
        "markers": get_insulin_carb_markers(db, start_dt, end_dt),
        "medication_calendar_days": medication_calendar_days,
        "medication_calendar_rows": medication_calendar_rows,
        "biometric_profile": get_current_biometric_profile(db),
        "glucose_summary": get_glucose_summary_stats(db, start_dt, end_dt),
        "agp_bands": get_agp_percentile_bands(db, start_dt, end_dt),
        "glucose_calendar_weeks": get_monthly_glucose_calendar(db, start_dt, end_dt),
    }


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request, start: str | None = None, end: str | None = None, db: Session = Depends(get_db)
) -> HTMLResponse:
    if not has_any_data(db):
        return templates.TemplateResponse(request, "dashboard_empty.html", {})

    context = _dashboard_context(db, start, end)

    # The date-range form re-submits this same route via HTMX to refresh
    # without a full page reload (design.md); on that follow-up request we
    # return only the inner fragment, not the full layout/CDN scripts again.
    if request.headers.get("hx-request") == "true":
        return templates.TemplateResponse(request, "dashboard_content.html", context)
    return templates.TemplateResponse(request, "dashboard.html", context)
