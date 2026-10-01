from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import close_sensor_log_entry, get_sensor_log_entries, insert_sensor_log_entry, SensorLogOverlapError

router = APIRouter(tags=["sensor-log"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _render_list(request: Request, db: Session, error: str | None = None) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "sensor_log.html",
        {"entries": get_sensor_log_entries(db), "error": error},
    )


@router.get("/sensor-log", response_class=HTMLResponse)
def show_sensor_log(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    return _render_list(request, db)


@router.post("/sensor-log", response_class=HTMLResponse)
def create_sensor_log_entry(
    request: Request,
    serial: str = Form(...),
    start_date: date = Form(...),
    start_status_code: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        insert_sensor_log_entry(db, serial, start_date, start_status_code)
    except SensorLogOverlapError as exc:
        return _render_list(request, db, error=str(exc))
    return RedirectResponse(url="/sensor-log", status_code=303)


@router.post("/sensor-log/{entry_id}/close", response_class=HTMLResponse)
def close_sensor_log(
    request: Request,
    entry_id: int,
    end_date: date = Form(...),
    end_status_code: str | None = Form(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    # An empty form field arrives as "", not absent -- normalise it to None so
    # it stores as SQL NULL (the "status code unavailable at close time"
    # scenario), not an empty string.
    closed = close_sensor_log_entry(db, entry_id, end_date, end_status_code or None)
    if closed is None:
        raise HTTPException(status_code=404, detail=f"No sensor-log entry with id {entry_id}")
    return RedirectResponse(url="/sensor-log", status_code=303)
