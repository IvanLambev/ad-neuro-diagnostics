from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .insights import FOCUS_TARGETS, TARGET_DIRECTIONS, build_benchmark_summary
from .manifests import ProjectPaths, load_ratings
from .utils import ensure_dir, save_json

TARGET_TITLES = {
    "engagement": "Attention",
    "confusion": "Clarity",
    "memorability": "Memorability",
}

TARGET_SUMMARY_LABELS = {
    "engagement": "holding attention",
    "confusion": "keeping the message clear",
    "memorability": "sticking in memory",
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
    "audio_loudness_std": ("more variation in audio intensity", "steadier audio intensity"),
    "audio_rms_mean": ("stronger average audio energy", "lighter average audio energy"),
    "word_count": ("more spoken words", "fewer spoken words"),
    "speech_density": ("faster speaking pace", "slower speaking pace"),
    "subtitle_density": ("denser on-screen language", "lighter on-screen language"),
    "shot_count": ("more scene changes", "fewer scene changes"),
    "cut_rate": ("faster editing pace", "slower editing pace"),
    "colorfulness_mean": ("more colorful visuals", "more muted visuals"),
    "n_timesteps": ("a longer unfolding arc", "a shorter unfolding arc"),
    "duration_sec_x": ("a longer runtime", "a shorter runtime"),
    "duration_sec_y": ("a longer runtime", "a shorter runtime"),
}


def ratings_summary(paths: ProjectPaths, ad_id: str) -> pd.DataFrame:
    ratings = load_ratings(paths)
    if ratings.empty:
        return pd.DataFrame()
    subset = ratings.loc[ratings["ad_id"] == ad_id]
    if subset.empty:
        return pd.DataFrame()
    numeric = subset[
        ["engagement", "clarity", "emotional_intensity", "confusion", "memorability"]
    ].apply(pd.to_numeric, errors="coerce")
    return pd.DataFrame(
        {
            "metric": numeric.columns,
            "mean": numeric.mean().values,
            "count": numeric.count().values,
        }
    )


def _single_summary_text(summary: pd.Series) -> str:
    top_rois = summary.get("top_rois", "")
    top_text = top_rois if top_rois else "not available"
    return (
        f"Strongest predicted segment occurs at timestep {int(summary['strongest_timestep'])}. "
        f"The activation profile peaks at {summary['mean_abs_max']:.3f} on the mean absolute curve. "
        f"Top ROI signals: {top_text}."
    )


def _format_target_label(target: str) -> str:
    return target.replace("_", " ").title()


def _target_title(target: str) -> str:
    return TARGET_TITLES.get(target, _format_target_label(target))


def _status_word(target: str, score: float, mean_value: float) -> str:
    direction = TARGET_DIRECTIONS.get(target, 1.0)
    delta = (score - mean_value) * direction
    if delta >= 0.5:
        return "strong"
    if delta >= 0.15:
        return "slightly strong"
    if delta <= -0.5:
        return "weak"
    if delta <= -0.15:
        return "slightly weak"
    return "around average"


def _benchmark_line(
    target_row: dict[str, object],
    similar_means: dict[str, float],
    dataset_size: int,
) -> str:
    target = str(target_row["target"])
    score = float(target_row["score"])
    dataset_mean = float(target_row["dataset_mean"])
    better_than = int(target_row["better_than_count"])
    total_others = int(target_row["total_others"])
    peer_mean = similar_means.get(target)
    delta_to_dataset = score - dataset_mean
    direction = TARGET_DIRECTIONS.get(target, 1.0)
    raw_dataset_relation = "higher than" if delta_to_dataset >= 0 else "lower than"
    target_dataset_relation = "better" if delta_to_dataset * direction >= 0 else "worse"

    line = (
        f"- {_format_target_label(target)}: {score:.2f}, {raw_dataset_relation} the {dataset_size}-ad mean "
        f"of {dataset_mean:.2f}, which is {target_dataset_relation} for this target. "
        f"It ranks ahead of {better_than} of {total_others} historical ads."
    )
    if peer_mean is not None and pd.notna(peer_mean):
        raw_peer_relation = "higher than" if score - peer_mean >= 0 else "lower than"
        target_peer_relation = "better" if (score - peer_mean) * direction >= 0 else "worse"
        line += (
            f" Versus the closest ads, it is {raw_peer_relation} the peer mean of {peer_mean:.2f}, "
            f"which is {target_peer_relation} for this target."
    )
    return line


def _plain_driver_text(driver: dict[str, object]) -> str:
    feature = str(driver["feature"])
    value = float(driver["feature_value"])
    mean_value = float(driver["dataset_mean"])
    is_high = value >= mean_value
    high_text, low_text = FEATURE_PLAIN_ENGLISH.get(
        feature,
        (f"higher `{feature}`", f"lower `{feature}`"),
    )
    return high_text if is_high else low_text


def _driver_line(target: str, drivers: list[dict[str, object]]) -> str:
    if not drivers:
        return f"- {_target_title(target)}: not enough variation yet for a stable read."

    pieces = []
    for driver in drivers:
        feature = str(driver["feature"])
        value = float(driver["feature_value"])
        mean_value = float(driver["dataset_mean"])
        pieces.append(
            f"{_plain_driver_text(driver)} (`{feature}`: {value:.2f} vs set mean {mean_value:.2f})"
        )
    return f"- {_target_title(target)}: " + ", ".join(pieces) + "."


def _executive_summary_lines(benchmark: dict[str, object]) -> list[str]:
    lines: list[str] = []
    for row in benchmark["target_benchmarks"]:
        target = str(row["target"])
        score = float(row["score"])
        mean_value = float(row["dataset_mean"])
        status = _status_word(target, score, mean_value)
        lines.append(
            f"- {_target_title(target)}: {status} versus the current {int(benchmark['dataset_size'])}-ad reference set."
        )
    return lines


def _strength_risk_lines(benchmark: dict[str, object]) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    risks: list[str] = []
    for row in benchmark["target_benchmarks"]:
        target = str(row["target"])
        score = float(row["score"])
        mean_value = float(row["dataset_mean"])
        status = _status_word(target, score, mean_value)
        driver_texts = [
            _plain_driver_text(driver)
            for driver in benchmark["likely_drivers"].get(target, [])
        ]
        driver_suffix = f" Likely reasons: {', '.join(driver_texts[:2])}." if driver_texts else ""

        if target == "confusion":
            if status in {"strong", "slightly strong"}:
                strengths.append(f"The ad looks relatively clear compared with the reference set.{driver_suffix}")
            elif status in {"weak", "slightly weak"}:
                risks.append(f"The ad may be harder to follow than comparable ads.{driver_suffix}")
        else:
            readable = TARGET_SUMMARY_LABELS.get(target, target)
            if status in {"strong", "slightly strong"}:
                strengths.append(f"The ad looks better than average at {readable}.{driver_suffix}")
            elif status in {"weak", "slightly weak"}:
                risks.append(f"The ad looks weaker than average at {readable}.{driver_suffix}")
    return strengths, risks


def _customer_friendly_similar_ads(similar_ads: pd.DataFrame) -> list[str]:
    if similar_ads.empty:
        return ["- We do not yet have enough comparable ads in the current reference set."]

    lines = []
    for row in similar_ads.itertuples():
        brand = getattr(row, "brand", "unknown brand")
        lines.append(
            f"- `{row.ad_id}` ({brand}) is one of the closest matches in pacing, feature pattern, and predicted response shape."
        )
    return lines


def generate_single_report(paths: ProjectPaths, ad_id: str):
    features_dir = paths.features_dir(ad_id)
    reports_dir = ensure_dir(paths.reports_dir(ad_id))
    summary_path = features_dir / "summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing features for {ad_id}; run extract-features first")
    summary = pd.read_csv(summary_path).iloc[0]
    report_path = reports_dir / "single_report.md"
    ratings = ratings_summary(paths, ad_id)
    benchmark = None
    try:
        benchmark = build_benchmark_summary(paths, ad_id, targets=FOCUS_TARGETS, similar_k=3)
    except (FileNotFoundError, ValueError, KeyError):
        benchmark = None

    lines = [
        f"# Single Ad Report: {ad_id}",
    ]
    if benchmark is not None:
        similar_ads = pd.DataFrame(benchmark["similar_ads"])
        if not similar_ads.empty:
            similar_ads.to_csv(reports_dir / "similar_ads.csv", index=False)
        save_json(reports_dir / "benchmark_summary.json", benchmark)
        strengths, risks = _strength_risk_lines(benchmark)

        lines.extend(["", "## Quick Read"])
        lines.extend(_executive_summary_lines(benchmark))

        lines.extend(["", "## What This Means"])
        if strengths:
            lines.append("### Strengths")
            lines.extend(f"- {item}" for item in strengths)
        if risks:
            lines.append("### Risks")
            lines.extend(f"- {item}" for item in risks)
        if not strengths and not risks:
            lines.append("- This ad looks broadly middle-of-the-pack in the current reference set.")

        lines.extend(["", "## Similar Ads You Should Compare Against"])
        lines.extend(_customer_friendly_similar_ads(similar_ads))

        lines.extend(["", "## Historical Benchmark"])
        for target_row in benchmark["target_benchmarks"]:
            lines.append(
                _benchmark_line(
                    target_row,
                    benchmark["similar_means"],
                    int(benchmark["dataset_size"]),
                )
            )

        if not similar_ads.empty:
            display_cols = [
                column
                for column in ["ad_id", "brand", "distance", *FOCUS_TARGETS]
                if column in similar_ads.columns
            ]
            lines.extend(
                [
                    "",
                    "## Similar Ads Table",
                    similar_ads[display_cols].to_markdown(index=False),
                ]
            )

        lines.extend(["", "## Why The System Thinks That"])
        for target in FOCUS_TARGETS:
            lines.append(_driver_line(target, benchmark["likely_drivers"].get(target, [])))

    lines.extend(
        [
            "",
            "## Technical Appendix",
            _single_summary_text(summary),
            "",
            "### Artifacts",
            f"- Activation curve: `{features_dir / 'activation_strength.csv'}`",
            f"- Brain strongest frame: `{features_dir / 'brain_strongest.png'}`",
            f"- Brain animation: `{features_dir / 'brain_animation.gif'}`",
        ]
    )

    if not ratings.empty:
        lines.extend(["", "### Annotation Summary", ratings.to_markdown(index=False)])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def generate_compare_report(paths: ProjectPaths, ad_a: str, ad_b: str):
    features_a = pd.read_csv(paths.features_dir(ad_a) / "activation_strength.csv")
    features_b = pd.read_csv(paths.features_dir(ad_b) / "activation_strength.csv")
    summary_a = pd.read_csv(paths.features_dir(ad_a) / "summary.csv").iloc[0]
    summary_b = pd.read_csv(paths.features_dir(ad_b) / "summary.csv").iloc[0]

    compare_dir = ensure_dir(paths.root / "reports" / f"{ad_a}_vs_{ad_b}")
    plot_path = compare_dir / "activation_compare.png"
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(features_a["timestep"], features_a["mean_abs"], label=ad_a)
    ax.plot(features_b["timestep"], features_b["mean_abs"], label=ad_b)
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Mean absolute response")
    ax.set_title("Activation curve comparison")
    ax.legend()
    fig.savefig(plot_path, dpi=160, bbox_inches="tight")
    plt.close(fig)

    report_path = compare_dir / "compare_report.md"
    delta = summary_a["mean_abs_max"] - summary_b["mean_abs_max"]
    stronger = ad_a if delta >= 0 else ad_b
    lines = [
        f"# Compare Ads: {ad_a} vs {ad_b}",
        "",
        "## Deterministic Summary",
        (
            f"{stronger} shows the higher peak mean-absolute predicted response by "
            f"{abs(delta):.3f}. "
            f"{ad_a} strongest timestep: {int(summary_a['strongest_timestep'])}; "
            f"{ad_b} strongest timestep: {int(summary_b['strongest_timestep'])}."
        ),
        "",
        "## Key Deltas",
        f"- {ad_a} top ROIs: {summary_a.get('top_rois', '')}",
        f"- {ad_b} top ROIs: {summary_b.get('top_rois', '')}",
        f"- Activation plot: `{plot_path}`",
    ]

    ratings_a = ratings_summary(paths, ad_a)
    ratings_b = ratings_summary(paths, ad_b)
    if not ratings_a.empty and not ratings_b.empty:
        merged = ratings_a.merge(
            ratings_b, on="metric", suffixes=(f"_{ad_a}", f"_{ad_b}")
        )
        lines.extend(["", "## Annotation Comparison", merged.to_markdown(index=False)])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
