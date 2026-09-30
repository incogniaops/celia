import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime

CSV_TIMESTAMP_FORMAT = "%d-%m-%Y %H:%M"
CSV_HEADER_MARKER = "Dispositivo"

# Reserved record_type for a PDF-derived summary row: real LibreView CSV
# record types are small non-negative integers (0, 1, 5, 6, ...), so this
# value can never collide with a real CSV-sourced reading.
PDF_SUMMARY_RECORD_TYPE = 99

_GENERATED_AT_PATTERN = re.compile(r"(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2})")


class UnrecognisedFileError(Exception):
    """Raised when an uploaded file does not match any recognised LibreView format."""


@dataclass
class ParsedGlucoseExport:
    readings: list[dict]
    skipped_row_count: int = 0
    skipped_reasons: list[str] = field(default_factory=list)


def sniff_file_type(content: bytes) -> str:
    """Detect a LibreView CSV or PDF export by content, not by filename."""
    if content.startswith(b"%PDF"):
        return "libre_pdf"
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return "unknown"
    lines = text.splitlines()
    if len(lines) >= 2 and lines[1].startswith(CSV_HEADER_MARKER):
        return "libre_csv"
    return "unknown"


def parse_libre_csv(content: bytes) -> ParsedGlucoseExport:
    """Parse a LibreView CSV export (skips the metadata line on row 1)."""
    text = content.decode("utf-8-sig")
    lines = text.splitlines()
    if len(lines) < 2 or not lines[1].startswith(CSV_HEADER_MARKER):
        raise UnrecognisedFileError("File does not match the expected LibreView CSV format")

    reader = csv.DictReader(lines[1:])

    readings: list[dict] = []
    skipped_reasons: list[str] = []

    for row_number, row in enumerate(reader, start=3):
        try:
            readings.append(_parse_csv_row(row))
        except (KeyError, ValueError) as exc:
            skipped_reasons.append(f"row {row_number}: {exc}")

    return ParsedGlucoseExport(
        readings=readings,
        skipped_row_count=len(skipped_reasons),
        skipped_reasons=skipped_reasons,
    )


def _parse_csv_row(row: dict) -> dict:
    timestamp_raw = row.get("Marca de hora del dispositivo")
    record_type_raw = row.get("Tipo de registro")
    if not timestamp_raw or not record_type_raw:
        raise ValueError("missing device timestamp or record type")

    device_timestamp = datetime.strptime(timestamp_raw.strip(), CSV_TIMESTAMP_FORMAT)
    record_type = int(record_type_raw)

    return {
        "device_timestamp": device_timestamp,
        "record_type": record_type,
        "historic_glucose_mgdl": _to_float(row.get("Historial de glucosa mg/dL")),
        "scan_glucose_mgdl": _to_float(row.get("Escanear glucosa mg/dL")),
        "rapid_acting_insulin_units": _to_float(row.get("Insulina de acción rápida (unidades)")),
        "long_acting_insulin_units": _to_float(row.get("Insulina de acción prolongada (unidades)")),
        "carbohydrates_grams": _to_float(row.get("Carbohidratos (gramos)")),
        "source": "libreview_csv",
        "raw_row": row,
    }


def _to_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def parse_libre_pdf(content: bytes) -> ParsedGlucoseExport:
    """Best-effort extraction of a LibreView PDF report's summary text.

    This does not attempt to reconstruct per-reading granularity (see
    design.md, Non-Goals). The extracted text is stored as a single
    summary row so nothing the PDF contained is silently discarded, using
    the report's own "Generado el" timestamp when present, or the current
    time otherwise.
    """
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if not text:
        raise UnrecognisedFileError("Could not extract any text from the PDF")

    match = _GENERATED_AT_PATTERN.search(text)
    generated_at = (
        datetime.strptime(match.group(1), CSV_TIMESTAMP_FORMAT) if match else datetime.utcnow()
    )

    reading = {
        "device_timestamp": generated_at,
        "record_type": PDF_SUMMARY_RECORD_TYPE,
        "historic_glucose_mgdl": None,
        "scan_glucose_mgdl": None,
        "rapid_acting_insulin_units": None,
        "long_acting_insulin_units": None,
        "carbohydrates_grams": None,
        "source": "libreview_pdf",
        "raw_row": {"pdf_text": text},
    }

    return ParsedGlucoseExport(readings=[reading])
