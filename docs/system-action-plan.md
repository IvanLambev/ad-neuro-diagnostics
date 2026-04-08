# Ad Neuro-Diagnostics System Action Plan

## Current State

- [x] Remote VM test suite passed on 2026-04-08 using `~/tribev2/.venv/bin/python -m pytest -q`
- [x] VM baseline result: `10 passed in 8.13s`
- [x] Remote project snapshot has been copied locally
- [x] We have `33` ingested ads in `workspace_local`
- [x] We have `12` ads with completed TRIBE raw outputs and extracted features in `workspace_small`
- [x] We now have human ratings for those `12` processed ads
- [x] We are **not** retraining TRIBE v2
- [x] We are training a downstream model on top of TRIBE-derived features plus media features
- [x] Single-ad reports can now include historical benchmarking, similar ads, and likely driver summaries in the local repo
- [x] Baseline training has been run on the rated `12`-ad set
- [ ] Local repo test suite is not yet fully runnable in the current Windows Python because `mne` is missing locally

## What We Are Training

We are training a small supervised model on top of the cached TRIBE outputs and derived features.

Input features currently include:

- [x] TRIBE temporal activation summaries
- [x] strongest timestep and activation peak statistics
- [x] ROI summaries
- [x] brightness, motion, cut-rate, loudness, and transcript-density features

Current supervised targets are:

- [x] engagement
- [x] clarity
- [x] emotional_intensity
- [x] confusion
- [x] memorability

Current baseline models are:

- [x] Ridge regression
- [x] Random forest regression

## Baseline Readout On The 12 Rated Ads

This is an early validation run, not a production-quality model benchmark.

- [x] `confusion` shows real early signal
  - Ridge: `MAE 0.237`, `R2 0.773`
  - Random forest: `MAE 0.310`, `R2 0.626`
- [x] `engagement` is not yet reliable
  - Best current MAE: `0.967`
  - R2 is still negative
- [x] `memorability` is not yet reliable
  - Best current MAE: `1.088`
  - R2 is still negative
- [x] The current result supports the idea that the pipeline can learn something useful
- [ ] The current result does **not** yet support strong predictive claims for engagement or memorability

## What Is Already Ready

### Ingest And Processing

- [x] register ads
- [x] normalize videos into analysis clips
- [x] cache TRIBE raw outputs
- [x] track artifact status
- [x] extract derived feature tables
- [x] generate brain-frame images and GIFs
- [x] generate per-ad feature summaries

### Reference Dataset

- [x] 12 processed reference ads
- [x] 12 rated reference ads
- [x] historical feature table in `workspace_small/manifests/ad_features.csv`
- [x] human labels in `workspace_small/manifests/ratings.csv`

### Reporting

- [x] single-ad report
- [x] ad-vs-ad compare report
- [x] annotation summaries
- [x] similar-ad lookup in local repo
- [x] historical benchmark text in local repo
- [x] likely-driver summary in local repo

### Training

- [x] end-to-end baseline training command exists
- [x] grouped train/test split by campaign exists
- [x] predictions and metrics are written to disk

## What Is Not Ready Yet

- [ ] one-command customer pipeline for "new ad in, full customer report out"
- [ ] persistent reference benchmark artifacts for every new scored ad
- [ ] explicit ranking model for "this ad did better than similar ads"
- [ ] stable confidence/uncertainty estimates
- [ ] retrieval of the most similar historical ads with reusable summary assets
- [ ] stronger labels for real business outcomes
- [ ] validation on more than `12` rated ads
- [ ] local environment parity with the VM
- [ ] productized export format for customer delivery

## Full System Goal

Target user flow:

1. User gives us a new ad.
2. We register and normalize it.
3. We run it through TRIBE.
4. We extract temporal, ROI, video, audio, and transcript features.
5. We compare it against the rated historical library.
6. We estimate likely engagement, confusion, and memorability behavior.
7. We show which parts of the ad likely drive those outcomes.
8. We tell the customer which historical ads it most resembles and whether it looks stronger or weaker than them.

## Action Plan

### Phase 1: Lock The 12-Ad Validation Slice

- [x] Use only the `12` already processed TRIBE ads for the first validation cycle
- [x] Import ratings into the active `workspace_small` manifest
- [x] Run baseline training on the rated `12`
- [x] Generate benchmark-style single-ad reports for the rated `12`
- [ ] Review every generated report manually and sanity-check the wording
- [ ] Pick 3 to 5 example ads and turn them into customer-facing report examples

### Phase 2: Turn The Current Logic Into A Product Story

- [ ] Create a single "score new ad" workflow that:
  - registers the ad
  - normalizes it
  - runs TRIBE
  - extracts features
  - benchmarks it against the rated library
  - writes a customer-ready report bundle
- [ ] Add a summary section that says:
  - what this ad is most similar to
  - whether it is stronger or weaker than those similar ads
  - which moments likely drive engagement
  - which moments likely drive confusion
  - which moments likely drive memorability
- [ ] Add a concise customer conclusion with "keep / test / rethink" style recommendations

### Phase 3: Make The Model More Useful Without Retraining TRIBE

- [ ] Train dedicated models for:
  - engagement
  - confusion
  - memorability
- [ ] Add pairwise ranking features so we can say "better than this prior ad"
- [ ] Use full ROI timecourses, not only summary aggregates
- [ ] Add segment-level scoring so we can identify strong and weak moments over time
- [ ] Add transcript semantics and CTA detection from `events.csv`
- [ ] Add nearest-neighbor retrieval as a first-class output, not just a report side table

### Phase 4: Improve Trust

- [ ] Add confidence scores to every prediction
- [ ] Add leave-one-campaign-out evaluation as a standard benchmark
- [ ] Store benchmark snapshots so scoring is reproducible
- [ ] Track model versions separately from TRIBE cache versions
- [ ] Add explicit warnings when the reference set is too small for a strong claim

### Phase 5: Expand The Dataset Carefully

- [ ] Process the remaining `21` ingested ads through TRIBE
- [ ] Rate those additional ads
- [ ] Re-run feature extraction and supervised training
- [ ] Check whether engagement and memorability become learnable with more labeled examples
- [ ] Only then decide whether the system is ready for broader customer use

## Immediate Next Steps

- [ ] Validate the newly generated benchmark reports by hand
- [ ] Add a dedicated CLI command for customer scoring
- [ ] Add pairwise "better than similar ads" logic to the training/evaluation layer
- [ ] Process and rate more ads after the `12`-ad validation readout is reviewed

## Files To Treat As The Current Working Assets

- `remote_snapshot/instance-20260331-200137/workspace_small/manifests/ad_features.csv`
- `remote_snapshot/instance-20260331-200137/workspace_small/manifests/ratings.csv`
- `remote_snapshot/instance-20260331-200137/workspace_small/experiments/baseline_metrics.csv`
- `remote_snapshot/instance-20260331-200137/workspace_small/artifacts/<ad_id>/reports/single_report.md`

## Decision

- [x] Keep TRIBE v2 frozen as the backbone
- [x] Build our own retrieval, benchmarking, and supervised scoring layer on top
- [x] Validate first on the `12` processed and rated ads
- [ ] Scale to the remaining ads only after the first report and benchmark review is complete
