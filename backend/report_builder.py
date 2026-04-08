from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ad_neuro_diagnostics.insights import FOCUS_TARGETS, TARGET_DIRECTIONS, load_scored_ads, numeric_feature_columns
from ad_neuro_diagnostics.manifests import ProjectPaths

TARGET_NAMES = {
    "engagement": "attention",
    "confusion": "clarity",
    "memorability": "memorability",
}

FEATURE_PLAIN_ENGLISH = {
    "mean_abs_max": ("stronger standout moments", "weaker standout moments"),
    "mean_abs_peak_count": ("more repeated spikes of attention", "fewer repeated spikes of attention"),
    "max_abs_peak_count": ("more sharp peaks", "fewer sharp peaks"),
    "max_abs_std": ("bigger swings in intensity", "flatter intensity over time"),
    "motion_mean": ("more visual movement", "less visual movement"),
    "motion_std": ("more variation in pacing and movement", "more even pacing and movement"),
    "brightness_mean": ("brighter visuals", "darker visuals"),
    "brightness_std": ("more contrast between bright and dark moments", "more even lighting throughout"),
    "audio_loudness_mean": ("louder audio presence", "quieter audio presence"),
    "word_count": ("more spoken words", "fewer spoken words"),
    "speech_density": ("faster speaking pace", "slower speaking pace"),
    "shot_count": ("more scene changes", "fewer scene changes"),
    "cut_rate": ("faster editing pace", "slower editing pace"),
    "colorfulness_mean": ("more colorful visuals", "more muted visuals"),
    "n_timesteps": ("a longer unfolding arc", "a shorter unfolding arc"),
    "duration_sec": ("a longer runtime", "a shorter runtime"),
    "duration_sec_x": ("a longer runtime", "a shorter runtime"),
    "duration_sec_y": ("a longer runtime", "a shorter runtime"),
}


def _reference_similarity(reference_frame: pd.DataFrame, new_row: pd.Series, top_k: int = 3) -> pd.DataFrame:
    columns = numeric_feature_columns(reference_frame)
    ref_numeric = reference_frame[columns].apply(pd.to_numeric, errors="coerce")
    medians = ref_numeric.median()
    scale = ref_numeric.std(ddof=0).replace(0, 1.0).fillna(1.0)
    center = ref_numeric.mean().fillna(0.0)

    filled_ref = ref_numeric.fillna(medians)
    new_numeric = pd.Series({column: pd.to_numeric(new_row.get(column), errors="coerce") for column in columns})
    filled_new = new_numeric.fillna(medians)

    ref_norm = (filled_ref - center) / scale
    new_norm = (filled_new - center) / scale
    distances = np.linalg.norm(ref_norm.to_numpy(dtype=np.float64) - new_norm.to_numpy(dtype=np.float64), axis=1)

    neighbors = reference_frame.copy()
    neighbors["distance"] = distances
    return neighbors.sort_values("distance").head(top_k).reset_index(drop=True)


def _weighted_target_predictions(neighbors: pd.DataFrame) -> dict[str, dict[str, float]]:
    distances = np.maximum(neighbors["distance"].to_numpy(dtype=np.float64), 1e-6)
    weights = 1.0 / distances
    payload: dict[str, dict[str, float]] = {}
    for target in FOCUS_TARGETS:
        values = pd.to_numeric(neighbors[target], errors="coerce").to_numpy(dtype=np.float64)
        payload[TARGET_NAMES[target]] = {
            "score": float(np.average(values, weights=weights)),
            "peer_mean": float(values.mean()),
        }
    return payload


def _band_for_target(target: str, score: float, dataset_mean: float) -> str:
    delta = (score - dataset_mean) * TARGET_DIRECTIONS.get(target, 1.0)
    if delta >= 0.5:
        return "strong"
    if delta >= 0.15:
        return "slightly_strong"
    if delta <= -0.5:
        return "weak"
    if delta <= -0.15:
        return "slightly_weak"
    return "average"


def _plain_driver_text(feature: str, value: float, mean_value: float) -> str:
    high_text, low_text = FEATURE_PLAIN_ENGLISH.get(feature, (f"higher {feature}", f"lower {feature}"))
    return high_text if value >= mean_value else low_text


def _likely_drivers(reference_frame: pd.DataFrame, new_row: pd.Series, target: str, top_k: int = 3) -> list[dict[str, object]]:
    target_values = pd.to_numeric(reference_frame[target], errors="coerce")
    drivers: list[dict[str, object]] = []
    for column in numeric_feature_columns(reference_frame):
        series = pd.to_numeric(reference_frame[column], errors="coerce")
        valid = series.notna() & target_values.notna()
        if valid.sum() < 3:
            continue
        series_std = float(series[valid].std(ddof=0))
        target_std = float(target_values[valid].std(ddof=0))
        if np.isclose(series_std, 0.0) or np.isclose(target_std, 0.0):
            continue
        new_value = pd.to_numeric(new_row.get(column), errors="coerce")
        if pd.isna(new_value):
            continue
        correlation = float(series[valid].corr(target_values[valid]))
        if np.isnan(correlation) or abs(correlation) < 0.15:
            continue
        mean_value = float(series[valid].mean())
        z_score = (float(new_value) - mean_value) / series_std
        alignment = z_score * correlation * TARGET_DIRECTIONS.get(target, 1.0)
        if alignment <= 0:
            continue
        drivers.append(
            {
                "feature": column,
                "feature_value": float(new_value),
                "dataset_mean": mean_value,
                "alignment": float(alignment),
                "plain_text": _plain_driver_text(column, float(new_value), mean_value),
            }
        )
    drivers.sort(key=lambda item: float(item["alignment"]), reverse=True)
    return drivers[:top_k]


def _moment_payload(features_dir: Path, duration_sec: float, top_k: int = 2) -> list[dict[str, object]]:
    activation_path = features_dir / "activation_strength.csv"
    if not activation_path.exists():
        return []
    activation = pd.read_csv(activation_path)
    if activation.empty:
        return []
    n = len(activation)
    seconds_per_step = duration_sec / max(n, 1)
    strongest = activation.nlargest(top_k, "mean_abs")
    weakest = activation.nsmallest(top_k, "mean_abs")

    moments: list[dict[str, object]] = []
    for row, label in ((strongest, "Strong moment"), (weakest, "Potential drop-off moment")):
        for item in row.itertuples():
            start_sec = float(item.timestep) * seconds_per_step
            moments.append(
                {
                    "start_sec": round(start_sec, 2),
                    "end_sec": round(start_sec + seconds_per_step, 2),
                    "label": label,
                    "impact": ["attention"],
                }
            )
    moments.sort(key=lambda item: (item["start_sec"], item["label"]))
    return moments


def build_customer_report(
    job_id: str,
    ad_id: str,
    title: str,
    brand: str,
    features_dir: Path,
    reference_paths: ProjectPaths,
) -> tuple[dict[str, object], str]:
    summary = pd.read_csv(features_dir / "summary.csv").iloc[0]
    reference_frame = load_scored_ads(reference_paths)
    neighbors = _reference_similarity(reference_frame, summary, top_k=3)
    target_scores = _weighted_target_predictions(neighbors)
    dataset_means = {
        target: float(pd.to_numeric(reference_frame[target], errors="coerce").mean())
        for target in FOCUS_TARGETS
    }

    strengths: list[str] = []
    risks: list[str] = []
    why: dict[str, list[str]] = {}
    summary_payload: dict[str, dict[str, float | str]] = {}

    for target in FOCUS_TARGETS:
        outward_name = TARGET_NAMES[target]
        score = float(target_scores[outward_name]["score"])
        dataset_mean = dataset_means[target]
        peer_mean = float(pd.to_numeric(neighbors[target], errors="coerce").mean())
        band = _band_for_target(target, score, dataset_mean)
        summary_payload[outward_name] = {
            "band": band,
            "score": round(score, 3),
            "dataset_mean": round(dataset_mean, 3),
            "peer_mean": round(peer_mean, 3),
        }

        drivers = _likely_drivers(reference_frame, summary, target)
        why[outward_name] = [str(item["plain_text"]) for item in drivers]
        if target == "confusion":
            if band in {"strong", "slightly_strong"}:
                strengths.append("The ad looks clearer than average compared with the current reference set.")
            elif band in {"weak", "slightly_weak"}:
                risks.append("The message may be harder to follow than similar ads.")
        elif target == "engagement":
            if band in {"strong", "slightly_strong"}:
                strengths.append("The ad looks better than average at holding attention.")
            elif band in {"weak", "slightly_weak"}:
                risks.append("The ad may struggle to hold attention compared with similar ads.")
        elif target == "memorability":
            if band in {"strong", "slightly_strong"}:
                strengths.append("The ad looks more memorable than average in the current reference set.")
            elif band in {"weak", "slightly_weak"}:
                risks.append("The ad may be less memorable than similar ads.")

    report = {
        "job_id": job_id,
        "status": "completed",
        "ad": {
            "ad_id": ad_id,
            "title": title,
            "brand": brand,
            "duration_sec": float(summary.get("duration_sec", 0.0)),
        },
        "summary": summary_payload,
        "strengths": strengths,
        "risks": risks,
        "similar_ads": [
            {
                "ad_id": row.ad_id,
                "brand": row.brand,
                "distance": round(float(row.distance), 3),
                "why_similar": "Close pacing and response pattern",
            }
            for row in neighbors.itertuples()
        ],
        "moments": _moment_payload(features_dir, float(summary.get("duration_sec", 0.0))),
        "why": why,
        "assets": {
            "activation_curve": "activation_strength.csv",
            "brain_strongest": "brain_strongest.png",
            "brain_animation": "brain_animation.gif",
        },
        "technical": {
            "top_rois": str(summary.get("top_rois", "")).split(",") if summary.get("top_rois") else [],
            "strongest_timestep": int(summary.get("strongest_timestep", 0)),
            "summary": summary.to_dict(),
        },
    }

    lines = [f"# Customer Report: {title}", "", "## Quick Read"]
    for label, payload in report["summary"].items():
        lines.append(f"- {label.title()}: {payload['band'].replace('_', ' ')}")
    if strengths:
        lines.extend(["", "## Strengths", *[f"- {item}" for item in strengths]])
    if risks:
        lines.extend(["", "## Risks", *[f"- {item}" for item in risks]])
    lines.extend(["", "## Similar Ads", *[f"- {item['ad_id']} ({item['brand']})" for item in report["similar_ads"]]])
    lines.extend(["", "## Why We Think This"])
    for label, items in report["why"].items():
        lines.append(f"- {label.title()}: {', '.join(items) if items else 'Not enough signal yet.'}")
    return report, "\n".join(lines) + "\n"


def save_customer_report(report: dict[str, object], markdown: str, reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "customer_report.json"
    md_path = reports_dir / "customer_report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path
