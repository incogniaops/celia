from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import GlucoseReading, HealthMetric, MedicationDose

# record_type 0 (historic auto-reading) and 1 (manual scan) are glucose
# values; 5 (insulin/carb), 6 (sensor event) and 99 (PDF summary, see
# glucose-ingestion's PDF_SUMMARY_RECORD_TYPE) are not.
GLUCOSE_RECORD_TYPES = (0, 1)

# Named only in the dashboard requirement's "current biometric profile" --
# steps/sleep exist in health_metrics but showing them is a later addition
# (see design.md Non-Goals), not silently bundled in here.
BIOMETRIC_METRIC_TYPES = ("weight", "body_fat", "heart_rate", "daily_resting_heart_rate")


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
