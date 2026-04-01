# Ad Neuro-Diagnostics

Research-first CLI for evaluating short video ads with cached TRIBE outputs.

## What it does

- registers ad assets and metadata
- normalizes source videos into analysis clips
- runs or validates cached TRIBE inference artifacts
- extracts temporal and ROI features from `preds.npy`
- generates single-ad and compare-two-ad reports
- trains simple baseline models against human ratings

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
ads ingest init --project-root ./workspace
```

## Project structure

- `manifests/ads.csv`: canonical creative metadata
- `manifests/clips.csv`: normalized media assets
- `manifests/ratings.csv`: human annotation table
- `manifests/artifact_manifest.csv`: per-stage artifact status
- `artifacts/<ad_id>/raw`: TRIBE outputs such as `preds.npy` and `events.csv`
- `artifacts/<ad_id>/features`: derived feature tables and plots
- `artifacts/<ad_id>/reports`: single-ad and compare outputs

## Notes

- This repo treats TRIBE inference as an offline stage.
- Downstream analytics operate on cached artifacts by default.
- Predictions are average-subject fMRI-like responses, not measures of liking or conversion.

