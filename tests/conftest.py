import os

import pytest
from sqlalchemy import text

# A dedicated database, never the one compose/dev/the container uses for
# real data. This fixture TRUNCATEs on every test -- pointing it at the
# real "celia" database cost a real sync's worth of data (all four tables
# wiped) when a local pytest run picked up DATABASE_URL=...localhost/celia
# while the dev container held real, just-uploaded data. Guarded below so
# that mistake fails loudly instead of silently deleting real data again.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://celia:celia@localhost:5432/celia_test")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")
os.environ.setdefault("PROFILE_HEIGHT_M", "1.80")
os.environ.setdefault("PROFILE_BIRTH_DATE", "2000-01-01")
os.environ.setdefault("PROFILE_NAME", "Test User")

if "_test" not in os.environ["DATABASE_URL"].rsplit("/", 1)[-1]:
    raise RuntimeError(
        "Refusing to run tests: DATABASE_URL does not point at a *_test database. "
        f"Got: {os.environ['DATABASE_URL']!r}. This fixture TRUNCATEs its tables on "
        "every test -- pointing it at a real database will destroy real data."
    )

from app.database import get_session_factory  # noqa: E402 -- import after setting env defaults


@pytest.fixture
def db_session():
    session_factory = get_session_factory()
    session = session_factory()
    session.execute(
        text(
            "TRUNCATE TABLE glucose_readings, medication_doses, "
            "health_metrics, google_health_credentials RESTART IDENTITY"
        )
    )
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
