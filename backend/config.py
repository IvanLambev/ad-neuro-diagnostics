from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADND_", case_sensitive=False)

    app_name: str = "Ad Neuro Diagnostics API"
    environment: str = "development"
    api_prefix: str = "/v1"

    data_root: Path = Path("/data")
    database_url: str = "postgresql+psycopg://adnd:adnd@postgres:5432/adnd"
    redis_url: str = "redis://redis:6379/0"
    result_backend_url: str = "redis://redis:6379/1"

    reference_workspace: Path = Path("/data/reference/workspace_small")
    tribe_runner_url: str = "http://host.docker.internal:8765"
    tribe_runner_timeout_sec: float = 3600.0

    max_video_seconds: int = 60
    allowed_video_suffixes: tuple[str, ...] = (".mp4", ".mov", ".mkv", ".avi", ".webm")

    auth_mode: str = "development"
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    clerk_audience: str | None = None

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    default_queue: str = "default"
    gpu_queue: str = "gpu"
    gpu_worker_concurrency: int = 1

    @property
    def uploads_root(self) -> Path:
        return self.data_root / "uploads"

    @property
    def jobs_root(self) -> Path:
        return self.data_root / "jobs"


@lru_cache
def get_settings() -> Settings:
    return Settings()

