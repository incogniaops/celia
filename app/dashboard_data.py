import statistics
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GlucoseReading, HealthMetric, MedicationDose

# record_type 0 (historic auto-reading) and 1 (manual scan) are glucose
# values; 5 (insulin/carb), 6 (sensor event) and 99 (PDF summary, see
# glucose-ingestion's PDF_SUMMARY_RECORD_TYPE) are not.
GLUCOSE_RECORD_TYPES = (0, 1)

# Named only in the dashboard requirement's "current biometric profile" --
# steps/sleep (and the other Wyze body-composition fields: BMI, body water,
# lean body mass, bone mass, protein, visceral fat, BMR, metabolic age,
# skeletal muscle rate, fat content, subcutaneous fat) exist in
# health_metrics but showing them is a later addition (see design.md
# Non-Goals), not silently bundled in here.
BIOMETRIC_METRIC_TYPES = ("weight", "body_fat", "heart_rate", "daily_resting_heart_rate", "muscle_mass")

# Fixed international AGP consensus bands (Battelino et al., 2019) -- the
# same boundaries the user's own LibreView report uses, not a
# user-configurable setting (see design.md).
VERY_LOW_THRESHOLD_MGDL = 54
LOW_THRESHOLD_MGDL = 70
HIGH_THRESHOLD_MGDL = 180
VERY_HIGH_THRESHOLD_MGDL = 250
GLUCOSE_BANDS = ("very_low", "low", "in_range", "high", "very_high")

# Matches the FreeStyle Libre's own ~15-minute historic-reading cadence
# (see design.md) -- each bucket aggregates one reading per day rather than
# interpolating.
AGP_BUCKET_MINUTES = 15


def glucose_value(reading: GlucoseReading) -> float:
    return float(
        reading.historic_glucose_mgdl
        if reading.historic_glucose_mgdl is not None
        else reading.scan_glucose_mgdl
    )


def _glucose_band(value: float) -> str:
    if value < VERY_LOW_THRESHOLD_MGDL:
        return "very_low"
    if value < LOW_THRESHOLD_MGDL:
        return "low"
    if value <= HIGH_THRESHOLD_MGDL:
        return "in_range"
    if value <= VERY_HIGH_THRESHOLD_MGDL:
        return "high"
    return "very_high"


def get_glucose_trend(db: Session, start: datetime, end: datetime) -> list[GlucoseReading]:
    stmt = (
        select(GlucoseReading)
        .where(GlucoseReading.record_type.in_(GLUCOSE_RECORD_TYPES))
        .where(GlucoseReading.device_timestamp >= start)
        .where(GlucoseReading.device_timestamp <= end)
        .order_by(GlucoseReading.device_timestamp)
    )
    return list(db.execute(stmt).scalars().all())


def get_insulin_carb_markers(db: Session, start: datetime, end: datetime) -> list[GlucoseReading]:
    stmt = (
        select(GlucoseReading)
        .where(GlucoseReading.device_timestamp >= start)
        .where(GlucoseReading.device_timestamp <= end)
        .where(
            GlucoseReading.rapid_acting_insulin_units.is_not(None)
            | GlucoseReading.long_acting_insulin_units.is_not(None)
            | GlucoseReading.carbohydrates_grams.is_not(None)
        )
        .order_by(GlucoseReading.device_timestamp)
    )
    return list(db.execute(stmt).scalars().all())


def get_medication_doses_in_range(db: Session, start: datetime, end: datetime) -> list[MedicationDose]:
    stmt = (
        select(MedicationDose)
        .where(MedicationDose.actual_date >= start)
        .where(MedicationDose.actual_date <= end)
        .order_by(MedicationDose.actual_date.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_medication_adherence_calendar(
    db: Session, start: datetime, end: datetime
) -> tuple[list[date], list[dict]]:
    """Medication-adherence calendar for the range: one row per medication
    name, one status per day (see design.md).

    Multiple doses for the same medication on the same day are consolidated
    to a single status -- if any of that day's doses was `rejected`, the
    whole day is `rejected`; only an all-`confirmed` day is `confirmed`.
    This deliberately surfaces a missed dose rather than hiding it behind an
    otherwise-adhered day.
    """
    doses = get_medication_doses_in_range(db, start, end)

    statuses_by_name_day: dict[str, dict[date, set[str]]] = {}
    for dose in doses:
        day = dose.actual_date.date()
        statuses_by_name_day.setdefault(dose.name, {}).setdefault(day, set()).add(dose.status)

    days = []
    day = start.date()
    while day <= end.date():
        days.append(day)
        day += timedelta(days=1)

    rows = []
    for name in sorted(statuses_by_name_day):
        day_statuses = statuses_by_name_day[name]
        cells = []
        for day in days:
            statuses = day_statuses.get(day)
            if statuses is None:
                cells.append(None)
            elif "rejected" in statuses:
                cells.append("rejected")
            else:
                cells.append("confirmed")
        rows.append({"name": name, "cells": cells})

    return days, rows


def get_glucose_summary_stats(db: Session, start: datetime, end: datetime) -> dict | None:
    """Time-in-range, GMI and %CV for the range (see design.md) -- the same
    five AGP bands and GMI formula (Bergenstal et al., 2018) the user's own
    LibreView report uses. Returns None when there's no data, rather than a
    misleading 0%-everywhere summary.
    """
    readings = get_glucose_trend(db, start, end)
    if not readings:
        return None

    values = [glucose_value(r) for r in readings]
    counts = dict.fromkeys(GLUCOSE_BANDS, 0)
    for value in values:
        counts[_glucose_band(value)] += 1

    mean = statistics.mean(values)
    cv_percent = (statistics.stdev(values) / mean * 100) if len(values) > 1 else 0.0

    return {
        "band_percentages": {band: count / len(values) * 100 for band, count in counts.items()},
        "average_mgdl": mean,
        "gmi_percent": 3.31 + 0.02392 * mean,
        "cv_percent": cv_percent,
    }


def _agp_bucket_minute(ts: datetime) -> int:
    minute_of_day = ts.hour * 60 + ts.minute
    return (round(minute_of_day / AGP_BUCKET_MINUTES) * AGP_BUCKET_MINUTES) % (24 * 60)


def get_agp_percentile_bands(db: Session, start: datetime, end: datetime) -> list[dict] | None:
    """Ambulatory glucose profile: every day in the range overlaid onto one
    24-hour axis as percentile bands (see design.md). Returns None when the
    range spans fewer than 2 distinct calendar days -- a percentile band
    across a single day isn't meaningful.
    """
    readings = get_glucose_trend(db, start, end)
    distinct_days = {r.device_timestamp.date() for r in readings}
    if len(distinct_days) < 2:
        return None

    values_by_bucket: dict[int, list[float]] = {
        minute: [] for minute in range(0, 24 * 60, AGP_BUCKET_MINUTES)
    }
    for reading in readings:
        values_by_bucket[_agp_bucket_minute(reading.device_timestamp)].append(glucose_value(reading))

    bands = []
    for minute in sorted(values_by_bucket):
        values = values_by_bucket[minute]
        if len(values) < 2:
            bands.append(
                {"minute_of_day": minute, "p5": None, "p25": None, "median": None, "p75": None, "p95": None}
            )
            continue
        cuts = statistics.quantiles(values, n=100, method="inclusive")
        bands.append(
            {
                "minute_of_day": minute,
                "p5": cuts[4],
                "p25": cuts[24],
                "median": statistics.median(values),
                "p75": cuts[74],
                "p95": cuts[94],
            }
        )
    return bands


def get_monthly_glucose_calendar(db: Session, start: datetime, end: datetime) -> list[list[dict | None]]:
    """Week-row/weekday-column calendar for the range (see design.md) --
    distinct from the medication-adherence calendar's row-per-item layout,
    since this answers "how did each day look", not "how did each
    medication do".
    """
    readings = get_glucose_trend(db, start, end)
    values_by_day: dict[date, list[float]] = {}
    for reading in readings:
        values_by_day.setdefault(reading.device_timestamp.date(), []).append(glucose_value(reading))

    start_day = start.date()
    end_day = end.date()
    grid_start = start_day - timedelta(days=start_day.weekday())
    grid_end = end_day + timedelta(days=6 - end_day.weekday())

    weeks: list[list[dict | None]] = []
    week: list[dict | None] = []
    day = grid_start
    while day <= grid_end:
        if start_day <= day <= end_day:
            values = values_by_day.get(day)
            if values:
                avg = statistics.mean(values)
                week.append({"date": day, "average_mgdl": avg, "band": _glucose_band(avg)})
            else:
                week.append({"date": day, "average_mgdl": None, "band": None})
        else:
            week.append(None)
        if len(week) == 7:
            weeks.append(week)
            week = []
        day += timedelta(days=1)
    return weeks


def get_current_biometric_profile(db: Session) -> dict[str, HealthMetric]:
    """Most recent value per biometric metric type, regardless of any
    selected date range -- "current", not "within the chart's window".
    """
    stmt = (
        select(HealthMetric)
        .where(HealthMetric.metric_type.in_(BIOMETRIC_METRIC_TYPES))
        .distinct(HealthMetric.metric_type)
        .order_by(HealthMetric.metric_type, HealthMetric.recorded_at.desc())
    )
    rows = db.execute(stmt).scalars().all()
    return {row.metric_type: row for row in rows}


def has_any_data(db: Session) -> bool:
    """True if anything has ever been ingested from any of the three
    sources -- distinct from a selected date range simply having no rows.
    """
    return bool(
        db.execute(select(GlucoseReading.id).limit(1)).first()
        or db.execute(select(MedicationDose.id).limit(1)).first()
        or db.execute(select(HealthMetric.id).limit(1)).first()
    )
