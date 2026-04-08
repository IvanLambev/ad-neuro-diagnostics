from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from celery.utils.log import get_task_logger

from ad_neuro_diagnostics.features import extract_features_for_ad
from ad_neuro_diagnostics.inference import update_artifact_manifest
from ad_neuro_diagnostics.ingest import normalize_ads, register_ads
from ad_neuro_diagnostics.manifests import init_project, load_clips, load_paths
from ad_neuro_diagnostics.utils import ffprobe_media, parse_media_info, stable_slug

from .celery_app import celery_app
from .config import get_settings
from .db import SessionLocal
from .models import AnalysisJob, JobStatus
from .report_builder import build_customer_report, save_customer_report
from .runner_client import TribeRunnerClient

logger = get_task_logger(__name__)
settings = get_settings()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _set_job_state(
    db,
    job: AnalysisJob,
    status: JobStatus,
    progress: int,
    current_step: str,
    error_message: str | None = None,
) -> None:
    job.status = status
    job.progress = progress
    job.current_step = current_step
    job.error_message = error_message
    if status != JobStatus.queued and job.started_at is None:
        job.started_at = _now()
    if status in {JobStatus.completed, JobStatus.failed}:
        job.completed_at = _now()
    db.add(job)
    db.commit()
    db.refresh(job)


def _validate_video(path: Path) -> None:
    info = ffprobe_media(path)
    media = parse_media_info(info)
    duration = float(media.get("duration_sec") or 0.0)
    if duration > settings.max_video_seconds:
        raise ValueError("Ads longer than 60 seconds are not supported yet.")
    if path.suffix.lower() not in settings.allowed_video_suffixes:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def _build_workspace(job: AnalysisJob) -> tuple[Path, str]:
    job_dir = settings.jobs_root / job.id
    if job_dir.exists():
        shutil.rmtree(job_dir)
    paths = init_project(job_dir)

    source_path = Path(job.source_path)
    ad_id = stable_slug(f"{job.brand}-{source_path.stem}-{job.id[:8]}")
    ads_csv = job_dir / "incoming_ad.csv"
    pd.DataFrame(
        [
            {
                "ad_id": ad_id,
                "source_path": str(source_path),
                "brand": job.brand,
                "campaign": job.campaign,
                "variant": source_path.stem,
                "duration_sec": 0,
                "language": "unknown",
                "split": "score",
            }
        ]
    ).to_csv(ads_csv, index=False)
    register_ads(paths, ads_csv)
    return job_dir, ad_id


@celery_app.task(name="backend.pipeline.run_analysis_job")
def run_analysis_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            raise RuntimeError(f"Unknown job id: {job_id}")

        _set_job_state(db, job, JobStatus.validating, 5, JobStatus.validating.value)
        _validate_video(Path(job.source_path))

        workspace_path, ad_id = _build_workspace(job)
        job.workspace_path = str(workspace_path)
        job.ad_id = ad_id
        db.add(job)
        db.commit()
        db.refresh(job)

        _set_job_state(db, job, JobStatus.normalizing, 20, JobStatus.normalizing.value)
        workspace = load_paths(workspace_path)
        normalize_ads(workspace)
        clip_row = load_clips(workspace).iloc[0]
        clip_path = Path(str(clip_row["clip_path"]))

        _set_job_state(db, job, JobStatus.running_tribe, 45, JobStatus.running_tribe.value)
        raw_dir = workspace.raw_dir(ad_id)
        raw_dir.mkdir(parents=True, exist_ok=True)
        TribeRunnerClient().run_job(clip_path, raw_dir)
        update_artifact_manifest(
            workspace,
            ad_id,
            "tribe_raw",
            "ready",
            cache_key=f"remote_runner:{clip_path}",
        )

        _set_job_state(db, job, JobStatus.extracting_features, 65, JobStatus.extracting_features.value)
        extract_features_for_ad(workspace, ad_id)

        _set_job_state(db, job, JobStatus.benchmarking, 80, JobStatus.benchmarking.value)
        reference_paths = load_paths(settings.reference_workspace)
        report, markdown = build_customer_report(
            job_id=job.id,
            ad_id=ad_id,
            title=job.title,
            brand=job.brand,
            features_dir=workspace.features_dir(ad_id),
            reference_paths=reference_paths,
        )

        _set_job_state(db, job, JobStatus.generating_report, 92, JobStatus.generating_report.value)
        json_path, md_path = save_customer_report(report, markdown, workspace.reports_dir(ad_id))
        job.report_json_path = str(json_path)
        job.report_markdown_path = str(md_path)
        job.metadata_json = {
            "workspace_path": str(workspace_path),
            "ad_id": ad_id,
        }
        db.add(job)
        db.commit()
        db.refresh(job)

        _set_job_state(db, job, JobStatus.completed, 100, JobStatus.completed.value)
    except Exception as exc:
        logger.exception("analysis job failed", exc_info=exc)
        if "job" in locals() and isinstance(job, AnalysisJob):
            _set_job_state(
                db,
                job,
                JobStatus.failed,
                job.progress or 0,
                job.current_step or JobStatus.failed.value,
                error_message=str(exc),
            )
        raise
    finally:
        db.close()
