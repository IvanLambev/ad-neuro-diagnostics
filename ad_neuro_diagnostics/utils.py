from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def stable_slug(value: str) -> str:
    keep = [c.lower() if c.isalnum() else "-" for c in value.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def robust_scale(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float32)
    median = np.median(values)
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    scale = q3 - q1
    if np.isclose(scale, 0):
        scale = np.std(values)
    if np.isclose(scale, 0):
        scale = 1.0
    return (values - median) / scale


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def run_command(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd is not None else None,
        check=False,
        capture_output=True,
        text=True,
    )


def ffprobe_media(path: Path, ffprobe_bin: str = "ffprobe") -> dict[str, Any]:
    command = [
        ffprobe_bin,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr.strip()}")
    return json.loads(result.stdout)


def parse_media_info(info: dict[str, Any]) -> dict[str, float | int | None]:
    streams = info.get("streams", [])
    format_info = info.get("format", {})
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), {})
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), {})

    frame_rate = video_stream.get("avg_frame_rate", "0/1")
    try:
        num, den = frame_rate.split("/")
        fps = float(num) / float(den) if float(den) != 0 else 0.0
    except Exception:
        fps = 0.0

    duration = format_info.get("duration") or video_stream.get("duration") or audio_stream.get("duration")
    return {
        "duration_sec": float(duration) if duration else None,
        "fps": fps or None,
        "width": int(video_stream["width"]) if video_stream.get("width") else None,
        "height": int(video_stream["height"]) if video_stream.get("height") else None,
        "audio_hz": int(audio_stream["sample_rate"]) if audio_stream.get("sample_rate") else None,
    }


def read_csv_if_exists(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return empty_frame(columns)
    return pd.read_csv(path)

