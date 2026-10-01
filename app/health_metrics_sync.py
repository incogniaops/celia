from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.auth.google import NotAuthorisedError, TokenExchangeError, ensure_valid_access_token
from app.config import Settings
from app.repository import get_google_health_credential, insert_health_metrics, record_sync_result
from app.timezone import MEXICO_CITY

API_BASE = "https://health.googleapis.com/v4/users/me/dataTypes"

# First-sync bootstrap depth for point-sample types -- generous, since
# duplicates are harmless (ON CONFLICT DO NOTHING) and these were confirmed
# working with a single wide-filter request during manual testing.
_POINT_SAMPLE_BOOTSTRAP = timedelta(days=365)
# First-sync bootstrap depth for paginated types -- deliberately bounded
# (see design.md Decisions: not tested at larger scale, steps in particular
# returned only same-day intervals unpaginated during manual testing).
_PAGINATED_BOOTSTRAP = timedelta(days=30)

POINT_SAMPLE_TYPES = ("weight", "body_fat", "heart_rate", "daily_resting_heart_rate")
PAGINATED_TYPES = ("steps", "sleep")

_URL_IDS = {
    "weight": "weight",
    "body_fat": "body-fat",
    "heart_rate": "heart-rate",
    "daily_resting_heart_rate": "daily-resting-heart-rate",
    "steps": "steps",
    "sleep": "sleep",
}

_FILTER_FIELDS = {
    "weight": "weight.sample_time.physical_time",
    "body_fat": "body_fat.sample_time.physical_time",
    "heart_rate": "heart_rate.sample_time.physical_time",
    "daily_resting_heart_rate": "daily_resting_heart_rate.date",
    "steps": "steps.interval.start_time",
    "sleep": "sleep.interval.end_time",
}


class GoogleHealthApiError(Exception):
    """Raised when the Google Health API itself is unreachable or errors."""


def _format_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_google_timestamp(value: str) -> datetime:
    """Google reports these as true UTC instants; every other source celia
    ingests (LibreView, MyTherapy, Wyze) already stores local wall-clock
    time, so this converts to America/Mexico_City before dropping tzinfo,
    rather than storing the UTC wall-clock time as if it were local (see
    mexico-city-local-time's design.md).
    """
    utc_instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return utc_instant.astimezone(MEXICO_CITY).replace(tzinfo=None)


def _base_metric(metric_type: str, recorded_at: datetime, value: float | None, unit: str, data_point: dict) -> dict:
    data_source = data_point.get("dataSource", {})
    return {
        "metric_type": metric_type,
        "recorded_at": recorded_at,
        "value": value,
        "unit": unit,
        "source_platform": data_source.get("platform"),
        "source_package": data_source.get("application", {}).get("packageName"),
        "raw_json": data_point,
    }


def _extract_weight(data_point: dict) -> dict:
    weight = data_point["weight"]
    grams = float(weight["weightGrams"])
    recorded_at = _parse_google_timestamp(weight["sampleTime"]["physicalTime"])
    return _base_metric("weight", recorded_at, grams / 1000, "kg", data_point)


def _extract_body_fat(data_point: dict) -> dict:
    body_fat = data_point["bodyFat"]
    recorded_at = _parse_google_timestamp(body_fat["sampleTime"]["physicalTime"])
    return _base_metric("body_fat", recorded_at, float(body_fat["percentage"]), "%", data_point)


def _extract_heart_rate(data_point: dict) -> dict:
    heart_rate = data_point["heartRate"]
    recorded_at = _parse_google_timestamp(heart_rate["sampleTime"]["physicalTime"])
    return _base_metric("heart_rate", recorded_at, float(heart_rate["beatsPerMinute"]), "bpm", data_point)


def _extract_daily_resting_heart_rate(data_point: dict) -> dict:
    daily = data_point["dailyRestingHeartRate"]
    date = daily["date"]
    recorded_at = datetime(date["year"], date["month"], date["day"])
    return _base_metric("daily_resting_heart_rate", recorded_at, float(daily["beatsPerMinute"]), "bpm", data_point)


def _extract_steps(data_point: dict) -> dict:
    steps = data_point["steps"]
    recorded_at = _parse_google_timestamp(steps["interval"]["startTime"])
    return _base_metric("steps", recorded_at, float(steps["count"]), "steps", data_point)


def _extract_sleep(data_point: dict) -> dict:
    sleep = data_point["sleep"]
    recorded_at = _parse_google_timestamp(sleep["interval"]["startTime"])
    minutes_asleep = sleep.get("summary", {}).get("minutesAsleep")
    value = float(minutes_asleep) if minutes_asleep is not None else None
    return _base_metric("sleep", recorded_at, value, "min", data_point)


_EXTRACTORS = {
    "weight": _extract_weight,
    "body_fat": _extract_body_fat,
    "heart_rate": _extract_heart_rate,
    "daily_resting_heart_rate": _extract_daily_resting_heart_rate,
    "steps": _extract_steps,
    "sleep": _extract_sleep,
}


def _build_filter(metric_type: str, since: datetime, until: datetime) -> str:
    field = _FILTER_FIELDS[metric_type]
    if metric_type == "daily_resting_heart_rate":
        # Upper bound is exclusive and date-only (not timestamp-only), so on
        # a same-day re-sync `since.date() == until.date()` would otherwise
        # produce an empty/invalid range -- Google rejects it outright
        # ("Query end time must be strictly larger than start time").
        # Always include the full day `until` falls on.
        upper_bound = until.date() + timedelta(days=1)
        return f'{field} >= "{since.date()}" AND {field} < "{upper_bound}"'
    return f'{field} >= "{_format_timestamp(since)}" AND {field} < "{_format_timestamp(until)}"'


def _fetch_data_points(access_token: str, url_id: str, filter_expr: str, page_token: str | None = None) -> dict:
    params = {"filter": filter_expr}
    if page_token:
        params["pageToken"] = page_token

    response = httpx.get(
        f"{API_BASE}/{url_id}/dataPoints",
        params=params,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code != 200:
        raise GoogleHealthApiError(
            f"Google Health API returned {response.status_code} for {url_id}: {response.text}"
        )
    return response.json()


def _sync_point_sample_type(access_token: str, metric_type: str, since: datetime, until: datetime) -> list[dict]:
    filter_expr = _build_filter(metric_type, since, until)
    response = _fetch_data_points(access_token, _URL_IDS[metric_type], filter_expr)
    extractor = _EXTRACTORS[metric_type]
    return [extractor(dp) for dp in response.get("dataPoints", [])]


def _sync_paginated_type(access_token: str, metric_type: str, since: datetime, until: datetime) -> list[dict]:
    filter_expr = _build_filter(metric_type, since, until)
    extractor = _EXTRACTORS[metric_type]
    url_id = _URL_IDS[metric_type]

    metrics: list[dict] = []
    page_token: str | None = None
    while True:
        response = _fetch_data_points(access_token, url_id, filter_expr, page_token)
        metrics.extend(extractor(dp) for dp in response.get("dataPoints", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return metrics


def sync_health_metrics(db: Session, settings: Settings) -> dict:
    """Run one sync across all six confirmed data types.

    Refreshes the access token first if needed, fetches each type, stores
    new data points (duplicates silently skipped), and records the sync's
    outcome on the credential row either way.
    """
    now = datetime.utcnow()

    try:
        access_token = ensure_valid_access_token(db, settings)
    except (NotAuthorisedError, TokenExchangeError) as exc:
        record_sync_result(db, status="failed", error=str(exc), synced_at=now)
        raise

    credential = get_google_health_credential(db)
    point_sample_since = credential.last_synced_at or (now - _POINT_SAMPLE_BOOTSTRAP)
    paginated_since = credential.last_synced_at or (now - _PAGINATED_BOOTSTRAP)

    metrics: list[dict] = []
    try:
        for metric_type in POINT_SAMPLE_TYPES:
            metrics.extend(_sync_point_sample_type(access_token, metric_type, point_sample_since, now))
        for metric_type in PAGINATED_TYPES:
            metrics.extend(_sync_paginated_type(access_token, metric_type, paginated_since, now))
    except GoogleHealthApiError as exc:
        record_sync_result(db, status="failed", error=str(exc), synced_at=now)
        raise

    inserted = insert_health_metrics(db, metrics)
    record_sync_result(db, status="success", error=None, synced_at=now)
    return {"fetched": len(metrics), "inserted": inserted}
