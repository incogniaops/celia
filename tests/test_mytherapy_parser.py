from datetime import datetime
from pathlib import Path

import pytest

from app.parsers.mytherapy import (
    UnrecognisedFileError,
    parse_mytherapy_csv,
    parse_mytherapy_pdf,
    sniff_file_type,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_sniff_csv():
    content = (FIXTURES / "mytherapy_sample.csv").read_bytes()
    assert sniff_file_type(content) == "mytherapy_csv"


def test_sniff_pdf():
    content = (FIXTURES / "mytherapy_sample.pdf").read_bytes()
    assert sniff_file_type(content) == "mytherapy_pdf"


def test_sniff_unknown():
    assert sniff_file_type(b"not a mytherapy file at all") == "unknown"


def test_parse_csv_only_returns_drug_rows():
    content = (FIXTURES / "mytherapy_sample.csv").read_bytes()

    result = parse_mytherapy_csv(content)

    # 6 drug rows, 2 non-persisted (activity + measurement), 1 malformed.
    assert len(result.doses) == 6
    assert all(d["type"] == "drug" for d in result.doses)
    assert result.discarded_row_count == 2
    assert result.skipped_row_count == 1


def test_parse_csv_dose_values():
    content = (FIXTURES / "mytherapy_sample.csv").read_bytes()

    result = parse_mytherapy_csv(content)

    losartan = next(d for d in result.doses if d["name"] == "Losartán tabletas")
    assert losartan["actual_date"] == datetime(2026, 8, 18, 8, 0, 0)
    assert losartan["status"] == "confirmed"
    assert losartan["note"] is None

    combo_drug_names = [d for d in result.doses if d["name"] == "Ketoprofeno, paracetamol tabletas"]
    assert len(combo_drug_names) == 2  # confirmed once, rejected once, different actual_date

    rejected = next(d for d in combo_drug_names if d["status"] == "rejected")
    assert rejected["note"] == "Cambio de medicamento"


def test_parse_csv_rejects_non_mytherapy_file():
    with pytest.raises(UnrecognisedFileError):
        parse_mytherapy_csv(b"col1,col2\nval1,val2\n")


def test_parse_pdf_extracts_summary_text():
    content = (FIXTURES / "mytherapy_sample.pdf").read_bytes()

    result = parse_mytherapy_pdf(content)

    assert len(result.doses) == 1
    dose = result.doses[0]
    assert dose["status"] == "summary"
    assert "Resumen mensual de medicamentos de prueba" in dose["note"]
    assert dose["actual_date"] == datetime(2026, 10, 1, 9, 0, 0)
