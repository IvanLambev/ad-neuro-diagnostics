# Data Preparation Guide

## What to collect

Prioritize short video ads with audio:
- 6s, 15s, 30s, and 45-60s lengths
- multiple industries and creative styles
- multiple variants from the same campaign when possible

Avoid for v1:
- static image ads
- long-form videos
- interactive site recordings
- files with broken audio unless silent creative is intentional

## File preparation

Keep the original asset untouched.

For each ad:
- assign a stable `ad_id`
- record `brand`, `campaign`, and `variant`
- record `language`
- assign split by campaign or brand, not by single ad variant

Use the CLI normalization stage to create the analysis copy:
- MP4
- H.264 video
- AAC audio
- 1280x720
- 30 fps

## Annotation rubric

Each ad should be rated by at least 3 annotators on a 1-5 scale:
- engagement
- clarity
- emotional intensity
- confusion
- memorability

Also collect short free-text notes.

## First batch recommendations

Aim for 80-120 ads minimum for a prototype, and 200-300 for a more useful first dataset.

Make sure the first batch spans:
- low/high pacing
- low/high narration density
- low/high text overlay density
- low/high emotional tone
- clear vs ambiguous product message
- weak vs strong first-3-second hooks

## Example workflow

```bash
ads ingest init --project-root ./workspace
ads ingest register --project-root ./workspace --input-csv ./examples/ads_template.csv
ads ingest normalize --project-root ./workspace
ads annotate export --project-root ./workspace --annotators 3
ads run-tribe --project-root ./workspace --tribe-repo ../tribev2
ads extract-features --project-root ./workspace --top-k 10 --fps 1
ads report single --project-root ./workspace --ad-id brandx-hook-a
ads train-baseline --project-root ./workspace
```
