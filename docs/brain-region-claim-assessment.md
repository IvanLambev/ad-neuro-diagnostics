# Brain Region Claim Assessment

This note maps common neuromarketing claims to what we can support with the current TRIBE-based product, what we can support only as careful proxies, and what we should not claim yet.

## Bottom Line

- We can support stronger time-based creative diagnostics now.
- We can support some cortical region-inspired proxy tracks with careful language.
- We cannot honestly claim literal amygdala, ventral striatum, or hippocampus activation with the current harness.
- We should not market direct purchase prediction from single-ad TRIBE output alone.

## Why This Matters

Our current brain mapping layer operates on a cortical `fsaverage5` surface and summarizes those predictions into HCP cortical ROIs, not subcortical structures. See [brain.py](C:/Users/ivan2/Documents/GitHub/ad-neuro-diagnostics/ad_neuro_diagnostics/brain.py#L15) and [brain.py](C:/Users/ivan2/Documents/GitHub/ad-neuro-diagnostics/ad_neuro_diagnostics/brain.py#L47). The feature pipeline then writes cortical ROI timecourses and cortical brain-frame assets from those predictions. See [features.py](C:/Users/ivan2/Documents/GitHub/ad-neuro-diagnostics/ad_neuro_diagnostics/features.py#L364).

## Claim-by-Claim

### 1. Positive vs. Negative Emotional Engagement

What people often say:
- vmPFC means positive connection or personal relevance
- amygdala means fear, stress, or aversion

What we can do:
- We can build an experimental `positive connection` cortical proxy if we explicitly treat it as a vmPFC-like valuation/approach-style signal, not as a literal emotion detector.
- We can build an experimental `skepticism / threat attention` proxy using cortical signals plus pacing/text/event cues.

What we cannot do yet:
- We cannot honestly say "the amygdala lit up" with the current surface-only harness.

Recommended product language:
- "The ad shows a stronger positive-valuation style pattern in the current reference set."
- "The ad may trigger more caution or resistance in this section."

Avoid:
- "The viewer felt joy."
- "The amygdala lit up."

### 2. Reward / Purchase Desire

What people often say:
- ventral striatum activity predicts wanting and can forecast purchase behavior

What we can do:
- We can build a `reward anticipation` or `subjective value lift` proxy track from cortical patterns, timing, and peer-relative comparisons.
- We can align that to product reveal, offer reveal, and CTA windows.

What we cannot do yet:
- We cannot honestly claim literal ventral striatum activation from the current cortical harness.
- We should not claim direct purchase prediction without our own outcome validation.

Recommended product language:
- "The product reveal appears to generate stronger reward-style lift than similar ads."
- "This section looks more desire-building than the current benchmark set."

Avoid:
- "This predicts purchase."
- "The reward center lit up."

### 3. Memory Encoding / Brand Recall

What people often say:
- hippocampus activation means long-term memory encoding

What we can do:
- We already support memorability benchmarking and can strengthen it with better end-weighting, brand-handoff timing, repetition, and late-stage stabilization.
- We can add a `brand memory lift` or `encoding-friendly close` track.

What we cannot do yet:
- We cannot honestly say "the hippocampus lit up" with the current harness.

Recommended product language:
- "This ending looks more likely to leave a memory trace than similar ads."
- "The brand handoff lands in a stronger memory window than the library average."

Avoid:
- "The hippocampus is encoding this."

### 4. Pricing Friction / Pain of Paying

What people often say:
- insula activation means price pain, disgust, or friction

What we can do:
- We can build an experimental `price friction` or `offer friction` proxy if the ad contains a price or value proposition, using:
  - cortical insula-like / salience-style signals where available
  - text overlay detection
  - OCR on pricing frames
  - pacing + speech density + CTA timing
- This is especially useful around price reveal moments.

What we cannot do yet:
- We should not claim literal "pain" or literal insula-driven disgust without stronger validation.

Recommended product language:
- "The price reveal may introduce friction here."
- "The offer section looks harder to accept than the rest of the ad."

Avoid:
- "The price caused neural pain."

### 5. Deception Detection / Trust Alarm

What people often say:
- precuneus and amygdala detect deceptive advertising

What we can do:
- We can build a `trust risk` or `claim skepticism` exploratory track now.
- This is a strong fit for our current report system because it can combine:
  - cortical patterns
  - text-heavy frames
  - claim-like language in transcript
  - CTA timing
  - abrupt pacing changes

What we cannot do yet:
- We cannot present this as a lie detector.

Recommended product language:
- "This claim sequence may trigger more scrutiny than similar ads."
- "The ad may ask for trust faster than it earns it."

Avoid:
- "The brain detected deception."

### 6. Second-by-Second Optimization

What people often say:
- fMRI allows second-by-second commercial optimization

What we can do:
- This is the strongest direct product fit right now.
- We already have:
  - timeline moments
  - event alignment
  - side-by-side ad + brain playback
  - product/logo/text/CTA visual heuristics
- We should keep pushing here.

Recommended product language:
- "At 0:06 the hook strengthens."
- "At 0:18 the message becomes harder to track."
- "At 0:24 the CTA lands in a stronger response window."

### 7. Eye Tracking

What people often say:
- fMRI is often paired with eye tracking to know what the viewer was looking at

What we can do now:
- approximate on-screen attention targets with:
  - OCR
  - logo detection
  - product detection
  - saliency / gaze prediction models

What would be stronger:
- true eye-tracking collection in research studies
- webcam or lab-based gaze data for validation

Recommended product language:
- "The response spike overlaps with the product frame."
- "The text-heavy frame is likely competing for attention."

Avoid:
- "The viewer looked exactly here" unless we have actual gaze data.

## Implementation Decision

### Safe to implement now

- Stronger second-by-second report logic
- Product reveal lift
- Brand handoff strength
- CTA close quality
- Trust / skepticism proxy
- Offer / price friction proxy
- Better visual event detection
- Saliency-style element attribution

### Implement only as experimental proxies

- Positive emotional connection
- Reward anticipation
- Memory encoding
- Trust alarm

### Do not claim yet

- literal amygdala activation
- literal ventral striatum activation
- literal hippocampus activation
- direct purchase prediction from one ad alone
- deception detection as a factual classifier

## Research Notes

- Reverse inference is a major risk in this space. A region being associated with a process in prior work does not mean every activation instance means that process in our product context.
- The product is strongest when it translates neuroscience into creative guidance rather than making medical-style brain claims.

## Sources

- [Tuned In: The Brain’s Response to Ad Sequencing](https://www.oversight.gov/sites/default/files/documents/reports/2017-09/RARC-WP-17-004.pdf)
- [Neural predictors of purchases](https://pmc.ncbi.nlm.nih.gov/articles/PMC1876732/)
- [Suspicious Minds: Exploring Neural Processes during Exposure to Deceptive Advertising](https://journals.sagepub.com/doi/10.1509/jmr.09.0007)
- [NC State summary of deceptive advertising study](https://news.ncsu.edu/2012/02/wmswooddeceptive/)
- [Effect of Brand Knowledge on Beverages](https://mcclurelab.org/pdf/McClureLi2004.pdf)
- [Neuroforecasting Aggregate Choice](https://pubmed.ncbi.nlm.nih.gov/29706726/)
- [Neuroimaging Techniques in Advertising Research](https://www.mdpi.com/2071-1050/13/11/6488)
