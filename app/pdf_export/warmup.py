"""Build-time only (Containerfile task 1.2): renders report.tex.j2 with
synthetic sample data and prints the resulting .tex to stdout, so the
Containerfile compiles the REAL template -- not a hand-maintained stand-in
document -- to warm Tectonic's package cache. A separate warm-up document
was tried first and drifted from the real template twice during
implementation (a different \\documentclass option, a missing pgfplots
library), each time only surfacing as a runtime failure; rendering the real
template here makes that drift structurally impossible.
"""

from datetime import date

from app.pdf_export.render import render_tex
from app.pdf_export.report_data import build_report_context

_SAMPLE_GLUCOSE_SUMMARY = {
    "average_mgdl": 110.0,
    "gmi_percent": 6.0,
    "gmi_mmol_mol": 42.0,
    "cv_percent": 16.0,
    "band_percentages": {
        "very_low": 1.0,
        "low": 2.0,
        "in_range": 90.0,
        "high": 5.0,
        "very_high": 2.0,
    },
}

_SAMPLE_AGP_BANDS = [
    {"minute_of_day": minute, "p5": 80.0, "p25": 95.0, "median": 110.0, "p75": 130.0, "p95": 160.0}
    for minute in range(0, 24 * 60, 15)
]

_SAMPLE_DAILY_WEEKS = [
    [
        {"date": date(2026, 1, 5 + day_index), "points": [(hour * 60, 100.0 + hour) for hour in range(0, 24, 2)]}
        for day_index in range(7)
    ],
    [None] * 7,
]


def build_sample_tex() -> str:
    context = build_report_context(
        profile_name="Warm-up",
        start_date=date(2026, 1, 5),
        end_date=date(2026, 1, 18),
        glucose_summary=_SAMPLE_GLUCOSE_SUMMARY,
        agp_bands=_SAMPLE_AGP_BANDS,
        daily_profile_weeks=_SAMPLE_DAILY_WEEKS,
        generated_date="2026-01-18",
    )
    return render_tex(context)


if __name__ == "__main__":
    print(build_sample_tex())
