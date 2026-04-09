from __future__ import annotations

from pathlib import Path

import pytest

from backend.config import Settings
from backend.runner_client import TribeRunnerClient


def test_settings_parse_cors_origins_from_csv() -> None:
    settings = Settings(
        postgres_password="test-password",
        cors_origins="https://app.example.com, https://preview.example.com",
    )
    assert settings.cors_origins == [
        "https://app.example.com",
        "https://preview.example.com",
    ]


def test_settings_require_clerk_metadata_in_clerk_mode() -> None:
    with pytest.raises(ValueError, match="Clerk auth mode requires"):
        Settings(
            postgres_password="test-password",
            auth_mode="clerk",
        )


def test_runner_client_translates_container_paths_to_host_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADND_POSTGRES_PASSWORD", "test-password")
    monkeypatch.setenv("ADND_HOST_DATA_ROOT", "/host-data")
    monkeypatch.setenv("ADND_DATA_ROOT", "/data")
    monkeypatch.setenv("ADND_TRIBE_RUNNER_URL", "http://runner.internal:8765")

    from backend.config import get_settings

    get_settings.cache_clear()
    client = TribeRunnerClient()

    translated = client._host_path(Path("/data/jobs/example/clip.mp4"))
    untouched = client._host_path(Path("/tmp/outside-data-root.mp4"))

    assert translated == "/host-data/jobs/example/clip.mp4"
    assert untouched == "/tmp/outside-data-root.mp4"

    get_settings.cache_clear()


def test_celery_registers_analysis_task(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADND_POSTGRES_PASSWORD", "test-password")
    from backend.config import get_settings
    from backend.celery_app import celery_app

    get_settings.cache_clear()
    assert "backend.pipeline.run_analysis_job" in celery_app.tasks
    get_settings.cache_clear()
