from datetime import datetime
from pathlib import Path

import pytest

from app.parsers.libre import (
    PDF_SUMMARY_RECORD_TYPE,
    UnrecognisedFileError,
    parse_libre_csv,
    parse_libre_pdf,
    sniff_file_type,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_sniff_csv():
    content = (FIXTURES / "libre_sample.csv").read_bytes()
    assert sniff_file_type(content) == "libre_csv"


def test_sniff_pdf():
    content = (FIXTURES / "libre_sample.pdf").read_bytes()
    assert sniff_file_type(content) == "libre_pdf"


def test_sniff_unknown():
    assert sniff_file_type(b"not a libreview file at all") == "unknown"


def test_parse_csv_skips_malformed_row_and_keeps_good_rows():
    content = (FIXTURES / "libre_sample.csv").read_bytes()

    result = parse_libre_csv(content)

    # 7 well-formed data rows in the fixture, 1 intentionally malformed row.
    assert len(result.readings) == 7
    assert result.skipped_row_count == 1
    assert len(result.skipped_reasons) == 1


def test_parse_csv_reading_values():
    content = (FIXTURES / "libre_sample.csv").read_bytes()

    result = parse_libre_csv(content)

    historic = next(r for r in result.readings if r["record_type"] == 0 and r["historic_glucose_mgdl"] == 240)
    assert historic["device_timestamp"] == datetime(2026, 8, 1, 0, 5)
    assert historic["source"] == "libreview_csv"

    scan = next(r for r in result.readings if r["record_type"] == 1)
    assert scan["scan_glucose_mgdl"] == 260

    with_carbs = next(r for r in result.readings if r["carbohydrates_grams"] == 45)
    assert with_carbs["rapid_acting_insulin_units"] == 3.0
    assert with_carbs["long_acting_insulin_units"] == 1.0


def test_parse_csv_rejects_non_libreview_file():
    with pytest.raises(UnrecognisedFileError):
        parse_libre_csv(b"col1,col2\nval1,val2\n")


def test_parse_pdf_extracts_summary_text():
    content = (FIXTURES / "libre_sample.pdf").read_bytes()

    result = parse_libre_pdf(content)

    assert len(result.readings) == 1
    reading = result.readings[0]
    assert reading["record_type"] == PDF_SUMMARY_RECORD_TYPE
    assert reading["source"] == "libreview_pdf"
    assert "Resumen de glucosa de prueba" in reading["raw_row"]["pdf_text"]
    assert reading["device_timestamp"] == datetime(2026, 10, 1, 9, 0)
