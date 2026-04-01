from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from ad_neuro_diagnostics.youtube_ingest import (
    DownloadedVideo,
    ensure_project,
    parse_video_requests,
    write_download_outputs,
)
from ad_neuro_diagnostics.utils import ensure_dir, stable_slug


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download YouTube ad videos from a text file and build project-ready CSV manifests."
    )
    parser.add_argument(
        "--input-txt",
        type=Path,
        default=Path("videos.txt"),
        help="Text file with one 'Brand: URL' entry per line.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("workspace_local"),
        help="Local project workspace where manifests and downloads will be stored.",
    )
    parser.add_argument(
        "--downloads-dir",
        type=Path,
        default=None,
        help="Optional override for where downloaded source videos should live.",
    )
    parser.add_argument(
        "--validation-ratio",
        type=float,
        default=0.3,
        help="Fraction of brands to place into the validation split.",
    )
    parser.add_argument(
        "--default-language",
        default="unknown",
        help="Fallback language code when YouTube metadata does not expose one.",
    )
    return parser.parse_args()


def discover_download_path(downloads_dir: Path, video_id: str) -> Path:
    matches = [
        path
        for path in downloads_dir.glob(f"{video_id}.*")
        if path.is_file() and path.suffix not in {".part", ".ytdl"}
    ]
    if not matches:
        raise FileNotFoundError(f"Could not find a downloaded file for video id '{video_id}'")
    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def write_failures_csv(project_root: Path, failures: list[dict[str, str]]) -> Path:
    paths = ensure_project(project_root)
    output_path = paths.manifests_dir / "youtube_failures.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["brand", "url", "error"])
        writer.writeheader()
        writer.writerows(failures)
    return output_path


def clear_failures_csv(project_root: Path) -> None:
    paths = ensure_project(project_root)
    failures_path = paths.manifests_dir / "youtube_failures.csv"
    if failures_path.exists():
        failures_path.unlink()


def download_videos(
    input_txt: Path,
    downloads_dir: Path,
    default_language: str,
) -> tuple[list[DownloadedVideo], list[dict[str, str]]]:
    try:
        from yt_dlp import YoutubeDL
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "yt-dlp is not installed in this environment. Run 'pip install -e \".[download]\"'."
        ) from exc

    requests = parse_video_requests(input_txt)
    ensure_dir(downloads_dir)
    archive_file = downloads_dir / "download_archive.txt"
    ffmpeg_available = shutil.which("ffmpeg") is not None
    ydl_opts = {
        "format": (
            "bestvideo*+bestaudio/best"
            if ffmpeg_available
            else "best[ext=mp4]/best[ext=webm]/best"
        ),
        "noplaylist": True,
        "outtmpl": str(downloads_dir / "%(id)s.%(ext)s"),
        "windowsfilenames": True,
        "download_archive": str(archive_file),
        "quiet": False,
    }
    if ffmpeg_available:
        ydl_opts["merge_output_format"] = "mp4"
    else:
        print("ffmpeg was not found, so downloads will use a single-file fallback format.")
    metadata_opts = {
        "noplaylist": True,
        "quiet": False,
        "skip_download": True,
    }

    downloads: list[DownloadedVideo] = []
    failures: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    with YoutubeDL(ydl_opts) as ydl, YoutubeDL(metadata_opts) as metadata_ydl:
        for request in requests:
            try:
                info = ydl.extract_info(request.url, download=True)
            except Exception as exc:
                failures.append(
                    {
                        "brand": request.brand,
                        "url": request.url,
                        "error": str(exc),
                    }
                )
                print(f"Failed to download {request.url}: {exc}")
                continue
            if info is None:
                try:
                    info = metadata_ydl.extract_info(request.url, download=False)
                except Exception as exc:
                    failures.append(
                        {
                            "brand": request.brand,
                            "url": request.url,
                            "error": f"metadata lookup failed after archive skip: {exc}",
                        }
                    )
                    print(f"Failed to read metadata for {request.url}: {exc}")
                    continue
            if info is None:
                failures.append(
                    {
                        "brand": request.brand,
                        "url": request.url,
                        "error": "yt-dlp returned no metadata",
                    }
                )
                continue
            video_id = str(info["id"])
            key = (stable_slug(request.brand), video_id)
            if key in seen_keys:
                print(f"Skipping duplicate entry for brand '{request.brand}' and video '{video_id}'")
                continue
            seen_keys.add(key)
            try:
                source_path = discover_download_path(downloads_dir, video_id)
            except FileNotFoundError as exc:
                failures.append(
                    {
                        "brand": request.brand,
                        "url": request.url,
                        "error": str(exc),
                    }
                )
                print(f"Failed to locate downloaded file for {request.url}: {exc}")
                continue
            downloads.append(
                DownloadedVideo(
                    brand=request.brand,
                    url=request.url,
                    video_id=video_id,
                    title=str(info.get("title") or video_id),
                    channel=str(info.get("channel") or info.get("uploader") or ""),
                    duration_sec=float(info["duration"]) if info.get("duration") else None,
                    source_path=source_path,
                    language=str(info.get("language") or default_language),
                )
            )
    return downloads, failures


def main() -> None:
    args = parse_args()
    project_root = args.project_root.resolve()
    downloads_dir = (args.downloads_dir or (project_root / "source_videos")).resolve()
    downloads, failures = download_videos(
        input_txt=args.input_txt.resolve(),
        downloads_dir=downloads_dir,
        default_language=args.default_language,
    )
    if not downloads:
        failures_csv = write_failures_csv(project_root=project_root, failures=failures)
        raise SystemExit(
            f"No videos were downloaded successfully. Failure details were written to {failures_csv}"
        )
    ads_csv, catalog_csv = write_download_outputs(
        project_root=project_root,
        downloads=downloads,
        validation_ratio=args.validation_ratio,
    )
    print(f"Downloaded {len(downloads)} videos into {downloads_dir}")
    print(f"Wrote project manifest to {ads_csv}")
    print(f"Wrote source catalog to {catalog_csv}")
    if failures:
        failures_csv = write_failures_csv(project_root=project_root, failures=failures)
        print(f"{len(failures)} videos failed and were recorded in {failures_csv}")
    else:
        clear_failures_csv(project_root=project_root)


if __name__ == "__main__":
    main()
