# Report V2 TODO

This file keeps the higher-value product ideas in one place so we do not lose them when implementation threads branch off.

## In Progress

- [x] Add a synced report schema with percentile, confidence, richer moments, and playback metadata
- [x] Expose source video, brain frames, activation curve images, and ROI plots through backend asset routes
- [x] Add a split report view with ad playback on the left and predicted brain response on the right
- [x] Add chapter-style timestamp jumps so users can move through moments like YouTube chapters
- [x] Add first-pass event alignment for transcript density, brand cues, CTA timing, and scene-change bursts
- [x] Add first-pass visual event detection for text-heavy frames, product-focus frames, logo-like marks, and end cards

## Next Backend Upgrades

- [ ] Move from simple peak-picking to segmented moments over more meaningful time windows
- [ ] Improve event alignment from first-pass heuristics into more stable segment-level alignment
- [ ] Use ROI timecourses directly in the explanation layer instead of relying mostly on compressed summaries
- [ ] Add target-specific confidence so attention, clarity, and memorability can differ in certainty
- [ ] Add peer-relative narrative lines such as "stronger opening hook than similar ads"
- [ ] Add calibration and uncertainty language when a new ad is far from the rated library
- [ ] Add hook score, clarity stability score, value-lift score, and trust-close score
- [ ] Add segment archetypes such as hook, explainer, emotional lift, brand handoff, and fatigue window
- [ ] Add shareability / social transmission proxy research track
- [ ] Improve visual event detection from first-pass heuristics into stronger logo, product, and end-card detection

## Next Frontend Upgrades

- [ ] Turn the chapter list into a visual timeline rail with stronger hover and active states
- [ ] Show per-moment overlays on the video player and brain panel during playback
- [ ] Add side-by-side comparison mode against a selected historical ad
- [ ] Add a cleaner "what changed" comparison summary when a new ad outperforms or underperforms peers
- [ ] Improve mobile handling for the synced video and brain layout

## Research Directions

- [ ] Investigate which TRIBE-derived segment signals best predict clarity drops
- [ ] Investigate whether certain repeated ROI patterns line up with stronger memorability
- [ ] Test whether event-aligned summaries are more useful to ad makers than generic moment labels
- [ ] Explore whether proxy purchase-intent style signals can be described safely without overclaiming
- [ ] Validate whether early-hook patterns are the most stable forecasting signal in our own ad library
- [ ] Validate whether trust/risk proxy signals improve CTA-end diagnostics
- [ ] Validate whether value-lift patterns around product reveal improve comparative reporting

## Product Guardrails

- [ ] Keep the language focused on likely response patterns, not causal claims about buying behavior
- [ ] Keep technical brain language secondary to plain-English creative guidance
- [ ] Use the historical library as context and comparison, not as a false ground truth
