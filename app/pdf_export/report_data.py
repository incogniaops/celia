"""Pure-Python preparation of the data-sharing PDF's render context --
derived business rules (band order/colours/targets, stacked-bar segment
geometry, AGP-series filtering) live here, not in the LaTeX template, the
same split celia's HTML dashboard already uses between dashboard_data.py and
its Jinja2 templates.
"""

from datetime import date

# Abbott/LibreView's own report orders bands high-to-low (top-down) in its
# legend; the stacked TikZ bar is built bottom-up from the reverse of this.
BAND_ORDER = ("very_high", "high", "in_range", "low", "very_low")

BAND_LABELS = {
    "very_high": "Muy alta (>250 mg/dL)",
    "high": "Alta (181-250 mg/dL)",
    "in_range": "Rango (70-180 mg/dL)",
    "low": "Baja (54-69 mg/dL)",
    "very_low": "Muy baja (<54 mg/dL)",
}

# International AGP consensus targets (Battelino et al., 2019) -- the same
# standard dashboard_data.GLUCOSE_BANDS cites for the band boundaries
# themselves; the dashboard's own HTML view doesn't display these numeric
# targets today, this PDF is the first celia view that does.
BAND_TARGETS = {
    "very_high": "<5%",
    "high": "<25%",
    "in_range": ">70%",
    "low": "<4%",
    "very_low": "<1%",
}

BAND_COLORS = {
    "very_high": "red!70!black",
    "high": "orange!90!black",
    "in_range": "green!55!black",
    "low": "orange!90!black",
    "very_low": "red!70!black",
}


def build_band_segments(band_percentages: dict[str, float], total_height_cm: float = 4.0) -> list[dict]:
    """Stacked-bar segments, bottom-up (very_low first), for the TikZ
    time-in-range bar.
    """
    bottom_up = tuple(reversed(BAND_ORDER))
    segments = []
    y = 0.0
    for band in bottom_up:
        pct = band_percentages[band]
        height = pct / 100 * total_height_cm
        segments.append({"band": band, "y0": round(y, 4), "height": round(height, 4), "color": BAND_COLORS[band]})
        y += height
    return segments


def build_agp_series(agp_bands: list[dict] | None) -> list[dict] | None:
    """Buckets with fewer than two readings carry all-None percentiles
    (get_agp_percentile_bands); drop them rather than plotting gaps as zero.
    """
    if not agp_bands:
        return None
    points = [b for b in agp_bands if b["median"] is not None]
    return points or None


def build_report_context(
    *,
    profile_name: str,
    start_date: date,
    end_date: date,
    glucose_summary: dict | None,
    agp_bands: list[dict] | None,
    daily_profile_weeks: list[list[dict | None]],
    generated_date: str,
) -> dict:
    return {
        "profile_name": profile_name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "range_days": (end_date - start_date).days + 1,
        "has_data": glucose_summary is not None,
        "glucose_summary": glucose_summary,
        "band_order": BAND_ORDER,
        "band_labels": BAND_LABELS,
        "band_targets": BAND_TARGETS,
        "band_segments": build_band_segments(glucose_summary["band_percentages"]) if glucose_summary else [],
        "agp_series": build_agp_series(agp_bands),
        "daily_profile_weeks": daily_profile_weeks,
        "generated_date": generated_date,
    }
