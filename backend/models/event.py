from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import uuid


class Event(Base):
    """
    Every user interaction captured by the JS SDK lands here.
    Optimised for time-series queries via a composite index.
    """
    __tablename__ = "events"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id    = Column(String(128), nullable=False, index=True)
    group         = Column(String(20), nullable=False)   # "control" | "treatment"

    # ── Event Type ────────────────────────────────────────────
    # page_view | click | scroll | conversion | session_end | rage_click | form_submit
    event_type = Column(String(50), nullable=False)
    element_id = Column(String(255), nullable=True)   # Button/link ID that was clicked
    page_url   = Column(String(512), nullable=True)

    # ── Metric Values ─────────────────────────────────────────
    value        = Column(Float, nullable=True)   # Revenue on conversion event
    duration     = Column(Float, nullable=True)   # Session duration in seconds
    scroll_depth = Column(Float, nullable=True)   # 0–100%

    # ── Context ───────────────────────────────────────────────
    device   = Column(String(20),  nullable=True)   # mobile | desktop | tablet
    country  = Column(String(10),  nullable=True)
    referrer = Column(String(512), nullable=True)
    extra_data = Column(JSON,      nullable=True)   # Any extra custom data (renamed from metadata)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Composite index for fast per-experiment, per-group, time-range queries
    __table_args__ = (
        Index("ix_events_exp_group_time", "experiment_id", "group", "timestamp"),
    )
