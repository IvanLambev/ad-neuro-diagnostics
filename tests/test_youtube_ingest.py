from __future__ import annotations

from pathlib import Path

from ad_neuro_diagnostics.youtube_ingest import (
    DownloadedVideo,
    assign_splits,
    build_ads_frame,
    parse_video_requests,
    write_download_outputs,
)


def test_parse_video_requests_reads_brand_and_url(tmp_path: Path):
    input_txt = tmp_path / "videos.txt"
    input_txt.write_text(
        "\n".join(
            [
                "# comment",
                "Nike: https://www.youtube.com/watch?v=abc123",
                "",
                "Sprite: https://www.youtube.com/watch?v=xyz789",
            ]
        ),
        encoding="utf-8",
    )

    items = parse_video_requests(input_txt)

    assert len(items) == 2
    assert items[0].brand == "Nike"
    assert items[1].url.endswith("xyz789")


def test_assign_splits_groups_same_brand_regardless_of_case():
    splits = assign_splits(["Nike", "nike", "Sprite", "Sony"], validation_ratio=0.34)

    assert splits["Nike"] == splits["nike"]
    assert set(splits.values()) == {"train", "validation"}


def test_build_ads_frame_creates_project_ready_columns(tmp_path: Path):
    downloads = [
        DownloadedVideo(
            brand="Nike",
            url="https://www.youtube.com/watch?v=abc123",
            video_id="abc123",
            title="Title A",
            channel="Channel A",
            duration_sec=15.0,
            source_path=tmp_path / "abc123.mp4",
            language="en",
        ),
        DownloadedVideo(
            brand="Sprite",
            url="https://www.youtube.com/watch?v=xyz789",
            video_id="xyz789",
            title="Title B",
            channel="Channel B",
            duration_sec=30.0,
            source_path=tmp_path / "xyz789.webm",
            language="en",
        ),
    ]

    frame = build_ads_frame(downloads, validation_ratio=0.5)

    assert frame.columns.tolist() == [
        "ad_id",
        "source_path",
        "brand",
        "campaign",
        "variant",
        "duration_sec",
        "language",
        "split",
    ]
    assert frame["ad_id"].tolist() == ["nike-abc123", "sprite-xyz789"]
    assert set(frame["split"]) == {"train", "validation"}


def test_write_download_outputs_creates_ads_and_source_catalog(tmp_path: Path):
    project_root = tmp_path / "workspace_local"
    source_file = tmp_path / "abc123.mp4"
    source_file.write_bytes(b"video")
    downloads = [
        DownloadedVideo(
            brand="Nike",
            url="https://www.youtube.com/watch?v=abc123",
            video_id="abc123",
            title="Title A",
            channel="Channel A",
            duration_sec=15.0,
            source_path=source_file,
            language="en",
        )
    ]

    ads_csv, catalog_csv = write_download_outputs(project_root=project_root, downloads=downloads)

    assert ads_csv.exists()
    assert catalog_csv.exists()
    assert (project_root / "project.json").exists()
