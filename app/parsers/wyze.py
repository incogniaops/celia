import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree as ET

_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

DATE_TIME_FORMAT = "%Y.%m.%d %I:%M %p"
MISSING_MARKER = "- -"
_LB_TO_KG = 0.45359237
_NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")

# The export's exact column set -- used both to recognise the file and to
# find each field's column letter (columns can shift between exports, the
# names don't). "Number" and "Weight(lb)" are recognised but never stored:
# the former is a row index, the latter a unit-converted duplicate of
# Weight(kg) (see design.md Decisions).
EXPECTED_HEADER = {
    "Number", "Date and Time", "Weight(lb)", "Weight(kg)", "BMI", "Body Fat",
    "Muscle Mass", "Muscle Mass %", "Body Water", "Lean Body Mass", "Bone Mass",
    "Protein", "Visceral Fat", "BMR", "Metabolic Age", "Skeletal Muscle Rate %",
    "Fat Content", "Subcutaneous Fat",
}

BODY_COMPOSITION_SECTION = "Body Composition Data"
# Optional: a scale model without a handgrip heart-rate sensor has no such
# section at all (see design.md Decisions) -- its absence is not an error.
HEART_RATE_SECTION = "Heart Rate"
EXPECTED_HEART_RATE_HEADER = {"Number", "Date and Time", "BPM"}
_SECTION_TITLES = {BODY_COMPOSITION_SECTION, HEART_RATE_SECTION}

# (header name, metric_type, unit, is_lb_field) -- lb fields are converted
# to kg so they share weight's unit (see design.md Decisions).
_FIELD_SPECS: list[tuple[str, str, str | None, bool]] = [
    ("Weight(kg)", "weight", "kg", False),
    ("BMI", "bmi", None, False),
    ("Body Fat", "body_fat", "%", False),
    ("Muscle Mass", "muscle_mass", "kg", True),
    ("Muscle Mass %", "muscle_mass_percent", "%", False),
    ("Body Water", "body_water_percent", "%", False),
    ("Lean Body Mass", "lean_body_mass", "kg", True),
    ("Bone Mass", "bone_mass", "kg", True),
    ("Protein", "protein_percent", "%", False),
    ("Visceral Fat", "visceral_fat", None, False),
    ("BMR", "bmr", "kcal", False),
    ("Metabolic Age", "metabolic_age", "years", False),
    ("Skeletal Muscle Rate %", "skeletal_muscle_rate_percent", "%", False),
    ("Fat Content", "fat_content", "kg", True),
    ("Subcutaneous Fat", "subcutaneous_fat_percent", "%", False),
]


class UnrecognisedFileError(Exception):
    """Raised when an uploaded file does not match the expected Wyze export format."""


@dataclass
class ParsedBodyCompositionExport:
    metrics: list[dict]
    skipped_row_count: int = 0
    skipped_reasons: list[str] = field(default_factory=list)


def _column_letter(cell_ref: str) -> str:
    return "".join(ch for ch in cell_ref if ch.isalpha())


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return ["".join(t.text or "" for t in si.findall(f".//{_NS}t")) for si in root.findall(f"{_NS}si")]


def _cell_value(cell_el: ET.Element, shared: list[str]) -> str | None:
    cell_type = cell_el.get("t")
    if cell_type == "inlineStr":
        is_el = cell_el.find(f"{_NS}is")
        if is_el is None:
            return None
        return "".join(t_el.text or "" for t_el in is_el.findall(f".//{_NS}t"))
    v_el = cell_el.find(f"{_NS}v")
    if v_el is None or v_el.text is None:
        return None
    if cell_type == "s":
        return shared[int(v_el.text)]
    return v_el.text


def _first_sheet_path(zf: zipfile.ZipFile) -> str:
    """The first <sheet> in xl/workbook.xml's document order -- the Wyze app
    always lists the logged-in account's own profile first, so position is
    the stable signal, never the sheet's name (see design.md Decisions).
    """
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    sheets_el = workbook.find(f"{_NS}sheets")
    first_sheet_el = sheets_el.find(f"{_NS}sheet")
    r_id = first_sheet_el.get(f"{_REL_NS}id")

    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    for rel_el in rels:
        if rel_el.get("Id") == r_id:
            target = rel_el.get("Target")
            return target if target.startswith("xl/") else f"xl/{target}"
    raise UnrecognisedFileError("Could not resolve the workbook's first worksheet")


def _raw_rows(content: bytes) -> dict[int, dict[str, str | None]]:
    """column_letter -> raw cell text, keyed by 1-based row number, for the
    first sheet only (see _first_sheet_path).
    """
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        sheet_path = _first_sheet_path(zf)
        shared = _shared_strings(zf)
        sheet_xml = ET.fromstring(zf.read(sheet_path))

    sheet_data = sheet_xml.find(f"{_NS}sheetData")
    if sheet_data is None:
        raise UnrecognisedFileError("Worksheet has no data")

    rows_by_number: dict[int, dict[str, str | None]] = {}
    for row_el in sheet_data.findall(f"{_NS}row"):
        cells: dict[str, str | None] = {}
        for cell_el in row_el.findall(f"{_NS}c"):
            cells[_column_letter(cell_el.get("r"))] = _cell_value(cell_el, shared)
        rows_by_number[int(row_el.get("r"))] = cells
    return rows_by_number


def _detect_sections(rows_by_number: dict[int, dict[str, str | None]]) -> list[tuple[int, str]]:
    """A section title row has exactly one non-empty cell, whose value is a
    known section name (see design.md Decisions) -- detected generically
    rather than assuming fixed row numbers, since one section's row count
    shifts the next section's starting row.
    """
    sections = []
    for row_number, cells in sorted(rows_by_number.items()):
        values = [v for v in cells.values() if v]
        if len(values) == 1 and values[0] in _SECTION_TITLES:
            sections.append((row_number, values[0]))
    return sections


def _read_sections(
    content: bytes,
) -> dict[str, tuple[dict[str, str], list[tuple[int, dict[str, str | None]]]]]:
    """Returns {section title: (column_letter -> header name, [(row_number, header_name -> raw value)])}."""
    rows_by_number = _raw_rows(content)
    section_starts = _detect_sections(rows_by_number)
    if not section_starts:
        raise UnrecognisedFileError("Worksheet has no recognised section")

    sections: dict[str, tuple[dict[str, str], list[tuple[int, dict[str, str | None]]]]] = {}
    for index, (title_row, title) in enumerate(section_starts):
        header_row = title_row + 1
        next_title_row = section_starts[index + 1][0] if index + 1 < len(section_starts) else None
        if header_row not in rows_by_number:
            continue

        name_by_column = {column: name for column, name in rows_by_number[header_row].items() if name}
        column_by_name = {name: column for column, name in name_by_column.items()}

        data_rows = [
            (row_number, {name: cells.get(column) for name, column in column_by_name.items()})
            for row_number, cells in sorted(rows_by_number.items())
            if row_number > header_row and (next_title_row is None or row_number < next_title_row)
        ]
        sections[title] = (name_by_column, data_rows)
    return sections


def sniff_file_type(content: bytes) -> str:
    """Detect a Wyze body-composition .xlsx export by content, not filename."""
    try:
        sections = _read_sections(content)
    except Exception:
        return "unknown"
    body_composition = sections.get(BODY_COMPOSITION_SECTION)
    if body_composition and set(body_composition[0].values()) == EXPECTED_HEADER:
        return "wyze_xlsx"
    return "unknown"


def _parse_number(raw: str) -> float | None:
    match = _NUMBER_PATTERN.match(raw.strip())
    return float(match.group()) if match else None


def _parse_body_composition_row(named_row: dict[str, str | None], row_number: int) -> list[dict]:
    date_raw = named_row.get("Date and Time")
    if not date_raw:
        raise ValueError("missing Date and Time")
    recorded_at = datetime.strptime(date_raw.strip(), DATE_TIME_FORMAT)

    raw_json = {"row": row_number, **named_row}

    metrics = []
    for header_name, metric_type, unit, is_lb in _FIELD_SPECS:
        raw = named_row.get(header_name)
        if raw is None or raw.strip() == MISSING_MARKER:
            continue
        value = _parse_number(raw)
        if value is None:
            continue
        if is_lb:
            value *= _LB_TO_KG
        metrics.append(
            {
                "metric_type": metric_type,
                "recorded_at": recorded_at,
                "value": value,
                "unit": unit,
                "source_platform": "wyze_export",
                "source_package": None,
                "raw_json": raw_json,
            }
        )
    return metrics


def _parse_heart_rate_row(named_row: dict[str, str | None], row_number: int) -> dict:
    date_raw = named_row.get("Date and Time")
    if not date_raw:
        raise ValueError("missing Date and Time")
    recorded_at = datetime.strptime(date_raw.strip(), DATE_TIME_FORMAT)

    bpm_raw = named_row.get("BPM")
    if bpm_raw is None or bpm_raw.strip() == MISSING_MARKER:
        raise ValueError("missing BPM")
    value = _parse_number(bpm_raw)
    if value is None:
        raise ValueError(f"unparseable BPM value '{bpm_raw}'")

    return {
        "metric_type": "heart_rate",
        "recorded_at": recorded_at,
        "value": value,
        "unit": "bpm",
        "source_platform": "wyze_export",
        "source_package": None,
        "raw_json": {"row": row_number, **named_row},
    }


def parse_wyze_export(content: bytes) -> ParsedBodyCompositionExport:
    """Parse a Wyze "Body Composition Data" .xlsx export, first sheet only.

    Stores every measurement a row has (not just muscle mass -- the user's
    explicit choice, see design.md), skipping any field the scale marked
    `"- -"` (no bioimpedance reading that time) rather than storing it as
    zero or null. Also parses the optional "Heart Rate" section into
    `heart_rate` data points, when present.
    """
    try:
        sections = _read_sections(content)
    except (KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        raise UnrecognisedFileError(
            "Could not read the uploaded file as an .xlsx workbook"
        ) from exc

    body_composition = sections.get(BODY_COMPOSITION_SECTION)
    if body_composition is None or set(body_composition[0].values()) != EXPECTED_HEADER:
        raise UnrecognisedFileError("File does not match the expected Wyze body-composition format")

    metrics: list[dict] = []
    skipped_reasons: list[str] = []

    for row_number, named_row in body_composition[1]:
        try:
            metrics.extend(_parse_body_composition_row(named_row, row_number))
        except (KeyError, ValueError) as exc:
            skipped_reasons.append(f"row {row_number}: {exc}")

    heart_rate = sections.get(HEART_RATE_SECTION)
    if heart_rate is not None and set(heart_rate[0].values()) == EXPECTED_HEART_RATE_HEADER:
        for row_number, named_row in heart_rate[1]:
            try:
                metrics.append(_parse_heart_rate_row(named_row, row_number))
            except (KeyError, ValueError) as exc:
                skipped_reasons.append(f"row {row_number}: {exc}")

    return ParsedBodyCompositionExport(
        metrics=metrics,
        skipped_row_count=len(skipped_reasons),
        skipped_reasons=skipped_reasons,
    )
