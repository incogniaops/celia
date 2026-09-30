from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import HealthMetric
from app.repository import save_google_health_tokens


@pytest.fixture
def client(db_session):
    return TestClient(app)


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict:
        return self._payload


_WEIGHT_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.hualai"}},
    "weight": {"sampleTime": {"physicalTime": "2026-09-27T14:25:21.699Z"}, "weightGrams": 113000},
}
_BODY_FAT_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.hualai"}},
    "bodyFat": {"sampleTime": {"physicalTime": "2026-09-27T14:25:21.699Z"}, "percentage": 34.4},
}
_HEART_RATE_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.xiaomi.wearable"}},
    "heartRate": {"sampleTime": {"physicalTime": "2026-09-27T18:50:39Z"}, "beatsPerMinute": "129"},
}
_DAILY_RESTING_HEART_RATE_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.google.android.apps.fitness"}},
    "dailyRestingHeartRate": {"date": {"year": 2026, "month": 7, "day": 18}, "beatsPerMinute": "86"},
}
_STEPS_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.xiaomi.wearable"}},
    "steps": {"interval": {"startTime": "2026-09-30T19:30:00Z", "endTime": "2026-09-30T19:59:59Z"}, "count": "18"},
}
_SLEEP_DATA_POINT = {
    "dataSource": {"platform": "HEALTH_CONNECT", "application": {"packageName": "com.xiaomi.wearable"}},
    "sleep": {
        "interval": {"startTime": "2026-09-30T07:27:00Z", "endTime": "2026-09-30T11:58:00Z"},
        "summary": {"minutesInSleepPeriod": "271", "minutesAsleep": "271"},
    },
}

_ONE_POINT_PER_URL_ID = {
    "weight": _WEIGHT_DATA_POINT,
    "body-fat": _BODY_FAT_DATA_POINT,
    "heart-rate": _HEART_RATE_DATA_POINT,
    "daily-resting-heart-rate": _DAILY_RESTING_HEART_RATE_DATA_POINT,
    "steps": _STEPS_DATA_POINT,
    "sleep": _SLEEP_DATA_POINT,
}


def _fake_get_one_point_per_type(url, params=None, headers=None):
    url_id = url.rsplit("/dataTypes/", 1)[1].split("/dataPoints")[0]
    return _FakeResponse(200, {"dataPoints": [_ONE_POINT_PER_URL_ID[url_id]]})


def test_sync_requires_authorisation_first(client):
    response = client.post("/sync/google-health")

    assert response.status_code == 401


def test_sync_stores_metrics_and_returns_counts(client, db_session, monkeypatch):
    save_google_health_tokens(
        db_session,
        access_token="AT",
        refresh_token="RT",
        access_token_expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    monkeypatch.setattr("app.health_metrics_sync.httpx.get", _fake_get_one_point_per_type)

    response = client.post("/sync/google-health")

    assert response.status_code == 200
    assert response.json() == {"fetched": 6, "inserted": 6}
    stored = db_session.execute(select(HealthMetric)).scalars().all()
    assert len(stored) == 6
