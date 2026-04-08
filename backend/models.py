from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class JobStatus(str, enum.Enum):
    queued = "queued"
    validating = "validating"
    normalizing = "normalizing"
    running_tribe = "running_tribe"
    extracting_features = "extracting_features"
    benchmarking = "benchmarking"
    generating_report = "generating_report"
    completed = "completed"
    failed = "failed"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    batch_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(255))
    campaign: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    original_filename: Mapped[str] = mapped_column(String(255))
    source_path: Mapped[str] = mapped_column(Text)
    workspace_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    ad_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.queued, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String(64), default=JobStatus.queued.value)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    report_json_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    report_markdown_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
