import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime

CSV_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
CSV_HEADER = "actual_date,scheduled_date,type,name,value,unit,status,note"

# Best-effort: if a date in this shape appears in the PDF's extracted text,
# use it so re-uploading the same report is idempotent (same key). Falls
# back to the current time otherwise -- this fallback path is explicitly
# best-effort (see design.md Non-Goals), not fully speced like the CSV path.
_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})")

DRUG_TYPE = "drug"
# Row types present in a real MyTherapy export that this capability parses
# (to still catch malformed rows across the whole file) but does not store,
# per this change's Non-Goals -- deferred to health-metrics-sync.
NON_PERSISTED_TYPES = {"activity", "measurement"}


class UnrecognisedFileError(Exception):
    """Raised when an uploaded file does not match any recognised MyTherapy format."""


@dataclass
class ParsedMedicationExport:
    doses: list[dict]
    discarded_row_count: int = 0
    """Rows of a recognised, non-persisted type (activity/measurement)."""
    skipped_row_count: int = 0
    skipped_reasons: list[str] = field(default_factory=list)


def sniff_file_type(content: bytes) -> str:
    """Detect a MyTherapy CSV or PDF export by content, not by filename."""
    if content.startswith(b"%PDF"):
        return "mytherapy_pdf"
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return "unknown"
    lines = text.splitlines()
    if lines and lines[0].strip() == CSV_HEADER:
        return "mytherapy_csv"
    return "unknown"


def parse_mytherapy_csv(content: bytes) -> ParsedMedicationExport:
    """Parse a MyTherapy CSV export, returning only `drug` rows as doses.

    `activity` and `measurement` rows are recognised (so a malformed row
    elsewhere in the file is still caught) but discarded -- see this
    capability's design.md Non-Goals.
    """
    text = content.decode("utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != CSV_HEADER:
        raise UnrecognisedFileError("File does not match the expected MyTherapy CSV format")

    reader = csv.DictReader(lines)

    doses: list[dict] = []
    discarded_row_count = 0
    skipped_reasons: list[str] = []

    for row_number, row in enumerate(reader, start=2):
        try:
            row_type = _require(row, "type")
        except ValueError as exc:
            skipped_reasons.append(f"row {row_number}: {exc}")
            continue

        if row_type in NON_PERSISTED_TYPES:
            discarded_row_count += 1
            continue

        if row_type != DRUG_TYPE:
            skipped_reasons.append(f"row {row_number}: unrecognised type '{row_type}'")
            continue

        try:
            doses.append(_parse_drug_row(row))
        except (KeyError, ValueError) as exc:
            skipped_reasons.append(f"row {row_number}: {exc}")

    return ParsedMedicationExport(
        doses=doses,
        discarded_row_count=discarded_row_count,
        skipped_row_count=len(skipped_reasons),
        skipped_reasons=skipped_reasons,
    )


def _require(row: dict, column: str) -> str:
    value = row.get(column)
    if not value:
        raise ValueError(f"missing {column}")
    return value


def _parse_drug_row(row: dict) -> dict:
    actual_date_raw = _require(row, "actual_date")
    name = _require(row, "name")
    status = _require(row, "status")

    return {
        "actual_date": datetime.strptime(actual_date_raw.strip(), CSV_TIMESTAMP_FORMAT),
        "scheduled_date": _parse_optional_timestamp(row.get("scheduled_date")),
        "type": DRUG_TYPE,
        "name": name,
        "value": _to_float(row.get("value")),
        "unit": row.get("unit") or None,
        "status": status,
        "note": row.get("note") or None,
    }


def _parse_optional_timestamp(value: str | None) -> datetime | None:
    if value is None or value.strip() == "":
        return None
    return datetime.strptime(value.strip(), CSV_TIMESTAMP_FORMAT)


def _to_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value)


def parse_mytherapy_pdf(content: bytes) -> ParsedMedicationExport:
    """Best-effort extraction of a MyTherapy PDF report's summary text.

    Same approach as glucose-ingestion's LibreView PDF fallback: no attempt
    to reconstruct per-dose granularity, just capture what text is there.
    """
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if not text:
        raise UnrecognisedFileError("Could not extract any text from the PDF")

    match = _DATE_PATTERN.search(text)
    report_date = (
        datetime.strptime(match.group(1).replace("T", " "), CSV_TIMESTAMP_FORMAT)
        if match
        else datetime.utcnow()
    )

    dose = {
        "actual_date": report_date,
        "scheduled_date": None,
        "type": "pdf_summary",
        "name": "MyTherapy PDF report",
        "value": None,
        "unit": None,
        "status": "summary",
        "note": text,
    }

    return ParsedMedicationExport(doses=[dose])
