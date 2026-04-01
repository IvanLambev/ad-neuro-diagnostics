from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from .manifests import ProjectPaths, load_ratings
from .utils import ensure_dir


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


def generate_single_report(paths: ProjectPaths, ad_id: str):
    features_dir = paths.features_dir(ad_id)
    reports_dir = ensure_dir(paths.reports_dir(ad_id))
    summary_path = features_dir / "summary.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing features for {ad_id}; run extract-features first")
    summary = pd.read_csv(summary_path).iloc[0]
    report_path = reports_dir / "single_report.md"
    ratings = ratings_summary(paths, ad_id)

    lines = [
        f"# Single Ad Report: {ad_id}",
        "",
        "## Summary",
        _single_summary_text(summary),
        "",
        "## Artifacts",
        f"- Activation curve: `{features_dir / 'activation_strength.csv'}`",
        f"- Brain strongest frame: `{features_dir / 'brain_strongest.png'}`",
        f"- Brain animation: `{features_dir / 'brain_animation.gif'}`",
    ]
    if not ratings.empty:
        lines.extend(["", "## Annotation Summary", ratings.to_markdown(index=False)])
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
