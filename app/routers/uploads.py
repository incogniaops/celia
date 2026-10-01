from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.parsers.libre import UnrecognisedFileError, parse_libre_csv, parse_libre_pdf, sniff_file_type
from app.parsers import mytherapy as mytherapy_parser
from app.parsers import wyze as wyze_parser
from app.repository import insert_glucose_readings, insert_health_metrics, upsert_medication_doses

router = APIRouter(prefix="/uploads", tags=["uploads"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/libre", response_class=HTMLResponse)
def show_libre_upload_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "upload_libre.html", {})


@router.post("/libre", response_class=HTMLResponse)
def upload_libre_export(
    request: Request, file: UploadFile, db: Session = Depends(get_db)
) -> HTMLResponse:
    content = file.file.read()
    file_type = sniff_file_type(content)

    try:
        if file_type == "libre_csv":
            parsed = parse_libre_csv(content)
        elif file_type == "libre_pdf":
            parsed = parse_libre_pdf(content)
        else:
            raise UnrecognisedFileError(
                "The uploaded file could not be recognised as a LibreView CSV or PDF export."
            )
    except UnrecognisedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    inserted = insert_glucose_readings(db, parsed.readings)

    return templates.TemplateResponse(
        request,
        "upload_libre_result.html",
        {
            "inserted": inserted,
            "total_parsed": len(parsed.readings),
            "skipped_row_count": parsed.skipped_row_count,
            "skipped_reasons": parsed.skipped_reasons,
        },
    )


@router.get("/mytherapy", response_class=HTMLResponse)
def show_mytherapy_upload_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "upload_mytherapy.html", {})


@router.post("/mytherapy", response_class=HTMLResponse)
def upload_mytherapy_export(
    request: Request, file: UploadFile, db: Session = Depends(get_db)
) -> HTMLResponse:
    content = file.file.read()
    file_type = mytherapy_parser.sniff_file_type(content)

    try:
        if file_type == "mytherapy_csv":
            parsed = mytherapy_parser.parse_mytherapy_csv(content)
        elif file_type == "mytherapy_pdf":
            parsed = mytherapy_parser.parse_mytherapy_pdf(content)
        else:
            raise mytherapy_parser.UnrecognisedFileError(
                "The uploaded file could not be recognised as a MyTherapy CSV or PDF export."
            )
    except mytherapy_parser.UnrecognisedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    processed = upsert_medication_doses(db, parsed.doses)

    return templates.TemplateResponse(
        request,
        "upload_mytherapy_result.html",
        {
            "processed": processed,
            "total_parsed": len(parsed.doses),
            "discarded_row_count": parsed.discarded_row_count,
            "skipped_row_count": parsed.skipped_row_count,
            "skipped_reasons": parsed.skipped_reasons,
        },
    )


@router.get("/wyze", response_class=HTMLResponse)
def show_wyze_upload_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "upload_wyze.html", {})


@router.post("/wyze", response_class=HTMLResponse)
def upload_wyze_export(request: Request, file: UploadFile, db: Session = Depends(get_db)) -> HTMLResponse:
    content = file.file.read()

    try:
        parsed = wyze_parser.parse_wyze_export(content)
    except wyze_parser.UnrecognisedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    inserted = insert_health_metrics(db, parsed.metrics)

    return templates.TemplateResponse(
        request,
        "upload_wyze_result.html",
        {
            "inserted": inserted,
            "total_parsed": len(parsed.metrics),
            "skipped_row_count": parsed.skipped_row_count,
            "skipped_reasons": parsed.skipped_reasons,
        },
    )
