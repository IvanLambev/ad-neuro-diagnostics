from __future__ import annotations

from pathlib import Path

import pandas as pd

from .constants import ADS_COLUMNS, SUPPORTED_VIDEO_SUFFIXES
from .manifests import ProjectPaths, load_ads, load_clips
from .utils import ensure_dir, ffprobe_media, parse_media_info, run_command, stable_slug


def validate_ads_frame(frame: pd.DataFrame) -> pd.DataFrame:
    missing = [column for column in ADS_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required ads columns: {missing}")
    if frame["ad_id"].duplicated().any():
        duplicates = frame.loc[frame["ad_id"].duplicated(), "ad_id"].tolist()
        raise ValueError(f"Duplicate ad_id values found: {duplicates}")
    for row in frame.itertuples():
        source = Path(row.source_path)
        if source.suffix.lower() not in SUPPORTED_VIDEO_SUFFIXES:
            raise ValueError(f"Unsupported video format for {row.ad_id}: {source.suffix}")
        if not source.exists():
            raise FileNotFoundError(f"Missing source asset for {row.ad_id}: {source}")
    normalized = frame.copy()
    normalized["ad_id"] = normalized["ad_id"].astype(str).map(stable_slug)
    return normalized[ADS_COLUMNS]


def register_ads(paths: ProjectPaths, input_csv: Path) -> pd.DataFrame:
    incoming = pd.read_csv(input_csv)
    incoming = validate_ads_frame(incoming)
    existing = load_ads(paths)
    if not existing.empty:
        overlap = set(existing["ad_id"]).intersection(incoming["ad_id"])
        if overlap:
            raise ValueError(f"ad_id values already exist in ads.csv: {sorted(overlap)}")
    merged = pd.concat([existing, incoming], ignore_index=True)
    merged.to_csv(paths.ads_csv, index=False)
    return merged


def normalize_ads(
    paths: ProjectPaths,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
) -> pd.DataFrame:
    ads = load_ads(paths)
    if ads.empty:
        raise ValueError("ads.csv is empty; register ads before normalization")

    existing = load_clips(paths)
    clips_root = ensure_dir(paths.root / "clips")
    clip_rows: list[dict[str, object]] = []

    for ad in ads.itertuples():
        source = Path(ad.source_path)
        clip_path = clips_root / f"{ad.ad_id}.mp4"
        command = [
            ffmpeg_bin,
            "-y",
            "-i",
            str(source),
            "-vf",
            f"scale={width}:{height},fps={fps}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            str(clip_path),
        ]
        result = run_command(command)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg normalization failed for {ad.ad_id}: {result.stderr.strip()}")
        info = parse_media_info(ffprobe_media(clip_path, ffprobe_bin=ffprobe_bin))
        clip_rows.append(
            {
                "ad_id": ad.ad_id,
                "clip_path": str(clip_path),
                "fps": info["fps"],
                "width": info["width"],
                "height": info["height"],
                "audio_hz": info["audio_hz"],
                "normalized_ok": True,
            }
        )

    output = pd.DataFrame(clip_rows)
    if not existing.empty:
        output = output.set_index("ad_id")
        output = output.combine_first(existing.set_index("ad_id")).reset_index()
    output.to_csv(paths.clips_csv, index=False)

    updated_ads = ads.copy()
    for idx, row in updated_ads.iterrows():
        clip_info = output.loc[output["ad_id"] == row["ad_id"]]
        if clip_info.empty:
            continue
        media = parse_media_info(ffprobe_media(Path(clip_info.iloc[0]["clip_path"]), ffprobe_bin=ffprobe_bin))
        updated_ads.at[idx, "duration_sec"] = media["duration_sec"]
    updated_ads.to_csv(paths.ads_csv, index=False)
    return output


def export_ratings_template(paths: ProjectPaths, annotators: int = 3, output: Path | None = None) -> Path:
    ads = load_ads(paths)
    if ads.empty:
        raise ValueError("ads.csv is empty; cannot export annotation template")
    rows = []
    for ad_id in ads["ad_id"]:
        for annotator_idx in range(1, annotators + 1):
            rows.append(
                {
                    "ad_id": ad_id,
                    "annotator_id": f"annotator_{annotator_idx}",
                    "engagement": "",
                    "clarity": "",
                    "emotional_intensity": "",
                    "confusion": "",
                    "memorability": "",
                    "notes": "",
                }
            )
    output_path = output or (paths.manifests_dir / "ratings_template.csv")
    pd.DataFrame(rows).to_csv(output_path, index=False)
    return output_path


def import_ratings(paths: ProjectPaths, ratings_csv: Path) -> pd.DataFrame:
    ratings = pd.read_csv(ratings_csv)
    ratings.to_csv(paths.ratings_csv, index=False)
    return ratings
