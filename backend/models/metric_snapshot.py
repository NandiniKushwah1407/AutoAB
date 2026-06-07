from sqlalchemy import Column, Float, DateTime, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base


class MetricSnapshot(Base):
    """
    Aggregated metrics computed every 5 minutes by the Celery worker.
    These power the live dashboard charts — no real-time aggregation needed.
    """
    __tablename__ = "metric_snapshots"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    group         = Column(String(20), nullable=False)   # "control" | "treatment"
    snapshot_at   = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # ── User Counts ───────────────────────────────────────────
    users_count    = Column(Integer, default=0)
    sessions_count = Column(Integer, default=0)

    # ── Conversion ────────────────────────────────────────────
    conversions     = Column(Integer, default=0)
    conversion_rate = Column(Float,   default=0.0)

    # ── Revenue ───────────────────────────────────────────────
    total_revenue = Column(Float, default=0.0)
    avg_revenue   = Column(Float, default=0.0)

    # ── Engagement ────────────────────────────────────────────
    ctr                  = Column(Float, default=0.0)   # Click-through rate
    avg_session_duration = Column(Float, default=0.0)   # Seconds
    bounce_rate          = Column(Float, default=0.0)   # % who never clicked
    avg_scroll_depth     = Column(Float, default=0.0)   # 0–100%

    __table_args__ = (
        Index("ix_snapshots_exp_group_time", "experiment_id", "group", "snapshot_at"),
    )
