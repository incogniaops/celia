from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from app.auth.google import NotAuthorisedError
from app.health_metrics_sync import (
    GoogleHealthApiError,
    _build_filter,
    _extract_body_fat,
    _extract_daily_resting_heart_rate,
    _extract_heart_rate,
    _extract_sleep,
    _extract_steps,
    _extract_weight,
    sync_health_metrics,
)
from app.config import Settings
from app.models import HealthMetric
from app.repository import save_google_health_tokens

_SETTINGS = Settings(database_url="unused", google_client_id="cid", google_client_secret="secret")


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict:
        return self._payload


# Real response shapes confirmed live during the hackathon (see
# docs/PS-CELIA-001-...md, US-03), trimmed to one data point each.
_WEIGHT_DATA_POINT = {
    "dataSource": {"recordingMethod": "PASSIVELY_MEASURED", "platform": "HEALTH_CONNECT", "application": {"packageName": "com.hualai"}},
    "weight": {"sampleTime": {"physicalTime": "2026-09-27T14:25:21.699Z"}, "weightGrams": 113000},
}
_BODY_FAT_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.hualai"}},
    "bodyFat": {"sampleTime": {"physicalTime": "2026-09-27T14:25:21.699Z"}, "percentage": 34.4},
}
_HEART_RATE_DATA_POINT = {
    "dataSource": {"device": {"manufacturer": "xiaomi"}, "platform": "HEALTH_CONNECT", "application": {"packageName": "com.xiaomi.wearable"}},
    "heartRate": {"sampleTime": {"physicalTime": "2026-09-27T18:50:39Z"}, "beatsPerMinute": "129"},
}
_DAILY_RESTING_HEART_RATE_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.google.android.apps.fitness"}},
    "dailyRestingHeartRate": {"date": {"year": 2026, "month": 7, "day": 18}, "beatsPerMinute": "86"},
}
_STEPS_DATA_POINT = {
    "dataSource": {"device": {"manufacturer": "xiaomi"}, "platform": "HEALTH_CONNECT", "application": {"packageName": "com.xiaomi.wearable"}},
    "steps": {"interval": {"startTime": "2026-09-30T19:30:00Z", "endTime": "2026-09-30T19:59:59Z"}, "count": "18"},
}
_SLEEP_DATA_POINT = {
    "dataSource": {"device": {"manufacturer": "xiaomi"}, "platform": "HEALTH_CONNECT", "application": {"packageName": "com.xiaomi.wearable"}},
    "sleep": {
        "interval": {"startTime": "2026-09-30T07:27:00Z", "endTime": "2026-09-30T11:58:00Z"},
        "summary": {"minutesInSleepPeriod": "271", "minutesAsleep": "271"},
    },
}


def test_extract_weight_converts_grams_to_kg():
    metric = _extract_weight(_WEIGHT_DATA_POINT)
    assert metric["metric_type"] == "weight"
    assert metric["value"] == 113.0
    assert metric["unit"] == "kg"
    assert metric["source_package"] == "com.hualai"
    assert metric["recorded_at"] == datetime(2026, 9, 27, 14, 25, 21, 699000)


def test_extract_body_fat():
    metric = _extract_body_fat(_BODY_FAT_DATA_POINT)
    assert metric["value"] == 34.4
    assert metric["unit"] == "%"


def test_extract_heart_rate():
    metric = _extract_heart_rate(_HEART_RATE_DATA_POINT)
    assert metric["value"] == 129.0
    assert metric["unit"] == "bpm"
    assert metric["source_package"] == "com.xiaomi.wearable"


def test_build_filter_for_daily_type_is_never_empty_on_same_day_resync():
    # Regression test: discovered live when a second real sync ran seconds
    # after the first, so `since` and `until` fell on the same calendar
    # day. Google rejected `>= "2026-09-30" AND < "2026-09-30"` outright
    # ("Query end time must be strictly larger than start time").
    same_day = datetime(2026, 9, 30, 20, 0, 0)
    a_bit_later = datetime(2026, 9, 30, 20, 0, 5)

    filter_expr = _build_filter("daily_resting_heart_rate", same_day, a_bit_later)

    assert filter_expr == (
        'daily_resting_heart_rate.date >= "2026-09-30" AND '
        'daily_resting_heart_rate.date < "2026-10-01"'
    )


def test_extract_daily_resting_heart_rate_uses_date_not_sample_time():
    metric = _extract_daily_resting_heart_rate(_DAILY_RESTING_HEART_RATE_DATA_POINT)
    assert metric["value"] == 86.0
    assert metric["recorded_at"] == datetime(2026, 7, 18)


def test_extract_steps():
    metric = _extract_steps(_STEPS_DATA_POINT)
    assert metric["value"] == 18.0
    assert metric["unit"] == "steps"
    assert metric["recorded_at"] == datetime(2026, 9, 30, 19, 30, 0)


def test_extract_sleep_uses_summary_minutes_asleep():
    metric = _extract_sleep(_SLEEP_DATA_POINT)
    assert metric["value"] == 271.0
    assert metric["unit"] == "min"
    assert metric["raw_json"]["sleep"]["summary"]["minutesInSleepPeriod"] == "271"


def _fake_get_one_point_per_type(url, params=None, headers=None):
    """Dispatch by URL to a single, correctly-shaped data point per type."""
    url_id = url.rsplit("/dataTypes/", 1)[1].split("/dataPoints")[0]
    one_point_per_url_id = {
        "weight": _WEIGHT_DATA_POINT,
        "body-fat": _BODY_FAT_DATA_POINT,
        "heart-rate": _HEART_RATE_DATA_POINT,
        "daily-resting-heart-rate": _DAILY_RESTING_HEART_RATE_DATA_POINT,
        "steps": _STEPS_DATA_POINT,
        "sleep": _SLEEP_DATA_POINT,
    }
    return _FakeResponse(200, {"dataPoints": [one_point_per_url_id[url_id]]})


def _authorise(db_session):
    save_google_health_tokens(
        db_session,
        access_token="AT",
        refresh_token="RT",
        access_token_expires_at=datetime.utcnow() + timedelta(hours=1),
    )


def test_sync_fetches_all_six_types_and_stores_them(db_session, monkeypatch):
    _authorise(db_session)

    responses_by_url_id = {
        "weight": {"dataPoints": [_WEIGHT_DATA_POINT]},
        "body-fat": {"dataPoints": [_BODY_FAT_DATA_POINT]},
        "heart-rate": {"dataPoints": [_HEART_RATE_DATA_POINT]},
        "daily-resting-heart-rate": {"dataPoints": [_DAILY_RESTING_HEART_RATE_DATA_POINT]},
        "steps": {"dataPoints": [_STEPS_DATA_POINT]},
        "sleep": {"dataPoints": [_SLEEP_DATA_POINT]},
    }

    def fake_get(url, params=None, headers=None):
        url_id = url.rsplit("/dataTypes/", 1)[1].split("/dataPoints")[0]
        assert headers["Authorization"] == "Bearer AT"
        return _FakeResponse(200, responses_by_url_id[url_id])

    monkeypatch.setattr("app.health_metrics_sync.httpx.get", fake_get)

    result = sync_health_metrics(db_session, _SETTINGS)

    assert result == {"fetched": 6, "inserted": 6}
    stored_types = {m.metric_type for m in db_session.execute(select(HealthMetric)).scalars().all()}
    assert stored_types == {"weight", "body_fat", "heart_rate", "daily_resting_heart_rate", "steps", "sleep"}


def test_sync_paginates_steps_and_sleep(db_session, monkeypatch):
    _authorise(db_session)

    second_steps_point = {
        **_STEPS_DATA_POINT,
        "steps": {
            "interval": {"startTime": "2026-09-30T20:00:00Z", "endTime": "2026-09-30T20:14:59Z"},
            "count": "5",
        },
    }
    call_count = {"steps": 0}

    def fake_get(url, params=None, headers=None):
        url_id = url.rsplit("/dataTypes/", 1)[1].split("/dataPoints")[0]
        if url_id == "steps":
            call_count["steps"] += 1
            if call_count["steps"] == 1:
                return _FakeResponse(200, {"dataPoints": [_STEPS_DATA_POINT], "nextPageToken": "page2"})
            return _FakeResponse(200, {"dataPoints": [second_steps_point]})
        if url_id == "sleep":
            return _FakeResponse(200, {"dataPoints": [_SLEEP_DATA_POINT]})
        return _FakeResponse(200, {"dataPoints": []})

    monkeypatch.setattr("app.health_metrics_sync.httpx.get", fake_get)

    sync_health_metrics(db_session, _SETTINGS)

    assert call_count["steps"] == 2
    steps_rows = (
        db_session.execute(select(HealthMetric).where(HealthMetric.metric_type == "steps")).scalars().all()
    )
    assert len(steps_rows) == 2


def test_sync_does_not_duplicate_on_overlapping_window(db_session, monkeypatch):
    _authorise(db_session)
    monkeypatch.setattr("app.health_metrics_sync.httpx.get", _fake_get_one_point_per_type)

    first = sync_health_metrics(db_session, _SETTINGS)
    second = sync_health_metrics(db_session, _SETTINGS)

    assert first["inserted"] == 6  # one data point per type
    assert second["inserted"] == 0
    count = db_session.execute(select(HealthMetric)).scalars().all()
    assert len(count) == 6


def test_sync_without_authorisation_raises_and_records_failure(db_session):
    with pytest.raises(NotAuthorisedError):
        sync_health_metrics(db_session, _SETTINGS)


def test_sync_records_failure_on_api_error_and_leaves_existing_data_unchanged(db_session, monkeypatch):
    _authorise(db_session)
    # First sync succeeds and stores one data point per type.
    monkeypatch.setattr("app.health_metrics_sync.httpx.get", _fake_get_one_point_per_type)
    sync_health_metrics(db_session, _SETTINGS)
    before = db_session.execute(select(HealthMetric)).scalars().all()

    # Second sync: Google Health API errors on every call.
    monkeypatch.setattr(
        "app.health_metrics_sync.httpx.get",
        lambda url, params=None, headers=None: _FakeResponse(500, {"error": "internal"}),
    )
    with pytest.raises(GoogleHealthApiError):
        sync_health_metrics(db_session, _SETTINGS)

    after = db_session.execute(select(HealthMetric)).scalars().all()
    assert len(after) == len(before)
