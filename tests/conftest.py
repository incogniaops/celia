import os

import pytest
from sqlalchemy import text

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://celia:celia@localhost:5432/celia")

from app.database import get_session_factory  # noqa: E402 -- import after setting DATABASE_URL default


@pytest.fixture
def db_session():
    session_factory = get_session_factory()
    session = session_factory()
    session.execute(text("TRUNCATE TABLE glucose_readings, medication_doses RESTART IDENTITY"))
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
