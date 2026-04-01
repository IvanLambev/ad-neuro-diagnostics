from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline

from .constants import SUMMARY_TARGETS
from .manifests import ProjectPaths, load_ads, load_ratings
from .utils import ensure_dir, save_json


def load_training_frame(paths: ProjectPaths) -> pd.DataFrame:
    features_path = paths.manifests_dir / "ad_features.csv"
    if not features_path.exists():
        raise FileNotFoundError("Missing ad_features.csv; run extract-features first")
    features = pd.read_csv(features_path)
    ads = load_ads(paths)
    ratings = load_ratings(paths)
    if ratings.empty:
        raise ValueError("ratings.csv is empty; import human ratings before training")

    numeric = ratings[["ad_id", *SUMMARY_TARGETS]].copy()
    for target in SUMMARY_TARGETS:
        numeric[target] = pd.to_numeric(numeric[target], errors="coerce")
    targets = numeric.groupby("ad_id", as_index=False)[SUMMARY_TARGETS].mean()
    return features.merge(ads, on="ad_id", how="left").merge(targets, on="ad_id", how="inner")


def grouped_split(
    frame: pd.DataFrame, group_column: str = "campaign"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    groups = frame[group_column].fillna("unknown").astype(str).unique().tolist()
    groups.sort()
    n_test = max(1, int(np.ceil(len(groups) * 0.3)))
    test_groups = set(groups[-n_test:])
    train = frame.loc[
        ~frame[group_column].fillna("unknown").astype(str).isin(test_groups)
    ].copy()
    test = frame.loc[
        frame[group_column].fillna("unknown").astype(str).isin(test_groups)
    ].copy()
    if train.empty or test.empty:
        raise ValueError("Not enough grouped data for train/test split")
    return train, test


def feature_columns(frame: pd.DataFrame) -> list[str]:
    excluded = {
        "ad_id",
        "brand",
        "campaign",
        "variant",
        "source_path",
        "language",
        "split",
        *SUMMARY_TARGETS,
    }
    return [
        column
        for column in frame.columns
        if column not in excluded and pd.api.types.is_numeric_dtype(frame[column])
    ]


def fit_models(paths: ProjectPaths, group_by: str = "campaign") -> Path:
    frame = load_training_frame(paths)
    train, test = grouped_split(frame, group_column=group_by)
    X_cols = feature_columns(frame)
    if not X_cols:
        raise ValueError("No numeric feature columns available for training")

    out_dir = ensure_dir(paths.root / "experiments")
    rows = []
    predictions = []
    estimators = {
        "ridge": Ridge(alpha=1.0),
        "random_forest": RandomForestRegressor(n_estimators=200, random_state=42),
    }
    for target in SUMMARY_TARGETS:
        y_train = train[target]
        y_test = test[target]
        for model_name, estimator in estimators.items():
            pipeline = Pipeline(
                [
                    ("impute", SimpleImputer(strategy="median")),
                    ("model", estimator),
                ]
            )
            pipeline.fit(train[X_cols], y_train)
            pred = pipeline.predict(test[X_cols])
            rows.append(
                {
                    "target": target,
                    "model": model_name,
                    "mae": float(mean_absolute_error(y_test, pred)),
                    "r2": float(r2_score(y_test, pred)),
                    "n_train": int(len(train)),
                    "n_test": int(len(test)),
                    "group_by": group_by,
                }
            )
            for ad_id, actual, estimate in zip(test["ad_id"], y_test, pred):
                predictions.append(
                    {
                        "ad_id": ad_id,
                        "target": target,
                        "model": model_name,
                        "actual": float(actual),
                        "predicted": float(estimate),
                    }
                )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(out_dir / "baseline_metrics.csv", index=False)
    pd.DataFrame(predictions).to_csv(out_dir / "baseline_predictions.csv", index=False)
    save_json(out_dir / "baseline_metrics.json", rows)
    return out_dir
