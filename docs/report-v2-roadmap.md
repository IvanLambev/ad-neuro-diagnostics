# Report V2 Roadmap

## Goal

Turn the current report from a compact benchmark summary into a richer creative-diagnostics product that makes better use of TRIBE outputs and presents them in a way non-technical ad makers can understand.

## Core Product Direction

- [x] Keep TRIBE frozen as the backbone
- [x] Keep the customer-facing language centered on attention, clarity, and memorability
- [x] Add synchronized ad-and-brain playback to the report
- [x] Add chapter-style timeline markers, similar to YouTube timestamps
- [ ] Improve moment quality so they reflect meaningful segments, not just generic peaks
- [ ] Improve explanations so they tie comparisons to actual ad structure
- [x] Add confidence and percentile framing to reduce false certainty

## Backend Upgrades

### Report quality

- [x] Add percentile scores for each target
- [x] Add confidence bands for each target
- [x] Add richer similar-ad explanations beyond generic distance language
- [x] Add peer-relative comparisons for each target
- [ ] Add narrative summary lines that turn raw metrics into creative guidance

### Timeline and moments

- [x] Promote time as a first-class signal instead of only using summary rows
- [x] Build chapter-style timeline entries with labels, timestamps, and rationale
- [ ] Add stronger and weaker moment segmentation over meaningful windows
- [x] Include frame index and time range for each moment
- [x] Attach target-specific impact labels to each moment

### TRIBE utilization

- [ ] Use ROI timecourses more directly in report generation
- [ ] Surface top ROI behavior over time instead of only strongest timestep
- [x] Add playback metadata that maps video time to TRIBE frame index
- [x] Expose brain frame assets for synchronized playback in the frontend
- [x] Add top ROI plot asset URLs and activation curve asset URLs in the report JSON

### Event alignment

- [ ] Align activation changes with transcript density and media events
- [x] Add better story labels such as hook, clarity dip, memorability lift, and brand handoff
- [ ] Connect pacing, cuts, and speech density to moment explanations

## Frontend Upgrades

### Report experience

- [x] Add split layout: ad on the left, brain activation on the right
- [x] Sync the right-side brain frame to the video current time
- [x] Add chapter chips / timeline jumps for key moments
- [x] Let the user click a moment to seek the video and the brain frame together
- [x] Show stronger score cards with score, percentile, and confidence

### Visual assets

- [x] Show strongest frame and top ROI plot without burying them
- [x] Keep the technical appendix available but secondary
- [x] Show clearer historical comparisons and why each peer is similar

## Research Questions

- [ ] Which additional signals from TRIBE outputs are most predictive at the segment level?
- [ ] Which event-alignment heuristics best explain clarity drops or memorability lifts?
- [ ] How much better do reports become when we use ROI timecourses directly?
- [ ] What level of confidence language feels honest and useful to customers?

## Current Implementation Focus

- [x] Add richer report JSON schema
- [x] Add playback metadata and frame serving
- [x] Add synchronized report UI
- [x] Add chapter-style moments
- [x] Add percentile and confidence summaries

## Notes

- The product should guide creative decisions, not imply hard purchase prediction.
- We should keep saying "likely to help / likely to hurt / similar to past ads" rather than making causal claims we have not validated.
- The strongest next unlock after this pass is better event alignment and stronger segment logic.
