from __future__ import annotations

from pathlib import Path
from pathlib import PureWindowsPath

import httpx

from .config import get_settings


class TribeRunnerClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.container_data_root = settings.data_root
        self.host_data_root = settings.host_data_root
        self.base_url = settings.tribe_runner_url.rstrip("/")
        self.timeout = settings.tribe_runner_timeout_sec

    def _host_path(self, path: Path) -> str:
        if not self.host_data_root:
            return str(path)
        try:
            relative = path.relative_to(self.container_data_root)
        except ValueError:
            return str(path)

        if ":" in self.host_data_root[:3] or "\\" in self.host_data_root:
            return str(PureWindowsPath(self.host_data_root).joinpath(*relative.parts))
        return str(Path(self.host_data_root).joinpath(*relative.parts))

    def run_job(self, clip_path: Path, output_dir: Path, device: str = "cuda") -> dict:
        payload = {
            "clip_path": self._host_path(clip_path),
            "output_dir": self._host_path(output_dir),
            "device": device,
        }
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/v1/run", json=payload)
            response.raise_for_status()
            return response.json()
