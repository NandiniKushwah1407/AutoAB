from sqlalchemy import (
    Column, String, Float, DateTime, Enum, Text, JSON, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from database import Base
import uuid
import enum


class ExperimentStatus(str, enum.Enum):
    DRAFT      = "draft"
    RUNNING    = "running"
    ANALYSIS   = "analysis"
    COMPLETED  = "completed"
    STOPPED    = "stopped"


class Experiment(Base):
    __tablename__ = "experiments"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # The two versions being compared
    url_a = Column(String(512), nullable=False)   # Control
    url_b = Column(String(512), nullable=False)   # Treatment

    # Status lifecycle: DRAFT → RUNNING → ANALYSIS → COMPLETED
    status = Column(Enum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False)

    # ── Statistical Config ────────────────────────────────────
    primary_metric         = Column(String(100), default="conversion_rate")
    alpha                  = Column(Float, default=0.05)    # Significance level
    min_detectable_effect  = Column(Float, default=0.02)    # Absolute MDE
    traffic_split          = Column(Float, default=0.5)     # 0.5 = 50/50
    required_sample_size   = Column(Float, nullable=True)   # Auto-computed on create

    # ── Timing ────────────────────────────────────────────────
    duration_days = Column(Float, default=7.0)
    start_time    = Column(DateTime(timezone=True), nullable=True)
    end_time      = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # ── LLM Outputs ───────────────────────────────────────────
    llm_diff   = Column(JSON, nullable=True)   # What changed between A and B
    llm_report = Column(JSON, nullable=True)   # Final AI-generated verdict
