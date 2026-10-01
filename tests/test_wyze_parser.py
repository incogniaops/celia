import io
import zipfile
from xml.sax.saxutils import escape

import pytest

from app.parsers.wyze import UnrecognisedFileError, parse_wyze_export, sniff_file_type

BODY_COMPOSITION_HEADER = [
    "Number", "Date and Time", "Weight(lb)", "Weight(kg)", "BMI", "Body Fat",
    "Muscle Mass", "Muscle Mass %", "Body Water", "Lean Body Mass", "Bone Mass",
    "Protein", "Visceral Fat", "BMR", "Metabolic Age", "Skeletal Muscle Rate %",
    "Fat Content", "Subcutaneous Fat",
]
HEART_RATE_HEADER = ["Number", "Date and Time", "BPM"]

FULL_ROW = [
    "1", "2026.09.27 08:25 AM", "220.0lb", "100.0kg", "30.0", "25.0%", "110.0lb", "55.0%",
    "50.0%", "150.0lb", "10.0lb", "15.0%", "10", "1800", "40", "40.0%", "50.0lb", "20.0%",
]
QUICK_WEIGH_ROW = [
    "2", "2026.09.28 08:00 AM", "219.0lb", "99.5kg", "29.8",
    "- -", "- -", "- -", "- -", "- -", "- -", "- -", "- -", "- -", "- -", "- -", "- -",
]


def _col(index: int) -> str:
    letters = ""
    index += 1
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _sheet_xml(sections: list[tuple[str | None, list[list[str]]]]) -> str:
    row_xml = []
    row_number = 1
    for title, rows in sections:
        if title is not None:
            row_xml.append(
                f'<row r="{row_number}"><c r="A{row_number}" t="inlineStr">'
                f"<is><t>{escape(title)}</t></is></c></row>"
            )
            row_number += 1
        for row in rows:
            cells = "".join(
                f'<c r="{_col(c)}{row_number}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
                for c, value in enumerate(row)
                if value is not None
            )
            row_xml.append(f'<row r="{row_number}">{cells}</row>')
            row_number += 1
    return (
        '<?xml version="1.0"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{''.join(row_xml)}</sheetData></worksheet>"
    )


def _build_xlsx(sheets: list[list[tuple[str | None, list[list[str]]]]]) -> bytes:
    """Minimal .xlsx containing only what app.parsers.wyze reads."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        sheet_entries = "".join(
            f'<sheet name="Sheet{i + 1}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
            for i in range(len(sheets))
        )
        zf.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{sheet_entries}</sheets></workbook>",
        )
        rel_entries = "".join(
            f'<Relationship Id="rId{i + 1}" Target="worksheets/sheet{i + 1}.xml"/>'
            for i in range(len(sheets))
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{rel_entries}</Relationships>",
        )
        for i, sections in enumerate(sheets):
            zf.writestr(f"xl/worksheets/sheet{i + 1}.xml", _sheet_xml(sections))
    return buffer.getvalue()


def _export(
    body_composition_rows: list[list[str]],
    *,
    heart_rate_rows: list[list[str]] | None = None,
    second_sheet_weight: str | None = "999.0kg",
) -> bytes:
    own_sheet: list[tuple[str | None, list[list[str]]]] = [
        ("Body Composition Data", [BODY_COMPOSITION_HEADER, *body_composition_rows]),
    ]
    if heart_rate_rows is not None:
        own_sheet.append(("Heart Rate", [HEART_RATE_HEADER, *heart_rate_rows]))

    sheets = [own_sheet]
    if second_sheet_weight is not None:
        other_row = list(FULL_ROW)
        other_row[3] = second_sheet_weight
        sheets.append([("Body Composition Data", [BODY_COMPOSITION_HEADER, other_row])])
    return _build_xlsx(sheets)


def test_sniff_recognises_valid_export():
    assert sniff_file_type(_export([FULL_ROW])) == "wyze_xlsx"


def test_sniff_returns_unknown_for_non_xlsx_bytes():
    assert sniff_file_type(b"not an xlsx file at all") == "unknown"


def test_parse_full_bioimpedance_row_returns_all_fields():
    parsed = parse_wyze_export(_export([FULL_ROW], second_sheet_weight=None))

    by_type = {m["metric_type"]: m for m in parsed.metrics}
    assert by_type["weight"]["value"] == 100.0
    assert by_type["weight"]["unit"] == "kg"
    assert by_type["bmi"]["value"] == 30.0
    assert by_type["body_fat"]["value"] == 25.0
    assert by_type["visceral_fat"]["value"] == 10.0
    assert by_type["bmr"]["value"] == 1800.0
    assert by_type["metabolic_age"]["value"] == 40.0
    assert len(parsed.metrics) == 15  # 17 columns minus Number and Weight(lb)


def test_parse_quick_weigh_row_only_returns_weight_and_bmi():
    parsed = parse_wyze_export(_export([QUICK_WEIGH_ROW], second_sheet_weight=None))

    metric_types = {m["metric_type"] for m in parsed.metrics}
    assert metric_types == {"weight", "bmi"}


def test_parse_converts_lb_fields_to_kg():
    parsed = parse_wyze_export(_export([FULL_ROW], second_sheet_weight=None))

    by_type = {m["metric_type"]: m for m in parsed.metrics}
    assert by_type["muscle_mass"]["value"] == pytest.approx(110.0 * 0.45359237)
    assert by_type["lean_body_mass"]["value"] == pytest.approx(150.0 * 0.45359237)
    assert by_type["bone_mass"]["value"] == pytest.approx(10.0 * 0.45359237)
    assert by_type["fat_content"]["value"] == pytest.approx(50.0 * 0.45359237)


def test_parse_ignores_second_sheet():
    parsed = parse_wyze_export(_export([FULL_ROW], second_sheet_weight="999.0kg"))

    weights = [m["value"] for m in parsed.metrics if m["metric_type"] == "weight"]
    assert weights == [100.0]


def test_parse_includes_heart_rate_section_when_present():
    parsed = parse_wyze_export(
        _export([FULL_ROW], heart_rate_rows=[["1", "2026.08.19 06:20 PM", "63/min"]], second_sheet_weight=None)
    )

    heart_rate = next(m for m in parsed.metrics if m["metric_type"] == "heart_rate")
    assert heart_rate["value"] == 63.0
    assert heart_rate["unit"] == "bpm"


def test_parse_succeeds_without_heart_rate_section():
    parsed = parse_wyze_export(_export([FULL_ROW], heart_rate_rows=None, second_sheet_weight=None))

    assert not any(m["metric_type"] == "heart_rate" for m in parsed.metrics)
    assert parsed.skipped_row_count == 0


def test_parse_rejects_unrecognised_header():
    bad_header_row = ["Not", "The", "Expected", "Header"]
    sheets = [[("Body Composition Data", [bad_header_row, ["1", "2", "3", "4"]])]]

    with pytest.raises(UnrecognisedFileError):
        parse_wyze_export(_build_xlsx(sheets))


def test_parse_rejects_non_xlsx_bytes():
    with pytest.raises(UnrecognisedFileError):
        parse_wyze_export(b"not an xlsx file at all")
