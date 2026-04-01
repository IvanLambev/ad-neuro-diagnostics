from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .constants import ADS_COLUMNS, ARTIFACT_COLUMNS, CLIPS_COLUMNS, RATINGS_COLUMNS
from .utils import empty_frame, ensure_dir, read_csv_if_exists, save_json


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @property
    def manifests_dir(self) -> Path:
        return self.root / "manifests"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def config_path(self) -> Path:
        return self.root / "project.json"

    @property
    def ads_csv(self) -> Path:
        return self.manifests_dir / "ads.csv"

    @property
    def clips_csv(self) -> Path:
        return self.manifests_dir / "clips.csv"

    @property
    def ratings_csv(self) -> Path:
        return self.manifests_dir / "ratings.csv"

    @property
    def artifact_manifest_csv(self) -> Path:
        return self.manifests_dir / "artifact_manifest.csv"

    def ad_artifact_dir(self, ad_id: str) -> Path:
        return self.artifacts_dir / ad_id

    def raw_dir(self, ad_id: str) -> Path:
        return self.ad_artifact_dir(ad_id) / "raw"

    def features_dir(self, ad_id: str) -> Path:
        return self.ad_artifact_dir(ad_id) / "features"

    def reports_dir(self, ad_id: str) -> Path:
        return self.ad_artifact_dir(ad_id) / "reports"


def init_project(root: Path) -> ProjectPaths:
    paths = ProjectPaths(root=root)
    ensure_dir(paths.root)
    ensure_dir(paths.manifests_dir)
    ensure_dir(paths.artifacts_dir)
    empty_frame(ADS_COLUMNS).to_csv(paths.ads_csv, index=False)
    empty_frame(CLIPS_COLUMNS).to_csv(paths.clips_csv, index=False)
    empty_frame(RATINGS_COLUMNS).to_csv(paths.ratings_csv, index=False)
    empty_frame(ARTIFACT_COLUMNS).to_csv(paths.artifact_manifest_csv, index=False)
    save_json(
        paths.config_path,
        {
            "version": 1,
            "description": "Ad neuro-diagnostics workspace",
            "manifests": {
                "ads": str(paths.ads_csv),
                "clips": str(paths.clips_csv),
                "ratings": str(paths.ratings_csv),
                "artifact_manifest": str(paths.artifact_manifest_csv),
            },
        },
    )
    return paths


def load_paths(root: Path) -> ProjectPaths:
    return ProjectPaths(root=root)


def load_ads(paths: ProjectPaths) -> pd.DataFrame:
    return read_csv_if_exists(paths.ads_csv, ADS_COLUMNS)


def load_clips(paths: ProjectPaths) -> pd.DataFrame:
    return read_csv_if_exists(paths.clips_csv, CLIPS_COLUMNS)


def load_ratings(paths: ProjectPaths) -> pd.DataFrame:
    return read_csv_if_exists(paths.ratings_csv, RATINGS_COLUMNS)


def load_artifact_manifest(paths: ProjectPaths) -> pd.DataFrame:
    return read_csv_if_exists(paths.artifact_manifest_csv, ARTIFACT_COLUMNS)

