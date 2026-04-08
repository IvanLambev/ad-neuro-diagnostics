from __future__ import annotations

from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "adnd",
    broker=settings.redis_url,
    backend=settings.result_backend_url,
    include=["backend.pipeline"],
)
celery_app.conf.task_default_queue = settings.default_queue
celery_app.conf.task_routes = {
    "backend.pipeline.run_analysis_job": {"queue": settings.gpu_queue},
}
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
