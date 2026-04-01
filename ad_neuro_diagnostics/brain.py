from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import mne
import nibabel as nib
import numpy as np
from mne.datasets import fetch_hcp_mmp_parcellation
from nilearn.datasets import fetch_surf_fsaverage
from nilearn.plotting import plot_surf_stat_map


FSAVERAGE5_VERTICES_PER_HEMI = 10242


@lru_cache
def get_hcp_labels(hemi: str) -> dict[str, np.ndarray]:
    if hemi not in {"left", "right"}:
        raise ValueError(f"Invalid hemisphere: {hemi}")
    subjects_dir = Path(mne.datasets.sample.data_path()) / "subjects"
    fetch_hcp_mmp_parcellation(subjects_dir=subjects_dir, combine=False, accept=True, verbose=False)
    labels = mne.read_labels_from_annot("fsaverage", "HCPMMP1", hemi="both", subjects_dir=subjects_dir)
    out: dict[str, np.ndarray] = {}
    offset = FSAVERAGE5_VERTICES_PER_HEMI if hemi == "right" else 0
    for label in labels:
        name = label.name
        if hemi == "left" and not name.endswith("-lh"):
            continue
        if hemi == "right" and not name.endswith("-rh"):
            continue
        clean = name[2:].replace("_ROI", "").replace("-lh", "").replace("-rh", "")
        vertices = np.array(label.vertices)
        vertices = vertices[vertices < FSAVERAGE5_VERTICES_PER_HEMI] + offset
        out[clean] = vertices
    return out


def summarize_by_roi(frame: np.ndarray, hemi: str) -> tuple[list[str], np.ndarray]:
    labels = get_hcp_labels(hemi)
    rois = list(labels.keys())
    values = np.array([frame[idx].mean() for idx in labels.values()], dtype=np.float32)
    return rois, values


def roi_timecourses(preds: np.ndarray) -> tuple[dict[str, np.ndarray], dict[str, list[str]]]:
    left_labels, _ = summarize_by_roi(preds[0], hemi="left")
    right_labels, _ = summarize_by_roi(preds[0], hemi="right")
    left_values = np.vstack([summarize_by_roi(frame, hemi="left")[1] for frame in preds])
    right_values = np.vstack([summarize_by_roi(frame, hemi="right")[1] for frame in preds])
    return {"left": left_values, "right": right_values}, {"left": left_labels, "right": right_labels}


def top_rois_from_timecourses(left: np.ndarray, right: np.ndarray, labels: dict[str, list[str]], top_k: int) -> list[str]:
    ranked: list[tuple[str, float]] = []
    for hemi_key, data in (("lh", left), ("rh", right)):
        hemi_name = "left" if hemi_key == "lh" else "right"
        for idx, label in enumerate(labels[hemi_name]):
            ranked.append((f"{label}-{hemi_key}", float(np.abs(data[:, idx]).max())))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return [name for name, _ in ranked[:top_k]]


def can_map_to_brain(preds: np.ndarray) -> bool:
    return preds.ndim == 2 and preds.shape[1] == 2 * FSAVERAGE5_VERTICES_PER_HEMI


def plot_brain_frame(frame: np.ndarray, output_path: Path, title: str, vmin: float, vmax: float) -> None:
    fs = fetch_surf_fsaverage(mesh="fsaverage5")
    left = frame[:FSAVERAGE5_VERTICES_PER_HEMI]
    right = frame[FSAVERAGE5_VERTICES_PER_HEMI:]
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), subplot_kw={"projection": "3d"})
    plot_surf_stat_map(
        surf_mesh=(nib.load(fs.infl_left).darrays[0].data, nib.load(fs.infl_left).darrays[1].data),
        stat_map=left,
        hemi="left",
        bg_map=nib.load(fs.sulc_left).darrays[0].data,
        view=(0, 180),
        axes=axes[0],
        figure=fig,
        cmap="hot",
        colorbar=False,
        vmin=vmin,
        vmax=vmax,
    )
    plot_surf_stat_map(
        surf_mesh=(nib.load(fs.infl_right).darrays[0].data, nib.load(fs.infl_right).darrays[1].data),
        stat_map=right,
        hemi="right",
        bg_map=nib.load(fs.sulc_right).darrays[0].data,
        view=(0, 0),
        axes=axes[1],
        figure=fig,
        cmap="hot",
        colorbar=True,
        vmin=vmin,
        vmax=vmax,
    )
    fig.suptitle(title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_gif_from_frames(frame_paths: list[Path], output_path: Path, fps: float) -> None:
    from PIL import Image

    if not frame_paths:
        return
    images = [Image.open(frame_path) for frame_path in frame_paths]
    duration_ms = max(int(1000 / max(fps, 1e-6)), 1)
    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=duration_ms,
        loop=0,
    )
    for image in images:
        image.close()

