from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import SUMMARY_TARGETS
from .manifests import ProjectPaths, load_ads, load_ratings

FOCUS_TARGETS = ("engagement", "confusion", "memorability")

TARGET_DIRECTIONS = {
    "engagement": 1.0,
    "clarity": 1.0,
    "emotional_intensity": 1.0,
    "confusion": -1.0,
    "memorability": 1.0,
}

EXCLUDED_COLUMNS = {
    "ad_id",
    "brand",
    "campaign",
    "variant",
    "source_path",
    "language",
    "split",
    "top_rois",
    "rating_count",
    *SUMMARY_TARGETS,
}


def load_scored_ads(paths: ProjectPaths) -> pd.DataFrame:
    features_path = paths.manifests_dir / "ad_features.csv"
    if not features_path.exists():
        raise FileNotFoundError("Missing ad_features.csv; run extract-features first")

    features = pd.read_csv(features_path)
    ratings = load_ratings(paths)
    if ratings.empty:
        raise ValueError("ratings.csv is empty; import human ratings before benchmarking")

    ads = load_ads(paths)
    numeric = ratings[["ad_id", *SUMMARY_TARGETS]].copy()
    for target in SUMMARY_TARGETS:
        numeric[target] = pd.to_numeric(numeric[target], errors="coerce")

    targets = numeric.groupby("ad_id", as_index=False)[SUMMARY_TARGETS].mean()
    counts = numeric.groupby("ad_id", as_index=False).size().rename(columns={"size": "rating_count"})
    return (
        features.merge(ads, on="ad_id", how="left")
        .merge(targets, on="ad_id", how="inner")
        .merge(counts, on="ad_id", how="left")
    )


def numeric_feature_columns(frame: pd.DataFrame) -> list[str]:
    return [
        column
        for column in frame.columns
        if column not in EXCLUDED_COLUMNS and pd.api.types.is_numeric_dtype(frame[column])
    ]


def similar_ads(frame: pd.DataFrame, ad_id: str, top_k: int = 3) -> pd.DataFrame:
    if ad_id not in frame["ad_id"].values:
        raise KeyError(f"Unknown ad_id: {ad_id}")

    columns = numeric_feature_columns(frame)
    output_columns = [
        column
        for column in [
            "ad_id",
            "brand",
            "campaign",
            "distance",
            *FOCUS_TARGETS,
            "strongest_timestep",
            "top_rois",
        ]
        if column in frame.columns or column == "distance"
    ]
    if not columns:
        return pd.DataFrame(columns=output_columns)

    numeric = frame[columns].apply(pd.to_numeric, errors="coerce")
    centered = numeric.fillna(numeric.median())
    scale = centered.std(ddof=0).replace(0, 1.0).fillna(1.0)
    normalized = (centered - centered.mean()) / scale

    idx = frame.index[frame["ad_id"] == ad_id][0]
    distances = np.linalg.norm(normalized.to_numpy(dtype=np.float64) - normalized.iloc[idx].to_numpy(dtype=np.float64), axis=1)

    neighbors = frame.copy()
    neighbors["distance"] = distances
    neighbors = neighbors.loc[neighbors["ad_id"] != ad_id].sort_values("distance").head(top_k)
    return neighbors[output_columns].reset_index(drop=True)


def benchmark_targets(
    frame: pd.DataFrame,
    ad_id: str,
    targets: tuple[str, ...] = FOCUS_TARGETS,
) -> list[dict[str, float | int | str]]:
    if ad_id not in frame["ad_id"].values:
        raise KeyError(f"Unknown ad_id: {ad_id}")

    row = frame.loc[frame["ad_id"] == ad_id].iloc[0]
    rows: list[dict[str, float | int | str]] = []
    for target in targets:
        if target not in frame.columns:
            continue
        values = pd.to_numeric(frame[target], errors="coerce")
        score = float(row[target])
        mean_value = float(values.mean())
        direction = TARGET_DIRECTIONS.get(target, 1.0)
        better_than = int((((score - values) * direction) > 0).sum())
        rows.append(
            {
                "target": target,
                "score": score,
                "dataset_mean": mean_value,
                "better_than_count": better_than,
                "total_others": int(max(len(values) - 1, 0)),
                "rating_count": int(row.get("rating_count", 0)),
            }
        )
    return rows


def likely_drivers(
    frame: pd.DataFrame,
    ad_id: str,
    target: str,
    top_k: int = 3,
) -> list[dict[str, float | str]]:
    if ad_id not in frame["ad_id"].values:
        raise KeyError(f"Unknown ad_id: {ad_id}")
    if target not in frame.columns:
        return []

    row = frame.loc[frame["ad_id"] == ad_id].iloc[0]
    target_values = pd.to_numeric(frame[target], errors="coerce")
    target_delta = float(row[target]) - float(target_values.mean())
    target_sign = 1.0 if np.isclose(target_delta, 0.0) else float(np.sign(target_delta))

    rows: list[dict[str, float | str]] = []
    for column in numeric_feature_columns(frame):
        series = pd.to_numeric(frame[column], errors="coerce")
        valid = series.notna() & target_values.notna()
        if valid.sum() < 3:
            continue

        series_std = float(series[valid].std(ddof=0))
        target_std = float(target_values[valid].std(ddof=0))
        if np.isclose(series_std, 0.0) or np.isclose(target_std, 0.0):
            continue

        correlation = float(series[valid].corr(target_values[valid]))
        if np.isnan(correlation) or abs(correlation) < 0.15 or pd.isna(row[column]):
            continue

        mean_value = float(series[valid].mean())
        z_score = (float(row[column]) - mean_value) / series_std
        alignment = z_score * correlation * target_sign
        if alignment <= 0:
            continue

        rows.append(
            {
                "feature": column,
                "feature_value": float(row[column]),
                "dataset_mean": mean_value,
                "correlation": correlation,
                "alignment": float(alignment),
            }
        )

    rows.sort(key=lambda item: (item["alignment"], abs(item["correlation"])), reverse=True)
    return rows[:top_k]


def build_benchmark_summary(
    paths: ProjectPaths,
    ad_id: str,
    targets: tuple[str, ...] = FOCUS_TARGETS,
    similar_k: int = 3,
) -> dict[str, object]:
    frame = load_scored_ads(paths)
    row = frame.loc[frame["ad_id"] == ad_id]
    if row.empty:
        raise KeyError(f"Unknown ad_id: {ad_id}")

    neighbors = similar_ads(frame, ad_id, top_k=similar_k)
    benchmarks = benchmark_targets(frame, ad_id, targets=targets)
    drivers = {target: likely_drivers(frame, ad_id, target) for target in targets}

    similar_means = {
        target: float(pd.to_numeric(neighbors[target], errors="coerce").mean())
        for target in targets
        if not neighbors.empty and target in neighbors.columns
    }

    return {
        "ad_id": ad_id,
        "dataset_size": int(len(frame)),
        "similar_ads": neighbors.to_dict(orient="records"),
        "target_benchmarks": benchmarks,
        "similar_means": similar_means,
        "likely_drivers": drivers,
    }
