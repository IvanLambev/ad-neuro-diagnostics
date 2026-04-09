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

SIMILARITY_FEATURE_TEXT = {
    "duration_sec": "runtime",
    "cut_rate": "editing pace",
    "motion_mean": "visual movement",
    "speech_density": "spoken pace",
    "colorfulness_mean": "visual color",
    "audio_loudness_mean": "audio intensity",
    "brightness_mean": "overall brightness",
}

TRACK_DEFINITIONS = {
    "hook_strength": {
        "label": "Hook strength",
        "weights": {
            "mean_abs_early_mean": 0.95,
            "mean_abs_peak_count": 0.45,
            "colorfulness_mean": 0.35,
            "motion_mean": 0.2,
        },
    },
    "clarity_stability": {
        "label": "Clarity stability",
        "weights": {
            "mean_abs_mean": 0.6,
            "max_abs_std": -0.7,
            "cut_rate": -0.55,
            "speech_density": -0.45,
            "brightness_mean": 0.2,
        },
    },
    "value_lift": {
        "label": "Value lift",
        "weights": {
            "mean_abs_late_mean": 0.85,
            "mean_abs_mid_mean": -0.35,
            "mean_abs_max": 0.35,
            "colorfulness_mean": 0.2,
        },
    },
    "trust_close": {
        "label": "Trust close",
        "weights": {
            "mean_abs_late_mean": 0.7,
            "max_abs_std": -0.55,
            "cut_rate": -0.45,
            "speech_density": -0.35,
            "brightness_mean": 0.15,
        },
    },
}

TRACK_DESCRIPTIONS = {
    "hook_strength": (
        "How strongly the first seconds pull people in.",
        "Fast early pull, opening energy, and whether the ad earns attention before the story settles.",
    ),
    "clarity_stability": (
        "How easy the message feels to stay with over time.",
        "Stability through pacing, intensity changes, and whether the ad stays readable instead of feeling noisy.",
    ),
    "value_lift": (
        "Whether the ad strengthens around the product, offer, or closing payoff.",
        "Late-stage lift matters because strong ads often build value instead of peaking too early and fading.",
    ),
    "trust_close": (
        "How steady and reassuring the closing section feels.",
        "This track is a proxy for whether the final product, brand, or CTA lands with enough stability to reduce friction.",
    ),
}

TRACK_COMPONENT_TEXT = {
    "mean_abs_early_mean": ("stronger early response", "softer early response"),
    "mean_abs_peak_count": ("more repeated attention beats", "fewer repeated attention beats"),
    "colorfulness_mean": ("richer color energy", "more restrained color energy"),
    "motion_mean": ("more motion in the opening", "less motion in the opening"),
    "mean_abs_mean": ("steadier overall response", "weaker overall response"),
    "max_abs_std": ("more abrupt intensity swings", "more controlled intensity swings"),
    "cut_rate": ("faster cutting", "slower cutting"),
    "speech_density": ("denser speech", "lighter speech load"),
    "brightness_mean": ("brighter visual framing", "darker visual framing"),
    "mean_abs_late_mean": ("stronger late-stage lift", "weaker late-stage lift"),
    "mean_abs_mid_mean": ("a heavier middle section", "a lighter middle section"),
    "mean_abs_max": ("a stronger standout peak", "a softer standout peak"),
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


def _target_percentile(reference_frame: pd.DataFrame, target: str, score: float) -> float:
    values = pd.to_numeric(reference_frame[target], errors="coerce").dropna().to_numpy(dtype=np.float64)
    if len(values) == 0:
        return 50.0
    direction = TARGET_DIRECTIONS.get(target, 1.0)
    better_than = (((score - values) * direction) >= 0).sum()
    return float(100.0 * better_than / len(values))


def _confidence_payload(neighbors: pd.DataFrame) -> dict[str, float | str]:
    if neighbors.empty:
        return {"score": 0.0, "label": "exploratory"}
    mean_distance = float(pd.to_numeric(neighbors["distance"], errors="coerce").mean())
    rating_count = float(pd.to_numeric(neighbors.get("rating_count"), errors="coerce").fillna(1).mean())
    closeness = float(np.exp(-mean_distance / 10.0))
    coverage = float(min(rating_count / 3.0, 1.0))
    score = round((0.75 * closeness) + (0.25 * coverage), 3)
    if score >= 0.72:
        label = "high"
    elif score >= 0.48:
        label = "moderate"
    else:
        label = "exploratory"
    return {"score": score, "label": label}


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


def _similarity_reason(reference_frame: pd.DataFrame, new_row: pd.Series, neighbor_row: pd.Series) -> str:
    reasons: list[tuple[str, float]] = []
    for feature, label in SIMILARITY_FEATURE_TEXT.items():
        if feature not in reference_frame.columns:
            continue
        series = pd.to_numeric(reference_frame[feature], errors="coerce")
        valid = series.notna()
        if valid.sum() < 3:
            continue
        scale = float(series[valid].std(ddof=0))
        if np.isclose(scale, 0.0):
            scale = 1.0
        new_value = pd.to_numeric(new_row.get(feature), errors="coerce")
        neighbor_value = pd.to_numeric(neighbor_row.get(feature), errors="coerce")
        if pd.isna(new_value) or pd.isna(neighbor_value):
            continue
        distance = abs(float(new_value) - float(neighbor_value)) / scale
        reasons.append((label, distance))
    if not reasons:
        return "Close pacing and response pattern."
    reasons.sort(key=lambda item: item[1])
    top_labels = [label for label, _ in reasons[:2]]
    if len(top_labels) == 1:
        return f"Similar {top_labels[0]}."
    return f"Similar {top_labels[0]} and {top_labels[1]}."


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


def _format_timestamp(seconds: float) -> str:
    total_seconds = max(int(seconds), 0)
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes}:{secs:02d}"


def _pick_spread_indices(values: pd.Series, top_k: int, largest: bool = True, min_gap: int = 1) -> list[int]:
    ordered = values.sort_values(ascending=not largest).index.tolist()
    selected: list[int] = []
    for idx in ordered:
        if all(abs(idx - previous) > min_gap for previous in selected):
            selected.append(int(idx))
        if len(selected) >= top_k:
            break
    return selected


def _moment_label(position_ratio: float, is_strong: bool) -> tuple[str, list[str], str]:
    if is_strong and position_ratio <= 0.2:
        return "Opening hook", ["attention", "clarity"], "The opening is one of the strongest response windows in the ad."
    if is_strong and position_ratio >= 0.72:
        return "Closing memory lift", ["memorability", "attention"], "The later section lands with relatively strong predicted response."
    if is_strong:
        return "High attention beat", ["attention"], "This moment stands out as one of the stronger response windows."
    if position_ratio <= 0.35:
        return "Early clarity dip", ["clarity"], "This early segment may be harder to follow than the surrounding moments."
    return "Potential drop-off", ["attention", "clarity"], "This segment looks weaker than the strongest moments in the ad."


def _track_band(percentile: float) -> str:
    if percentile >= 80:
        return "strong"
    if percentile >= 60:
        return "slightly_strong"
    if percentile <= 20:
        return "weak"
    if percentile <= 40:
        return "slightly_weak"
    return "average"


def _compute_track_value(row: pd.Series, weights: dict[str, float], reference_frame: pd.DataFrame) -> float:
    total = 0.0
    for feature, weight in weights.items():
        if feature not in reference_frame.columns:
            continue
        series = pd.to_numeric(reference_frame[feature], errors="coerce")
        if series.dropna().empty:
            continue
        mean_value = float(series.mean())
        std_value = float(series.std(ddof=0))
        if np.isclose(std_value, 0.0):
            std_value = 1.0
        row_value = pd.to_numeric(row.get(feature), errors="coerce")
        if pd.isna(row_value):
            row_value = mean_value
        total += weight * ((float(row_value) - mean_value) / std_value)
    return total


def _build_track_payload(reference_frame: pd.DataFrame, new_row: pd.Series) -> dict[str, dict[str, object]]:
    payload: dict[str, dict[str, object]] = {}
    for track_id, track_def in TRACK_DEFINITIONS.items():
        weights = track_def["weights"]
        reference_values = reference_frame.apply(lambda row: _compute_track_value(row, weights, reference_frame), axis=1)
        new_value = _compute_track_value(new_row, weights, reference_frame)
        mean_value = float(reference_values.mean()) if len(reference_values) else 0.0
        std_value = float(reference_values.std(ddof=0)) if len(reference_values) else 1.0
        if np.isclose(std_value, 0.0):
            std_value = 1.0
        percentile = float(100.0 * (reference_values <= new_value).sum() / max(len(reference_values), 1))
        score = float(np.clip(50.0 + (18.0 * ((new_value - mean_value) / std_value)), 0.0, 100.0))

        component_notes: list[tuple[str, float]] = []
        for feature, weight in weights.items():
            if feature not in reference_frame.columns:
                continue
            series = pd.to_numeric(reference_frame[feature], errors="coerce")
            if series.dropna().empty:
                continue
            mean_feature = float(series.mean())
            std_feature = float(series.std(ddof=0))
            if np.isclose(std_feature, 0.0):
                std_feature = 1.0
            row_value = pd.to_numeric(new_row.get(feature), errors="coerce")
            if pd.isna(row_value):
                continue
            contribution = weight * ((float(row_value) - mean_feature) / std_feature)
            component_notes.append((feature, float(contribution)))
        component_notes.sort(key=lambda item: abs(item[1]), reverse=True)
        top_components = []
        for feature, contribution in component_notes[:2]:
            positive_text, negative_text = TRACK_COMPONENT_TEXT.get(feature, (feature, feature))
            top_components.append(positive_text if contribution >= 0 else negative_text)

        short_text, long_text = TRACK_DESCRIPTIONS[track_id]
        payload[track_id] = {
            "label": track_def["label"],
            "score": round(score, 1),
            "percentile": round(percentile, 1),
            "band": _track_band(percentile),
            "short_description": short_text,
            "long_description": long_text,
            "why_it_matters": top_components,
        }
    return payload


def _creative_profile(track_payload: dict[str, dict[str, object]]) -> dict[str, str]:
    ranked = sorted(track_payload.items(), key=lambda item: float(item[1]["score"]), reverse=True)
    weakest = sorted(track_payload.items(), key=lambda item: float(item[1]["score"]))[0]
    strongest_id, strongest_payload = ranked[0]
    weakest_id, weakest_payload = weakest

    if strongest_id == "hook_strength" and weakest_id == "trust_close":
        return {
            "label": "Punchy opener",
            "summary": "The ad appears to win early attention more easily than it closes with reassurance or payoff.",
        }
    if strongest_id == "clarity_stability":
        return {
            "label": "Clear explainer",
            "summary": "The ad's strongest signal is steady readability rather than sudden spikes or theatrical peaks.",
        }
    if strongest_id == "value_lift":
        return {
            "label": "Late builder",
            "summary": "The ad appears to gather strength later, which often helps the product or offer land more clearly.",
        }
    if strongest_id == "trust_close":
        return {
            "label": "Confident closer",
            "summary": "The closing section looks calmer and steadier than the rest of the reference set, which can help reduce friction.",
        }
    return {
        "label": str(strongest_payload["label"]),
        "summary": f"The strongest signal in this cut is {str(strongest_payload['label']).lower()}, while {str(weakest_payload['label']).lower()} still looks less settled.",
    }


def _moment_payload(features_dir: Path, duration_sec: float, top_k: int = 2) -> list[dict[str, object]]:
    activation_path = features_dir / "activation_strength.csv"
    if not activation_path.exists():
        return []
    activation = pd.read_csv(activation_path)
    if activation.empty:
        return []
    n = len(activation)
    seconds_per_step = duration_sec / max(n, 1)
    gap = max(1, n // 8)
    strongest_indices = _pick_spread_indices(activation["mean_abs"], top_k=top_k, largest=True, min_gap=gap)
    weakest_indices = _pick_spread_indices(activation["mean_abs"], top_k=top_k, largest=False, min_gap=gap)

    moments: list[dict[str, object]] = []
    for idx in strongest_indices:
        start_sec = float(activation.iloc[idx]["timestep"]) * seconds_per_step
        ratio = idx / max(n - 1, 1)
        label, impact, summary = _moment_label(ratio, is_strong=True)
        moments.append(
            {
                "id": f"strong-{idx}",
                "start_sec": round(start_sec, 2),
                "end_sec": round(start_sec + seconds_per_step, 2),
                "label": label,
                "summary": summary,
                "impact": impact,
                "frame_index": int(idx),
                "timestamp_label": _format_timestamp(start_sec),
                "kind": "strong",
            }
        )
    for idx in weakest_indices:
        start_sec = float(activation.iloc[idx]["timestep"]) * seconds_per_step
        ratio = idx / max(n - 1, 1)
        label, impact, summary = _moment_label(ratio, is_strong=False)
        moments.append(
            {
                "id": f"weak-{idx}",
                "start_sec": round(start_sec, 2),
                "end_sec": round(start_sec + seconds_per_step, 2),
                "label": label,
                "summary": summary,
                "impact": impact,
                "frame_index": int(idx),
                "timestamp_label": _format_timestamp(start_sec),
                "kind": "weak",
            }
        )
    moments.sort(key=lambda item: (float(item["start_sec"]), str(item["kind"])))
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
    confidence = _confidence_payload(neighbors)
    creative_tracks = _build_track_payload(reference_frame, summary)
    creative_profile = _creative_profile(creative_tracks)

    for target in FOCUS_TARGETS:
        outward_name = TARGET_NAMES[target]
        score = float(target_scores[outward_name]["score"])
        dataset_mean = dataset_means[target]
        peer_mean = float(pd.to_numeric(neighbors[target], errors="coerce").mean())
        band = _band_for_target(target, score, dataset_mean)
        percentile = _target_percentile(reference_frame, target, score)
        summary_payload[outward_name] = {
            "band": band,
            "score": round(score, 3),
            "dataset_mean": round(dataset_mean, 3),
            "peer_mean": round(peer_mean, 3),
            "percentile": round(percentile, 1),
            "confidence_label": str(confidence["label"]),
            "confidence_score": float(confidence["score"]),
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

    moments = _moment_payload(features_dir, float(summary.get("duration_sec", 0.0)))
    frame_count = len(list((features_dir / "brain_frames").glob("frame_*.png")))
    seconds_per_frame = float(summary.get("duration_sec", 0.0)) / max(frame_count, 1) if frame_count else 0.0
    chapters = [
        {
            "title": str(moment["label"]),
            "timestamp_label": str(moment["timestamp_label"]),
            "start_sec": float(moment["start_sec"]),
            "frame_index": int(moment["frame_index"]),
        }
        for moment in moments
    ]

    activation_curve_plot = features_dir / "activation_curve.png"
    activation_curve_csv = features_dir / "activation_strength.csv"
    brain_strongest = features_dir / "brain_strongest.png"
    brain_animation = features_dir / "brain_animation.gif"
    top_roi_plot = features_dir / "top_roi_timecourses.png"

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
        "confidence": confidence,
        "creative_profile": creative_profile,
        "tracks": creative_tracks,
        "strengths": strengths,
        "risks": risks,
        "similar_ads": [
            {
                "ad_id": row.ad_id,
                "brand": row.brand,
                "distance": round(float(row.distance), 3),
                "why_similar": _similarity_reason(reference_frame, summary, pd.Series(row._asdict())),
            }
            for row in neighbors.itertuples()
        ],
        "moments": moments,
        "why": why,
        "assets": {
            "video_url": f"/v1/jobs/{job_id}/assets/source_video",
            "activation_curve_url": f"/v1/jobs/{job_id}/assets/activation_curve_plot" if activation_curve_plot.exists() else None,
            "activation_curve_csv_url": f"/v1/jobs/{job_id}/assets/activation_curve_csv" if activation_curve_csv.exists() else None,
            "brain_strongest_url": f"/v1/jobs/{job_id}/assets/brain_strongest" if brain_strongest.exists() else None,
            "brain_animation_url": f"/v1/jobs/{job_id}/assets/brain_animation" if brain_animation.exists() else None,
            "top_roi_timecourses_url": f"/v1/jobs/{job_id}/assets/top_roi_timecourses" if top_roi_plot.exists() else None,
        },
        "playback": {
            "frame_count": frame_count,
            "seconds_per_frame": round(seconds_per_frame, 4),
            "brain_frame_url_template": f"/v1/jobs/{job_id}/assets/brain_frame_{{index}}" if frame_count else None,
            "chapters": chapters,
        },
        "technical": {
            "top_rois": str(summary.get("top_rois", "")).split(",") if summary.get("top_rois") else [],
            "strongest_timestep": int(summary.get("strongest_timestep", 0)),
            "summary": summary.to_dict(),
        },
    }

    lines = [f"# Customer Report: {title}", "", "## Quick Read"]
    for label, payload in report["summary"].items():
        lines.append(
            f"- {label.title()}: {payload['band'].replace('_', ' ')}, "
            f"{payload['percentile']:.0f}th percentile, {payload['confidence_label']} confidence."
        )
    lines.extend(["", "## Creative Signals"])
    for payload in report["tracks"].values():
        lines.append(
            f"- {payload['label']}: {payload['band'].replace('_', ' ')}, "
            f"{payload['percentile']:.0f}th percentile. {payload['short_description']}"
        )
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
