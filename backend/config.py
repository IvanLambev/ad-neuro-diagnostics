from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADND_", case_sensitive=False)

    app_name: str = "Ad Neuro Diagnostics API"
    environment: str = "development"
    api_prefix: str = "/v1"

    data_root: Path = Path("/data")
    host_data_root: str | None = None
    database_url: str | None = None
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "ad_neuro_diagnostics"
    postgres_user: str = "adnd_app"
    postgres_password: str | None = None
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
    clerk_jwt_leeway_sec: int = 10

    cors_origins_raw: str = Field(default="http://localhost:5173", alias="cors_origins")
    sse_poll_interval_sec: float = 2.0

    default_queue: str = "default"
    gpu_queue: str = "gpu"
    gpu_worker_concurrency: int = 1

    @model_validator(mode="after")
    def _hydrate_database_url(self) -> "Settings":
        if self.database_url:
            db_url = self.database_url
        else:
            if not self.postgres_password:
                raise ValueError("Set ADND_POSTGRES_PASSWORD or ADND_DATABASE_URL before starting the backend.")
            db_url = (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        self.database_url = db_url
        if self.auth_mode == "clerk" and (not self.clerk_jwks_url or not self.clerk_issuer):
            raise ValueError("Clerk auth mode requires ADND_CLERK_JWKS_URL and ADND_CLERK_ISSUER.")
        return self

    @property
    def cors_origins(self) -> list[str]:
        stripped = self.cors_origins_raw.strip()
        if not stripped:
            return []
        if stripped.startswith("[") and stripped.endswith("]"):
            inner = stripped[1:-1].strip()
            if not inner:
                return []
            return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
        return [item.strip() for item in stripped.split(",") if item.strip()]

    @property
    def uploads_root(self) -> Path:
        return self.data_root / "uploads"

    @property
    def jobs_root(self) -> Path:
        return self.data_root / "jobs"


@lru_cache
def get_settings() -> Settings:
    return Settings()
