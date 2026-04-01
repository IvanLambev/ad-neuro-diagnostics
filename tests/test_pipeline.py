from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ad_neuro_diagnostics.experiments import fit_models
from ad_neuro_diagnostics.features import extract_all_features
from ad_neuro_diagnostics.ingest import normalize_ads, register_ads
from ad_neuro_diagnostics.inference import compute_cache_key, run_tribe_batch
from ad_neuro_diagnostics.manifests import init_project, load_paths
from ad_neuro_diagnostics.reports import generate_compare_report, generate_single_report


def write_ads_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return path


def build_project(tmp_path: Path):
    root = tmp_path / "workspace"
    paths = init_project(root)
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    for name in ("ad-a.mp4", "ad-b.mp4", "ad-c.mp4", "ad-d.mp4"):
        (src_dir / name).write_bytes(b"fake-video")
    ads_csv = write_ads_csv(
        tmp_path / "ads.csv",
        [
            {
                "ad_id": "ad-a",
                "source_path": str(src_dir / "ad-a.mp4"),
                "brand": "brand-a",
                "campaign": "camp-1",
                "variant": "v1",
                "duration_sec": 0,
                "language": "en",
                "split": "train",
            },
            {
                "ad_id": "ad-b",
                "source_path": str(src_dir / "ad-b.mp4"),
                "brand": "brand-a",
                "campaign": "camp-1",
                "variant": "v2",
                "duration_sec": 0,
                "language": "en",
                "split": "train",
            },
            {
                "ad_id": "ad-c",
                "source_path": str(src_dir / "ad-c.mp4"),
                "brand": "brand-b",
                "campaign": "camp-2",
                "variant": "v1",
                "duration_sec": 0,
                "language": "en",
                "split": "test",
            },
            {
                "ad_id": "ad-d",
                "source_path": str(src_dir / "ad-d.mp4"),
                "brand": "brand-b",
                "campaign": "camp-2",
                "variant": "v2",
                "duration_sec": 0,
                "language": "en",
                "split": "test",
            },
        ],
    )
    register_ads(paths, ads_csv)
    return paths


def test_register_ads_rejects_duplicates(tmp_path: Path):
    paths = init_project(tmp_path / "workspace")
    src = tmp_path / "ad.mp4"
    src.write_bytes(b"x")
    ads_csv = write_ads_csv(
        tmp_path / "dup.csv",
        [
            {
                "ad_id": "dup",
                "source_path": str(src),
                "brand": "brand",
                "campaign": "camp",
                "variant": "v1",
                "duration_sec": 1,
                "language": "en",
                "split": "train",
            },
            {
                "ad_id": "dup",
                "source_path": str(src),
                "brand": "brand",
                "campaign": "camp",
                "variant": "v2",
                "duration_sec": 1,
                "language": "en",
                "split": "train",
            },
        ],
    )
    with pytest.raises(ValueError):
        register_ads(paths, ads_csv)


def test_normalize_ads_uses_ffmpeg_and_ffprobe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    paths = build_project(tmp_path)

    def fake_run(command, cwd=None):
        clip_path = Path(command[-1])
        clip_path.write_bytes(b"normalized")
        class Result:
            returncode = 0
            stderr = ""
        return Result()

    def fake_ffprobe(path, ffprobe_bin="ffprobe"):
        return {
            "streams": [
                {"codec_type": "video", "width": 1280, "height": 720, "avg_frame_rate": "30/1"},
                {"codec_type": "audio", "sample_rate": "48000"},
            ],
            "format": {"duration": "15.0"},
        }

    monkeypatch.setattr("ad_neuro_diagnostics.ingest.run_command", fake_run)
    monkeypatch.setattr("ad_neuro_diagnostics.ingest.ffprobe_media", fake_ffprobe)

    clips = normalize_ads(paths)
    assert len(clips) == 4
    assert all(clips["normalized_ok"])


def test_run_tribe_batch_uses_cache(tmp_path: Path):
    paths = build_project(tmp_path)
    clips = pd.DataFrame(
        [
            {
                "ad_id": "ad-a",
                "clip_path": str(tmp_path / "workspace" / "clips" / "ad-a.mp4"),
                "fps": 30,
                "width": 1280,
                "height": 720,
                "audio_hz": 48000,
                "normalized_ok": True,
            }
        ]
    )
    Path(clips.iloc[0]["clip_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(clips.iloc[0]["clip_path"]).write_bytes(b"normalized")
    clips.to_csv(paths.clips_csv, index=False)

    raw_dir = paths.raw_dir("ad-a")
    raw_dir.mkdir(parents=True, exist_ok=True)
    np.save(raw_dir / "preds.npy", np.ones((4, 8), dtype=np.float32))
    pd.DataFrame([{"type": "Word", "start": 0, "duration": 1}]).to_csv(raw_dir / "events.csv", index=False)
    cache_key = compute_cache_key(Path(clips.iloc[0]["clip_path"]))
    (raw_dir / "manifest.json").write_text(
        json.dumps({"cache_key": cache_key}), encoding="utf-8"
    )

    result = run_tribe_batch(paths)
    assert result.iloc[0]["status"] == "cached"


def test_feature_extraction_and_reports(tmp_path: Path):
    paths = build_project(tmp_path)
    clips = []
    for ad_id in ("ad-a", "ad-b"):
        clip_path = tmp_path / "workspace" / "clips" / f"{ad_id}.mp4"
        clip_path.parent.mkdir(parents=True, exist_ok=True)
        clip_path.write_bytes(b"normalized")
        clips.append(
            {
                "ad_id": ad_id,
                "clip_path": str(clip_path),
                "fps": 30,
                "width": 1280,
                "height": 720,
                "audio_hz": 48000,
                "normalized_ok": True,
            }
        )
        raw_dir = paths.raw_dir(ad_id)
        raw_dir.mkdir(parents=True, exist_ok=True)
        np.save(raw_dir / "preds.npy", np.random.default_rng(0).normal(size=(5, 8)).astype(np.float32))
        pd.DataFrame(
            [
                {"type": "Word", "start": 0.0, "duration": 0.5},
                {"type": "Word", "start": 1.0, "duration": 0.5},
            ]
        ).to_csv(raw_dir / "events.csv", index=False)
    pd.DataFrame(clips).to_csv(paths.clips_csv, index=False)

    ratings = pd.DataFrame(
        [
            {"ad_id": "ad-a", "annotator_id": "ann-1", "engagement": 4, "clarity": 5, "emotional_intensity": 3, "confusion": 1, "memorability": 4, "notes": "good"},
            {"ad_id": "ad-a", "annotator_id": "ann-2", "engagement": 3, "clarity": 4, "emotional_intensity": 3, "confusion": 2, "memorability": 4, "notes": "solid"},
            {"ad_id": "ad-b", "annotator_id": "ann-1", "engagement": 2, "clarity": 3, "emotional_intensity": 2, "confusion": 3, "memorability": 2, "notes": "weak"},
            {"ad_id": "ad-b", "annotator_id": "ann-2", "engagement": 2, "clarity": 2, "emotional_intensity": 2, "confusion": 4, "memorability": 2, "notes": "unclear"},
        ]
    )
    ratings.to_csv(paths.ratings_csv, index=False)

    features = extract_all_features(paths)
    assert {"ad_id", "strongest_timestep", "mean_abs_max"}.issubset(features.columns)

    single = generate_single_report(paths, "ad-a")
    compare = generate_compare_report(paths, "ad-a", "ad-b")
    assert single.exists()
    assert compare.exists()


def test_baseline_training_writes_outputs(tmp_path: Path):
    paths = build_project(tmp_path)
    features = pd.DataFrame(
        [
            {"ad_id": "ad-a", "mean_abs_mean": 0.5, "mean_abs_max": 0.7, "duration_sec": 15, "speech_density": 1.0},
            {"ad_id": "ad-b", "mean_abs_mean": 0.6, "mean_abs_max": 0.8, "duration_sec": 15, "speech_density": 0.8},
            {"ad_id": "ad-c", "mean_abs_mean": 0.2, "mean_abs_max": 0.3, "duration_sec": 30, "speech_density": 0.5},
            {"ad_id": "ad-d", "mean_abs_mean": 0.1, "mean_abs_max": 0.2, "duration_sec": 30, "speech_density": 0.4},
        ]
    )
    features.to_csv(paths.manifests_dir / "ad_features.csv", index=False)
    ratings = pd.DataFrame(
        [
            {"ad_id": "ad-a", "annotator_id": "ann-1", "engagement": 4, "clarity": 5, "emotional_intensity": 3, "confusion": 1, "memorability": 4, "notes": ""},
            {"ad_id": "ad-b", "annotator_id": "ann-1", "engagement": 5, "clarity": 4, "emotional_intensity": 4, "confusion": 1, "memorability": 5, "notes": ""},
            {"ad_id": "ad-c", "annotator_id": "ann-1", "engagement": 2, "clarity": 2, "emotional_intensity": 2, "confusion": 3, "memorability": 2, "notes": ""},
            {"ad_id": "ad-d", "annotator_id": "ann-1", "engagement": 1, "clarity": 2, "emotional_intensity": 1, "confusion": 4, "memorability": 1, "notes": ""},
        ]
    )
    ratings.to_csv(paths.ratings_csv, index=False)

    out_dir = fit_models(paths)
    assert (out_dir / "baseline_metrics.csv").exists()
    assert (out_dir / "baseline_predictions.csv").exists()
