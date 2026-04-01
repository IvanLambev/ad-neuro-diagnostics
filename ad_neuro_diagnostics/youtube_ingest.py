from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .constants import ADS_COLUMNS
from .manifests import ProjectPaths, init_project, load_paths
from .utils import ensure_dir, stable_slug


@dataclass(frozen=True)
class RequestedVideo:
    brand: str
    url: str


@dataclass(frozen=True)
class DownloadedVideo:
    brand: str
    url: str
    video_id: str
    title: str
    channel: str
    duration_sec: float | None
    source_path: Path
    language: str


def parse_video_requests(input_path: Path) -> list[RequestedVideo]:
    items: list[RequestedVideo] = []
    for line_number, raw_line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Invalid line {line_number} in {input_path}: expected 'Brand: URL'")
        brand, url = line.split(":", maxsplit=1)
        brand = brand.strip()
        url = url.strip()
        if not brand or not url:
            raise ValueError(f"Invalid line {line_number} in {input_path}: missing brand or URL")
        items.append(RequestedVideo(brand=brand, url=url))
    if not items:
        raise ValueError(f"No video links found in {input_path}")
    return items


def assign_splits(brands: list[str], validation_ratio: float = 0.3) -> dict[str, str]:
    canonical_by_brand = {
        brand: stable_slug(brand) or brand.strip().lower()
        for brand in brands
        if brand.strip()
    }
    unique_brands = sorted(set(canonical_by_brand.values()))
    if not unique_brands:
        raise ValueError("Cannot assign splits without at least one brand")
    if len(unique_brands) == 1:
        return {brand: "train" for brand in canonical_by_brand}

    n_validation = max(1, round(len(unique_brands) * validation_ratio))
    n_validation = min(n_validation, len(unique_brands) - 1)
    validation_brands = set(unique_brands[-n_validation:])
    return {
        brand: ("validation" if canonical_by_brand[brand] in validation_brands else "train")
        for brand in canonical_by_brand
    }


def build_ads_frame(downloads: list[DownloadedVideo], validation_ratio: float = 0.3) -> pd.DataFrame:
    split_by_brand = assign_splits([item.brand for item in downloads], validation_ratio=validation_ratio)
    rows: list[dict[str, Any]] = []
    for item in downloads:
        campaign = item.brand
        variant = item.video_id
        ad_id = stable_slug(f"{item.brand}-{variant}")
        rows.append(
            {
                "ad_id": ad_id,
                "source_path": str(item.source_path.resolve()),
                "brand": item.brand,
                "campaign": campaign,
                "variant": variant,
                "duration_sec": item.duration_sec,
                "language": item.language,
                "split": split_by_brand[item.brand],
            }
        )
    frame = pd.DataFrame(rows)
    if frame["ad_id"].duplicated().any():
        duplicates = frame.loc[frame["ad_id"].duplicated(), "ad_id"].tolist()
        raise ValueError(f"Duplicate ad_id values after download: {duplicates}")
    return frame[ADS_COLUMNS].sort_values(["split", "brand", "ad_id"]).reset_index(drop=True)


def build_source_catalog_frame(downloads: list[DownloadedVideo], validation_ratio: float = 0.3) -> pd.DataFrame:
    split_by_brand = assign_splits([item.brand for item in downloads], validation_ratio=validation_ratio)
    rows = [
        {
            "brand": item.brand,
            "url": item.url,
            "video_id": item.video_id,
            "title": item.title,
            "channel": item.channel,
            "duration_sec": item.duration_sec,
            "language": item.language,
            "source_path": str(item.source_path.resolve()),
            "split": split_by_brand[item.brand],
        }
        for item in downloads
    ]
    return pd.DataFrame(rows).sort_values(["split", "brand", "video_id"]).reset_index(drop=True)


def ensure_project(project_root: Path) -> ProjectPaths:
    if (project_root / "project.json").exists():
        return load_paths(project_root)
    return init_project(project_root)


def write_download_outputs(
    project_root: Path,
    downloads: list[DownloadedVideo],
    validation_ratio: float = 0.3,
) -> tuple[Path, Path]:
    paths = ensure_project(project_root)
    ensure_dir(paths.manifests_dir)
    ads_frame = build_ads_frame(downloads, validation_ratio=validation_ratio)
    catalog_frame = build_source_catalog_frame(downloads, validation_ratio=validation_ratio)
    ads_frame.to_csv(paths.ads_csv, index=False)
    catalog_path = paths.manifests_dir / "youtube_sources.csv"
    catalog_frame.to_csv(catalog_path, index=False)
    return paths.ads_csv, catalog_path
