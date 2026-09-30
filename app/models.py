from datetime import datetime

from sqlalchemy import JSON, DateTime, Numeric, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GlucoseReading(Base):
    """A single row from a LibreView export.

    Uniqueness on (device_timestamp, record_type) is the deduplication key
    decided in this change's spec delta: LibreView CSV exports are cumulative,
    so re-uploading a superset export must not create duplicate rows, and a
    disagreeing value for an already-stored (timestamp, record_type) pair is
    discarded rather than overwriting the first value stored.
    """

    __tablename__ = "glucose_readings"
    __table_args__ = (
        UniqueConstraint("device_timestamp", "record_type", name="uq_glucose_reading_timestamp_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    record_type: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    historic_glucose_mgdl: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    scan_glucose_mgdl: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    rapid_acting_insulin_units: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    long_acting_insulin_units: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    carbohydrates_grams: Mapped[float | None] = mapped_column(Numeric, nullable=True)

    source: Mapped[str] = mapped_column(String, nullable=False, default="libreview_csv")
    raw_row: Mapped[dict] = mapped_column(JSON, nullable=False)
