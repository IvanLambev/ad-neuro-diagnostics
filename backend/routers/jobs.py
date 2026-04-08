from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
import json

from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ad_neuro_diagnostics.utils import ensure_dir

from ..auth import AuthenticatedUser, get_current_user
from ..config import get_settings
from ..db import get_db
from ..models import AnalysisJob, JobStatus
from ..pipeline import run_analysis_job
from ..schemas import JobCreateResponse, JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])
settings = get_settings()


def _job_or_404(db: Session, user_id: str, job_id: str) -> AnalysisJob:
    job = db.get(AnalysisJob, job_id)
    if job is None or job.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    file: UploadFile = File(...),
    title: str = Form(...),
    brand: str = Form(...),
    campaign: str = Form(...),
    notes: str | None = Form(default=None),
    batch_id: str | None = Form(default=None),
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.allowed_video_suffixes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported file type")

    uploads_dir = ensure_dir(settings.uploads_root / user.user_id)
    job = AnalysisJob(
        user_id=user.user_id,
        batch_id=batch_id,
        title=title,
        brand=brand,
        campaign=campaign,
        notes=notes,
        original_filename=file.filename or "upload.bin",
        source_path="",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    target_path = uploads_dir / f"{job.id}{suffix}"
    with target_path.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)

    job.source_path = str(target_path)
    db.add(job)
    db.commit()
    db.refresh(job)

    run_analysis_job.apply_async(args=[job.id], queue=settings.gpu_queue)
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("", response_model=list[JobRead])
def list_jobs(
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AnalysisJob]:
    stmt = select(AnalysisJob).where(AnalysisJob.user_id == user.user_id).order_by(AnalysisJob.created_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisJob:
    return _job_or_404(db, user.user_id, job_id)


@router.get("/{job_id}/report")
def get_report(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _job_or_404(db, user.user_id, job_id)
    if job.status != JobStatus.completed or not job.report_json_path:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report is not ready")
    report_path = Path(job.report_json_path)
    if not report_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file is missing")
    return json.loads(report_path.read_text(encoding="utf-8"))


@router.get("/{job_id}/assets/{asset_name}")
def get_asset(
    job_id: str,
    asset_name: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _job_or_404(db, user.user_id, job_id)
    if not job.workspace_path or not job.ad_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job workspace is not ready")

    asset_map = {
        "activation_curve": Path(job.workspace_path) / "artifacts" / job.ad_id / "features" / "activation_strength.csv",
        "brain_strongest": Path(job.workspace_path) / "artifacts" / job.ad_id / "features" / "brain_strongest.png",
        "brain_animation": Path(job.workspace_path) / "artifacts" / job.ad_id / "features" / "brain_animation.gif",
        "customer_report": Path(job.report_markdown_path) if job.report_markdown_path else None,
    }
    asset_path = asset_map.get(asset_name)
    if asset_path is None or not asset_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return FileResponse(asset_path)


@router.post("/{job_id}/retry", response_model=JobCreateResponse)
def retry_job(
    job_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    job = _job_or_404(db, user.user_id, job_id)
    if job.status != JobStatus.failed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only failed jobs can be retried")
    job.status = JobStatus.queued
    job.progress = 0
    job.current_step = JobStatus.queued.value
    job.error_message = None
    db.add(job)
    db.commit()
    db.refresh(job)
    run_analysis_job.apply_async(args=[job.id], queue=settings.gpu_queue)
    return JobCreateResponse(job_id=job.id, status=job.status)
