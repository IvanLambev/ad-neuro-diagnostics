from __future__ import annotations

ADS_COLUMNS = [
    "ad_id",
    "source_path",
    "brand",
    "campaign",
    "variant",
    "duration_sec",
    "language",
    "split",
]

CLIPS_COLUMNS = [
    "ad_id",
    "clip_path",
    "fps",
    "width",
    "height",
    "audio_hz",
    "normalized_ok",
]

RATINGS_COLUMNS = [
    "ad_id",
    "annotator_id",
    "engagement",
    "clarity",
    "emotional_intensity",
    "confusion",
    "memorability",
    "notes",
]

ARTIFACT_COLUMNS = [
    "ad_id",
    "stage",
    "status",
    "cache_key",
    "updated_at",
    "error",
]

SUMMARY_TARGETS = [
    "engagement",
    "clarity",
    "emotional_intensity",
    "confusion",
    "memorability",
]

SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

DEFAULT_TRIBE_CONFIG_VERSION = "tribe_v1"

