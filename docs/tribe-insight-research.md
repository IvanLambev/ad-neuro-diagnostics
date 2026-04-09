# TRIBE Insight Research

## Why this matters

TRIBE is already giving us much richer information than we currently expose. The best next step is not to make bigger claims about "this brain region means someone will buy." The best next step is to convert TRIBE's temporal and regional signals into stronger, more explainable proxies that help customers make creative decisions.

## What research suggests

### 1. Brain data can add forecasting value beyond self-report

Research in advertising and neuroforecasting suggests neural measures can improve forecasts of market-level outcomes beyond traditional copy testing alone.

- Venkatraman et al. found fMRI measures explained the most incremental variance beyond traditional measures in predicting advertising elasticities, with ventral striatum activity standing out as a strong predictor of real-world response.
- Knutson and Genevsky's neuroforecasting review argues that not every neural process generalizes equally well, and that some affective components can forecast aggregate demand better than self-report.
- A 2025 PNAS Nexus paper reports that neural activity tied to early affective responses remained predictive of aggregate demand even when behavior-based forecasts were less stable.

## What that means for us

We should treat TRIBE as a forecasting signal layer that augments surveys and historical benchmarks, not as a magical truth oracle.

### 2. Different ad goals may depend on different neural patterns

Research suggests different kinds of messages may rely on different neural systems.

- Informational or persuasive content can engage more medial prefrontal and related integration/mentalizing systems.
- Affective and reward-like signals may be more useful for broadly forecasting appeal and demand.
- Trust and perceived risk cues appear to recruit distinct neural processes and can influence willingness to pay and purchase intention in commerce settings.

## What that means for us

We should stop thinking in terms of one generic score and start thinking in terms of distinct creative questions:

- Does the ad create early approach or positive pull?
- Does the ad stay cognitively clear enough to follow?
- Does the brand handoff land as meaningful rather than just visible?
- Does the ending reinforce value, trust, or memory?

## High-value product ideas from TRIBE

These are product ideas inferred from the literature plus the data we already generate.

### A. Early Hook Score

Research signal:
- The neuroforecasting literature highlights early affective responses as especially generalizable.

Build:
- Measure first-2-second and first-20-percent activation behavior.
- Report time-to-first-peak, opening slope, and opening-vs-middle drop.
- Benchmark against historical winners and losers.

Customer value:
- "Your hook lands late."
- "This ad earns attention early but gives it back too quickly."

### B. Value / Reward Proxy

Research signal:
- Reward-related activity has been linked in prior work to market-level outcomes and aggregate choice forecasting.

Build:
- Use TRIBE temporal patterns plus ROI trajectories to estimate a value-lift proxy, especially around product reveal, offer reveal, and closing brand moments.
- Compare late-stage value-lift against similar ads.

Customer value:
- "The offer is visible, but the value signal does not strengthen when the product appears."

Important note:
- This is an inference from the cited neuroforecasting and advertising work, not a direct claim that our current TRIBE output equals ventral striatum measurement.

### C. Clarity / Cognitive Friction Track

Research signal:
- Informational strength and persuasive quality can recruit integration-related regions and predict downstream behavior in some message types.

Build:
- Detect drops in stability, inconsistent ROI coordination, and weak recovery after cuts or transcript density spikes.
- Label these as clarity dips, overload windows, or weak transitions.

Customer value:
- "The offer explanation arrives during a response drop and may be harder to process."

### D. Trust / Risk Proxy

Research signal:
- Neuroimaging work on online trust signals suggests neural responses to trust/risk cues relate to trust, risk, purchase intention, and willingness to pay.

Build:
- Create a trust/risk layer for end cards, seals, offer frames, pricing moments, CTA wording, and brand-safe visuals.
- Compare how trust/risk proxy changes before and after the CTA.

Customer value:
- "The ad gets attention, but the closing screen may not reduce enough decision friction."

### E. Shareability / Social Transmission Proxy

Research signal:
- Work on viral marketing success suggests social-related neural measures can help forecast sharing outcomes.

Build:
- Detect moments with unusually strong socially relevant or emotionally transmissible response signatures.
- Score whether an ad has one or more "shareable spikes."

Customer value:
- "This ad has strong late energy, but lacks a clear socially shareable beat."

### F. Memory Consolidation Pattern

Research signal:
- The literature consistently treats memory as distinct from attention and immediate liking.

Build:
- Move beyond one memorability score and detect whether the ad ends with consolidation or fragmentation.
- Compare last-third response stability, recurrence of key motifs, and post-peak sustain.

Customer value:
- "The ending is noticeable, but the memory trace decays too fast after the peak."

### G. Segment Archetypes

Research signal:
- The literature points toward different useful components for different markets and message types.

Build:
- Cluster segments into archetypes such as hook, explanation, emotional lift, brand handoff, trust close, and fatigue window.
- Explain which archetypes helped or hurt compared with similar ads.

Customer value:
- "Your ad behaves like a strong explainer but a weak closer."

## Best immediate upgrades for this repo

### 1. Event-aligned moments

Tie TRIBE moments to:
- cuts
- transcript density
- silence windows
- logo appearance
- product reveal
- price / CTA frames

This would instantly make the report more useful than generic peaks.

### 2. Better comparative language

Instead of:
- "distance 7.78"

Say:
- "Similar to Sprite because both ads build late and use a high-energy close."
- "Unlike Pringles, your strongest response comes after the core product explanation."

### 3. Distinct tracks, not one summary

We should expose:
- hook quality
- clarity stability
- value lift
- trust close
- memory finish

These can sit under the current plain-English umbrella of attention, clarity, and memorability.

### 4. Confidence by track

Different tracks should have different confidence levels depending on neighbor quality, label coverage, and how far the ad sits from the reference set.

## Guardrails

- We should not claim we can directly read purchase intent from a specific brain region using the current product.
- We can credibly claim that TRIBE-derived response patterns may improve comparative forecasting and creative diagnosis when benchmarked against historical ads.
- We should frame outputs as likely response patterns and actionable creative hypotheses.

## Recommended backlog additions

- Add event-aligned moment generation
- Add hook score, clarity stability score, trust close score, and value-lift score
- Add shareability proxy research spike
- Add segment archetype clustering
- Add comparative language that names why an ad behaves like its nearest neighbors
- Add confidence per score instead of only one global confidence

## Sources

- [Venkatraman et al., *Predicting Advertising Success Beyond Traditional Measures*](https://assets.tina.io/a371bbc3-e9fe-472a-a32b-f55a8990b0bc/Venkatraman%20et%20al.%20Predicting%20Advertising%20Success%20Beyond%20Traditional%20Measures-%20New%20Insights%20from%20Neurophysiological%20Methods%20and%20Market%20Response%20Modeling.pdf)
- [Genevsky and Knutson, *Neuroforecasting Aggregate Choice*](https://journals.sagepub.com/doi/10.1177/0963721417737877)
- [Genevsky et al., *Neuroforecasting reveals generalizable components of choice*](https://academic.oup.com/pnasnexus/article-abstract/4/2/pgaf029/8016018)
- [Casado-Aranda et al., *Consumer Processing of Online Trust Signals: A Neuroimaging Study*](https://www.sciencedirect.com/science/article/pii/S1094996819300520)
- [Wang et al., *Content Matters: Neuroimaging Investigation of Brain and Behavioral Impact of Televised Anti-Tobacco Public Service Announcements*](https://pubmed.ncbi.nlm.nih.gov/23616548/)
- [Nature Reviews Neuroscience summary, *Evaluating ads with fMRI*](https://www.nature.com/articles/nrn3521)
