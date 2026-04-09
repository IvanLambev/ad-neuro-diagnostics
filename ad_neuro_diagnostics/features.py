from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .brain import (
    can_map_to_brain,
    plot_brain_frame,
    roi_timecourses,
    save_gif_from_frames,
    top_rois_from_timecourses,
)
from .manifests import ProjectPaths, load_ads, load_clips
from .utils import ensure_dir, robust_scale, save_json


def activation_frame(preds: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestep": np.arange(len(preds)),
            "mean_abs": np.abs(preds).mean(axis=1),
            "max_abs": np.abs(preds).max(axis=1),
            "mean_signed": preds.mean(axis=1),
            "volatility": np.r_[0.0, np.abs(np.diff(np.abs(preds).mean(axis=1)))],
        }
    )


def summarize_temporal_features(series: pd.Series, prefix: str) -> dict[str, float]:
    n = len(series)
    split1 = max(1, n // 3)
    split2 = max(split1 + 1, (2 * n) // 3)
    early = series.iloc[:split1].mean()
    mid = series.iloc[split1:split2].mean()
    late = series.iloc[split2:].mean()
    peaks = (
        (series > series.shift(1, fill_value=series.iloc[0]))
        & (series > series.shift(-1, fill_value=series.iloc[-1]))
    ).sum()
    return {
        f"{prefix}_mean": float(series.mean()),
        f"{prefix}_std": float(series.std(ddof=0)),
        f"{prefix}_max": float(series.max()),
        f"{prefix}_argmax": int(series.idxmax()),
        f"{prefix}_early_mean": float(early),
        f"{prefix}_mid_mean": float(mid),
        f"{prefix}_late_mean": float(late),
        f"{prefix}_peak_count": int(peaks),
    }


def media_features_from_clip(clip_row: pd.Series, events_path: Path | None = None) -> dict[str, float]:
    features = {
        "duration_sec": float(clip_row.get("duration_sec", np.nan))
        if pd.notna(clip_row.get("duration_sec", np.nan))
        else np.nan,
        "fps": float(clip_row.get("fps", np.nan))
        if pd.notna(clip_row.get("fps", np.nan))
        else np.nan,
        "width": float(clip_row.get("width", np.nan))
        if pd.notna(clip_row.get("width", np.nan))
        else np.nan,
        "height": float(clip_row.get("height", np.nan))
        if pd.notna(clip_row.get("height", np.nan))
        else np.nan,
        "audio_hz": float(clip_row.get("audio_hz", np.nan))
        if pd.notna(clip_row.get("audio_hz", np.nan))
        else np.nan,
    }
    if events_path is not None and events_path.exists():
        events = pd.read_csv(events_path)
        words = events.loc[events["type"] == "Word"] if "type" in events else pd.DataFrame()
        duration = (
            features["duration_sec"]
            if pd.notna(features["duration_sec"]) and features["duration_sec"] > 0
            else np.nan
        )
        word_count = float(len(words))
        features["word_count"] = word_count
        features["speech_density"] = (
            word_count / duration if pd.notna(duration) and duration else np.nan
        )
        features["subtitle_density"] = (
            word_count / duration if pd.notna(duration) and duration else np.nan
        )
    return features


def sampled_video_features(clip_path: Path) -> dict[str, float]:
    try:
        from moviepy import VideoFileClip
        with VideoFileClip(str(clip_path)) as clip:
            duration = clip.duration or 0.0
            sample_times = np.linspace(
                0,
                max(duration - 1e-3, 0.0),
                num=max(2, min(24, int(duration) + 1)),
            )
            frames = np.array([clip.get_frame(float(t)) for t in sample_times], dtype=np.float32)
            if frames.ndim != 4:
                return {}

            gray = frames.mean(axis=3)
            brightness = gray.mean(axis=(1, 2))
            diffs = (
                np.abs(np.diff(gray, axis=0)).mean(axis=(1, 2))
                if len(gray) > 1
                else np.array([0.0], dtype=np.float32)
            )
            rg = np.abs(frames[:, :, :, 0] - frames[:, :, :, 1])
            yb = np.abs(0.5 * (frames[:, :, :, 0] + frames[:, :, :, 1]) - frames[:, :, :, 2])
            colorfulness = np.sqrt(rg.var(axis=(1, 2)) + yb.var(axis=(1, 2))) + 0.3 * np.sqrt(
                (rg.mean(axis=(1, 2)) ** 2) + (yb.mean(axis=(1, 2)) ** 2)
            )

            audio_features = {}
            if clip.audio is not None:
                audio = clip.audio.to_soundarray(fps=22050)
                if audio.size:
                    mono = audio.mean(axis=1) if audio.ndim == 2 else audio
                    window = max(1, len(mono) // 20)
                    rms = np.sqrt(np.convolve(mono**2, np.ones(window) / window, mode="valid"))
                    audio_features = {
                        "audio_loudness_mean": float(np.mean(np.abs(mono))),
                        "audio_loudness_std": float(np.std(np.abs(mono))),
                        "audio_rms_mean": float(np.mean(rms)),
                    }
    except Exception:
        return {}

    shot_threshold = float(np.mean(diffs) + np.std(diffs))
    shot_count = int((diffs > shot_threshold).sum() + 1)
    return {
        "brightness_mean": float(np.mean(brightness)),
        "brightness_std": float(np.std(brightness)),
        "colorfulness_mean": float(np.mean(colorfulness)),
        "motion_mean": float(np.mean(diffs)),
        "motion_std": float(np.std(diffs)),
        "shot_count": float(shot_count),
        "cut_rate": float(shot_count / max(duration, 1e-6)),
        **audio_features,
    }


def extract_features_for_ad(
    paths: ProjectPaths, ad_id: str, top_k: int = 10, fps: float = 1.0
) -> dict[str, str | int | float]:
    raw_dir = paths.raw_dir(ad_id)
    preds_path = raw_dir / "preds.npy"
    events_path = raw_dir / "events.csv"
    if not preds_path.exists():
        raise FileNotFoundError(f"Missing preds.npy for {ad_id}")
    preds = np.load(preds_path)
    if preds.ndim != 2:
        raise ValueError(f"Expected 2D predictions for {ad_id}, got {preds.shape}")

    features_dir = ensure_dir(paths.features_dir(ad_id))
    activation = activation_frame(preds)
    activation.to_csv(features_dir / "activation_strength.csv", index=False)

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(activation["timestep"], activation["mean_abs"], label="Mean absolute", linewidth=2)
    ax.plot(activation["timestep"], activation["max_abs"], label="Max absolute", linewidth=1.5, alpha=0.75)
    ax.set_title("Activation curve")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Predicted response")
    ax.legend()
    fig.savefig(features_dir / "activation_curve.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    normalized_preds = robust_scale(preds).reshape(preds.shape)
    norm_activation = activation_frame(normalized_preds)
    norm_activation.to_csv(features_dir / "activation_strength_normalized.csv", index=False)

    strongest_idx = int(activation["mean_abs"].idxmax())
    strongest_frame = preds[strongest_idx]
    clip_row = load_clips(paths).set_index("ad_id").loc[ad_id].to_dict()
    ad_row = load_ads(paths).set_index("ad_id").loc[ad_id].to_dict()
    merged_meta = {**ad_row, **clip_row}

    summary = {
        "ad_id": ad_id,
        "n_timesteps": int(preds.shape[0]),
        "n_vertices": int(preds.shape[1]),
        "strongest_timestep": strongest_idx,
        **summarize_temporal_features(activation["mean_abs"], "mean_abs"),
        **summarize_temporal_features(activation["max_abs"], "max_abs"),
        **media_features_from_clip(
            pd.Series(merged_meta), events_path=events_path if events_path.exists() else None
        ),
        **sampled_video_features(Path(str(clip_row["clip_path"]))),
    }

    top_rois: list[str] = []
    if can_map_to_brain(preds):
        roi_values, roi_labels = roi_timecourses(preds)
        left_df = pd.DataFrame(
            roi_values["left"], columns=[f"{label}-lh" for label in roi_labels["left"]]
        )
        right_df = pd.DataFrame(
            roi_values["right"], columns=[f"{label}-rh" for label in roi_labels["right"]]
        )
        roi_df = pd.concat([pd.Series(np.arange(len(preds)), name="timestep"), left_df, right_df], axis=1)
        roi_df.to_csv(features_dir / "roi_timecourses_all.csv", index=False)

        top_rois = top_rois_from_timecourses(
            roi_values["left"], roi_values["right"], roi_labels, top_k=top_k
        )
        roi_df[["timestep", *top_rois]].to_csv(
            features_dir / "top_roi_timecourses.csv", index=False
        )
        pd.DataFrame({"roi": top_rois}).to_csv(features_dir / "top_rois.csv", index=False)

        fig, ax = plt.subplots(figsize=(12, 5))
        for roi_name in top_rois:
            ax.plot(roi_df["timestep"], roi_df[roi_name], label=roi_name)
        ax.set_title("Top ROI timecourses")
        ax.set_xlabel("Timestep")
        ax.set_ylabel("Predicted ROI response")
        ax.legend(ncol=2, fontsize=8)
        fig.savefig(features_dir / "top_roi_timecourses.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

        abs_max = float(np.abs(preds).max())
        plot_brain_frame(
            strongest_frame,
            features_dir / "brain_strongest.png",
            f"Strongest predicted response frame #{strongest_idx}",
            -abs_max,
            abs_max,
        )
        frame_dir = ensure_dir(features_dir / "brain_frames")
        frame_paths = []
        for idx, frame in enumerate(preds):
            frame_path = frame_dir / f"frame_{idx:03d}.png"
            plot_brain_frame(
                frame,
                frame_path,
                f"Predicted response timestep #{idx}",
                -abs_max,
                abs_max,
            )
            frame_paths.append(frame_path)
        save_gif_from_frames(frame_paths, features_dir / "brain_animation.gif", fps=fps)

    summary["top_rois"] = ",".join(top_rois)
    save_json(features_dir / "summary.json", summary)
    pd.DataFrame([summary]).to_csv(features_dir / "summary.csv", index=False)
    return summary


def extract_all_features(paths: ProjectPaths, top_k: int = 10, fps: float = 1.0) -> pd.DataFrame:
    ads = load_ads(paths)
    summaries = []
    for ad_id in ads["ad_id"]:
        raw_dir = paths.raw_dir(ad_id)
        if not (raw_dir / "preds.npy").exists():
            continue
        summaries.append(extract_features_for_ad(paths, ad_id, top_k=top_k, fps=fps))
    output = pd.DataFrame(summaries)
    if not output.empty:
        output.to_csv(paths.manifests_dir / "ad_features.csv", index=False)
    return output
