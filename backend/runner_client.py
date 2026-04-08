from __future__ import annotations

from pathlib import Path

import httpx

from .config import get_settings


class TribeRunnerClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.tribe_runner_url.rstrip("/")
        self.timeout = settings.tribe_runner_timeout_sec

    def run_job(self, clip_path: Path, output_dir: Path, device: str = "cuda") -> dict:
        payload = {
            "clip_path": str(clip_path),
            "output_dir": str(output_dir),
            "device": device,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/v1/run", json=payload)
            response.raise_for_status()
            return response.json()
