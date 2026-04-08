from __future__ import annotations

from .celery_app import celery_app


def run() -> None:
    celery_app.worker_main(
        [
            "worker",
            "--loglevel=INFO",
            "--queues=gpu",
            "--concurrency=1",
        ]
    )
