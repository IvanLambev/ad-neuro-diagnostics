from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .models import JobStatus


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    brand: str
    campaign: str
    notes: str | None
    ad_id: str | None
    status: JobStatus
    progress: int
    current_step: str
    error_message: str | None
    created_at: datetime | None
    updated_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class ReportPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    job_id: str
    status: str
    ad: dict[str, Any]
    summary: dict[str, Any]
    strengths: list[str]
    risks: list[str]
    similar_ads: list[dict[str, Any]]
    moments: list[dict[str, Any]]
    why: dict[str, list[str]]
    assets: dict[str, str]
    technical: dict[str, Any]

