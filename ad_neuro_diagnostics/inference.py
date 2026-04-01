from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .constants import ARTIFACT_COLUMNS, DEFAULT_TRIBE_CONFIG_VERSION
from .manifests import ProjectPaths, load_artifact_manifest, load_clips
from .utils import ensure_dir, now_iso, run_command, save_json, sha256_file


def compute_cache_key(clip_path: Path, config_version: str = DEFAULT_TRIBE_CONFIG_VERSION) -> str:
    checksum = sha256_file(clip_path)
    return f"{config_version}:{clip_path.resolve()}:{checksum}"


def artifact_files_exist(raw_dir: Path) -> bool:
    return (raw_dir / "preds.npy").exists() and (raw_dir / "events.csv").exists()


def update_artifact_manifest(
    paths: ProjectPaths,
    ad_id: str,
    stage: str,
    status: str,
    cache_key: str,
    error: str = "",
) -> pd.DataFrame:
    manifest = load_artifact_manifest(paths)
    manifest = manifest[
        ~((manifest["ad_id"] == ad_id) & (manifest["stage"] == stage))
    ].copy()
    manifest = pd.concat(
        [
            manifest,
            pd.DataFrame(
                [
                    {
                        "ad_id": ad_id,
                        "stage": stage,
                        "status": status,
                        "cache_key": cache_key,
                        "updated_at": now_iso(),
                        "error": error,
                    }
                ],
                columns=ARTIFACT_COLUMNS,
            ),
        ],
        ignore_index=True,
    )
    manifest.to_csv(paths.artifact_manifest_csv, index=False)
    return manifest


def local_tribe_command(
    python_exe: str,
    clip_path: Path,
    output_dir: Path,
    device: str,
) -> list[str]:
    inline = """
from pathlib import Path
import numpy as np
from tribev2 import TribeModel

clip_path = Path(r'''{clip_path}''')
out = Path(r'''{output_dir}''')
out.mkdir(parents=True, exist_ok=True)
model = TribeModel.from_pretrained("facebook/tribev2", cache_folder=str(out / "cache"), device="{device}")
events = model.get_events_dataframe(video_path=str(clip_path))
preds, _segments = model.predict(events, verbose=True)
np.save(out / "preds.npy", preds)
events.to_csv(out / "events.csv", index=False)
"""
    return [python_exe, "-c", inline.format(clip_path=clip_path, output_dir=output_dir, device=device)]


def run_tribe_batch(
    paths: ProjectPaths,
    tribe_repo: Path | None = None,
    python_exe: str = "python",
    device: str = "cuda",
    config_version: str = DEFAULT_TRIBE_CONFIG_VERSION,
    force: bool = False,
) -> pd.DataFrame:
    clips = load_clips(paths)
    if clips.empty:
        raise ValueError("clips.csv is empty; run ads ingest normalize first")

    results = []
    for clip in clips.itertuples():
        if not bool(clip.normalized_ok):
            continue
        clip_path = Path(clip.clip_path)
        raw_dir = ensure_dir(paths.raw_dir(clip.ad_id))
        cache_key = compute_cache_key(clip_path, config_version=config_version)
        raw_manifest_path = raw_dir / "manifest.json"
        existing_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8")) if raw_manifest_path.exists() else {}
        if (
            not force
            and artifact_files_exist(raw_dir)
            and existing_manifest.get("cache_key") == cache_key
        ):
            update_artifact_manifest(paths, clip.ad_id, "tribe_raw", "cached", cache_key)
            results.append({"ad_id": clip.ad_id, "status": "cached"})
            continue

        if tribe_repo is None:
            update_artifact_manifest(
                paths,
                clip.ad_id,
                "tribe_raw",
                "missing_runner",
                cache_key,
                error="No tribe_repo provided and cached artifacts were missing",
            )
            results.append({"ad_id": clip.ad_id, "status": "missing_runner"})
            continue

        command = local_tribe_command(python_exe, clip_path, raw_dir, device=device)
        result = run_command(command, cwd=tribe_repo)
        if result.returncode != 0:
            (raw_dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
            (raw_dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
            update_artifact_manifest(paths, clip.ad_id, "tribe_raw", "failed", cache_key, error=result.stderr.strip())
            results.append({"ad_id": clip.ad_id, "status": "failed"})
            continue

        save_json(
            raw_manifest_path,
            {
                "stage": "tribe_raw",
                "cache_key": cache_key,
                "clip_path": str(clip_path),
                "config_version": config_version,
                "status": "ready",
            },
        )
        update_artifact_manifest(paths, clip.ad_id, "tribe_raw", "ready", cache_key)
        results.append({"ad_id": clip.ad_id, "status": "ready"})

    return pd.DataFrame(results)
