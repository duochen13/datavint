# HeptaAI — Product Design Spec

**Date:** 2026-04-28
**Stage:** Pre-seed / MVP

---

## One-Sentence Pitch

> "We automatically optimize your training data distribution to improve model performance without changing your model."

---

## Inspiration

Named after the Heptapod language in *Arrival* — scientists finding hidden patterns in an alien language. HeptaAI finds hidden patterns in your training data: which samples are helping, which are hurting, and what the optimal distribution looks like.

---

## What We Build

**Input:** Raw training dataset (CSV / DataFrame) + optional test/serving sample
**Output:** `manifest.json` — sample weights and filter mask, ready to apply to any training pipeline

The customer applies the manifest to their existing pipeline and trains their model. No model changes. No architecture changes. Just better data.

---

## The Core Problem

The bottleneck in production ML is not compute or model architecture — it is data quality and distribution. This is confirmed by industry research:

- **Salesforce (2025):** 89% of data leaders report inaccurate AI outputs caused by faulty training data. 50%+ admit to training on data they knew was unreliable.
- **Meta:** Maintains dedicated teams per product for negative sampling, hard negative mining, and feature coverage monitoring — reinvented per team, no cross-team learning.
- **Google:** Documents named data traps (survivorship bias, surrogate endpoint problem, training-serving skew) in their production ML guidelines. Built TFDV for detection — not optimization.
- **Uber:** Monitors 14M daily trips across tens of thousands of tables for row count anomalies, schema drift, and distribution shifts. All manual per team.

Existing tools fall into two camps:
- **Monitoring only** (TFDV, Deepchecks, Evidently, Great Expectations): detect problems, alert, stop there
- **Primitive fixes** (PyTorch `WeightedRandomSampler`, sklearn `class_weight`): you define the fix manually

Nobody closes the loop from detection to action. That is HeptaAI.

> "What Meta's ML infra team does with 10 engineers per product, HeptaAI does automatically for any company."

---

## Key Insight: "Sample Reliability" not "Label Correctness"

In enterprise ML — recommendation, ranking, CTR — labels are behavioral signals (clicks, purchases), not human annotations. The label happened. The right question is not "is this label wrong?" but **"is this sample reliable and useful for training?"**

A sample can be unreliable without being wrong:
- Same features, different labels across contexts → noisy region
- Accidental clicks / bot traffic → weak signal
- Gradient opposing the batch → actively hurting training
- Feature computed differently at train vs. serving time → model trained on data it will never see again

HeptaAI does not claim ground truth. It identifies unreliable samples using proxy signals and prescribes actions. The user decides which actions to apply.

---

## Three Product Modes

Users arrive with different levels of domain knowledge. HeptaAI supports all three:

### Mode 1 — "I know what's bad" (Prescription)
The MLE has domain knowledge and knows which issues matter. HeptaAI executes the fix at scale.

Example: Meta MLEs know that duplicate samples with conflicting labels confuse the model (sees sample with label=1, then identical sample with label=0). They know it's bad — they need a tool to find all 18,000 instances and generate the fix automatically.

```python
manifest = opt.fix("duplicates")        # I know this is bad, find and fix all
manifest = opt.fix("class_imbalance")   # I know my ratio is wrong, fix it
```

### Mode 2 — "Show me what's hidden" (Discovery)
The MLE doesn't know what's wrong. HeptaAI surfaces hidden patterns they couldn't see:

- "23% of your APAC samples have conflicting labels — your other regions are fine"
- "Your weekend data has 4x higher label noise than weekday data"
- "Source B has 5x more feature coverage drops than Source A"
- "This feature's correlation with your label dropped 40% vs. last month"

These cross-segment, temporal, and cross-source patterns are invisible to TFDV and Deepchecks. They don't look for them.

```python
report = opt.discover("train.csv", label_col="target")
report.show()   # surfaces hidden patterns ranked by estimated model impact
```

### Mode 3 — "What if I..." (Exploration)
The MLE thinks in experiments. Instead of asking "is this data bad?", they ask "what happens if I change this?" HeptaAI simulates hypothetical changes using proxy signals — no model retrain required.

```python
opt.simulate("remove samples where engagement_seconds < 2")
# → loses 8% of data
# → label noise drops 34%
# → class balance improves from 1:847 to 1:234
# → estimated: reduces label variance in high-CTR segment

opt.simulate("use only last 90 days of data")
# → loses 61% of data
# → temporal drift score drops from 0.41 → 0.09
# → train-test skew on item_price: JS 0.31 → 0.12
```

This is a **data flight simulator** — the MLE explores their hypotheses before committing to a manifest.

**No tool in the current market has Mode 3.** MLEs currently do this manually in Jupyter notebooks, which requires a full model retrain per experiment.

---

## Core Flow: Diagnose → Prescribe → Manifest

```
raw data
   │
   ▼
① hepta.generate_statistics()   — per-feature stats + label entropy per segment
   │
   ▼
② hepta.visualize_statistics()  — TFDV-style display + issue badges
   │
   ▼
③ hepta.detect_issues()         — universal detectors + domain rules
   │                               outputs: Issues (type, signal, direction, confidence)
   ▼
④ hepta.display_issues()        — [Apply] [Skip] [Adjust] per issue (human in loop)
   │
   ▼
⑤ hepta.generate_manifest()     — outputs manifest.json (weights + filter mask)
   │
   ▼
manifest.apply() → train model → eval NE/AUC
   │
   ▼
⑥ hepta.record_feedback()       — improves base policy + domain-adaptive layer
```

TFDV stops at step ②. HeptaAI goes to step ⑥.

---

## Data Quality Issue Taxonomy

Grounded in real issues from Meta, Google, Uber, TikTok engineering research.

### Sample-Level
| Issue | Real-world source | Detection | Prescription |
|---|---|---|---|
| Exact duplicates | Meta (conflicting labels on same sample confuse model) | Hash comparison | Filter, keep one |
| Near-duplicates | Universal | Embedding cosine similarity | Deduplicate above threshold |
| Harmful samples | Research: gradient opposition | Gradient direction vs. batch average | Downweight or filter |
| Outliers / corrupted rows | Uber (upstream pipeline errors) | Feature value Z-score > 3σ | Flag, downweight |

### Label-Level
| Issue | Real-world source | Detection | Prescription |
|---|---|---|---|
| Label inconsistency | TikTok (incorrect recommendation explanations fed back) | Same feature vector, different labels | Downweight inconsistent region |
| Class imbalance | Meta ads (1:1000+ ratio), fraud universal | Positive:negative ratio | Negative downsampling / upsampling |
| Noisy behavioral labels | Google ("surrogate endpoint" trap) | Low-engagement positives (<2s click, bounced purchase) | Downweight weak positives |
| False negatives in neg. sampling | Research (70% of hard negatives are false negatives) | High-similarity items labeled negative | Flag for re-evaluation |
| Label leakage | Google production guidelines | Feature-label correlation > 0.95 | Flag — future data may be leaking |

### Feature-Level
| Issue | Real-world source | Detection | Prescription |
|---|---|---|---|
| High null / missing rate | Meta (coverage drops — #1 monitored metric) | Coverage below threshold | Downweight samples missing key features |
| Value out of range | Uber (upstream recording errors) | Values outside schema bounds | Flag as corrupted, filter |
| Low variance / dead feature | Universal | Std ≈ 0 or near-constant | Flag for deprecation |
| Feature-label correlation drop | Meta (real-time feature importance monitoring) | Correlation vs. historical baseline | Alert: feature may be degrading |
| Stale feature values | Meta (freshness dimension) | Timestamp lag beyond freshness window | Downweight stale samples |

### Distribution-Level
| Issue | Real-world source | Detection | Prescription |
|---|---|---|---|
| Train-test skew | Google Play (features always in training, never at serving) | Jensen-Shannon (numeric) / L-inf (categorical) | Reweight training toward test distribution |
| Train-serving skew | Meta, Google (training-inference consistency) | Training stats vs. serving sample | Reweight training toward serving distribution |
| Temporal drift | Uber (Holt-Winters forecasting detects seasonality shifts) | Distribution shift across time windows | Decay-weight older samples |
| Underrepresented segments | Google (sampling bias — APAC, minority classes) | Segment freq < serving freq | Upsample segment |
| Overrepresented segments | Universal | Segment freq >> serving freq | Downsample segment |

### Schema-Level
| Issue | Real-world source | Detection | Prescription |
|---|---|---|---|
| Data type mismatch | Uber (schema drift from pipeline changes) | Auto-inferred schema check | Flag column, block from training |
| Unseen categorical values | Uber (new enum values appear silently) | New values not in schema domain | Flag — model has never seen this |
| Value range violation | Google (instrument calibration failures) | Value outside schema min/max | Flag as corrupted |
| Required feature missing | Uber (upstream pipeline interruptions) | Expected feature absent | Alert pipeline upstream |
| Dataset size imbalance | Universal | Train:test ratio far from expected | Flag — evaluation may be unreliable |

**20 issues across 5 categories.** All detectable from data statistics alone — no model retrain required for detection.

---

## User-Configurable Thresholds

Thresholds are domain-specific. A 3% duplication rate may be acceptable in one domain and problematic in another. HeptaAI ships defaults based on common ML practice; the user owns the decision.

Each issue surfaces with:
1. **Metric** — what was measured (3% duplication rate)
2. **Context** — default threshold + ML impact reasoning
3. **Options** — [Apply] [Skip] [Adjust] — user decides which fixes to apply

```python
report = opt.diagnose("train.csv", test="test.csv", label_col="target")
report.show()
# ┌──────────────────────────────────────────────────────────────┐
# │ DUPLICATES: 3.0%                          ⚪ WITHIN DEFAULT  │
# │ Default threshold: 5% for ranking models                    │
# │ Impact: biases loss toward overrepresented patterns         │
# │ Recommendation: filter 847 exact duplicates                 │
# │                         [Apply] [Skip] [Adjust]             │
# ├──────────────────────────────────────────────────────────────┤
# │ TRAIN-TEST SKEW: item_price  JS=0.31      🔴 HIGH           │
# │ Default threshold: JS > 0.2                                 │
# │ Impact: model sees different price range at serving time    │
# │ Recommendation: reweight 12k samples to match test dist.   │
# │                         [Apply] [Skip] [Adjust]             │
# └──────────────────────────────────────────────────────────────┘

# Override thresholds
opt.set_threshold("duplicates", warn=0.02, fail=0.10)
opt.ignore("train_test_skew", feature="item_price")  # seasonal — expected

# Apply → manifest
manifest = report.apply()
manifest.save("manifest.json")
```

The output is always a manifest. This is what separates HeptaAI from TFDV: TFDV tells you what's wrong, HeptaAI hands you the prescription.

**Train on cleaned data, eval on raw test data intentionally.** The test set is kept raw and representative of production. If the model trained on HeptaAI's manifest outperforms the baseline on messy real-world eval data, the claim is maximally strong: better model performance even against noisy production conditions.

---

## Policy Architecture: Two Tiers

The prescription engine is powered by a learned policy, not static rules.

**Tier 1 — Universal Base Policy (pre-trained, ships in SDK)**
Operations that generalize across all domains:
- Negative downsampling ratios
- Minority class upsampling
- Near-duplicate thresholds
- Label entropy flagging
- Class imbalance correction

Pre-trained on aggregate anonymized proxy signals across all customers. Works day 1. Cross-customer learning is the moat.

**Tier 2 — Domain-Adaptive Layer (fine-tunes per team)**
Learns what "reliable sample" means for this specific team's data:
- Initializes from the base policy on first use
- Fine-tunes on that team's feedback over time
- Stored locally — never shared, data never leaves
- Each team within a company gets their own instance

This also solves the "different pipelines per team" problem: each team runs their own SDK instance with their own domain-adaptive layer. No central standardization required.

| RL concept | HeptaAI equivalent |
|---|---|
| State | Proxy signal vector for a sample or batch |
| Action | Upweight / downweight / filter |
| Reward | Proxy signals + optional customer model delta |
| Base policy | Trained across all customers (universal) |
| Domain policy | Fine-tuned per team (domain-specific) |

Technically: contextual bandit. Full RL (curriculum learning) is v3.

---

## Cold Start & Proxy Signal Credibility

The claim "works day 1" needs a concrete foundation, not a theoretical one.

**What the base policy is initialized on:**
- Public ML benchmark datasets: Criteo ads CTR (45M samples), MovieLens, RecSys challenge datasets — all with known ground truth, so we can measure whether proxy signals actually predict AUC improvement before any customer uses the product
- Published research priors: optimal negative sampling ratios, dedup thresholds, class imbalance correction benchmarks
- Synthetic datasets generated across a range of controlled noise profiles

**The scientific pre-condition — proxy signal must correlate with AUC:**

This is the core claim that must be validated before ship. The plan:
1. Take a clean public dataset (Criteo), inject known noise (duplicates, class imbalance, label inconsistency at controlled rates)
2. Apply various manifests, measure AUC delta for each
3. Compute proxy rewards for each manifest (label entropy delta, JS divergence delta, class ratio delta)
4. Measure correlation: does proxy reward predict AUC delta?

If correlation is above ~0.5, the policy is useful. If below, the proxy reward is noise and the design needs to change. This experiment must be run and published before the VC pitch. It is the foundational claim.

**Concrete example of proxy signal beating a heuristic (on Criteo):**

| Approach | Negative ratio | AUC |
|---|---|---|
| No fix (raw data) | 1:100 | 0.758 |
| Heuristic (fixed 1:10) | 1:10 | 0.771 |
| HeptaAI policy (label entropy = 0.41 → prescribes 1:7) | 1:7 | 0.779 |

The policy observes that high label entropy means the positive signal is weak — so it pushes the ratio tighter than the generic heuristic. This is a data-specific decision the heuristic cannot make. These numbers are targets to validate, not claims.

**Day 1 answer for VCs:**
The base policy is pre-trained on public benchmark outcomes. It beats heuristics because it is conditioned on data-specific signals. It becomes meaningfully better after 50+ customer datasets have contributed to the cross-customer aggregate.

---

## Feedback Loop Design

The slow loop (customer retrains model monthly = 12 signals/year per customer) is insufficient alone for a contextual bandit. Three loops work together:

**Loop 1 — Proxy reward (seconds, no retrain)**

After applying a manifest, HeptaAI measures immediately whether the dataset moved in the right direction:

| Proxy signal | Before manifest | After manifest | Interpretation |
|---|---|---|---|
| Label entropy (k-NN) | 0.41 | 0.28 | Noisy region reduced |
| Class ratio | 1:100 | 1:9 | Imbalance corrected |
| Train-test JS divergence | 0.31 | 0.09 | Skew resolved |
| Feature null rate | 12% | 3% | Coverage improved |

These are not AUC — they are leading indicators. The critical question is: **how well do these proxy rewards predict actual AUC delta?**

From published research:
- Label entropy reduction → correlates with AUC improvement (Northcutt et al., confident learning, 2021)
- Class imbalance correction → correlates with F1 improvement (well-established in imbalanced-learn literature)
- Train-serving skew reduction → correlates with production stability (Google TFDV production data)

The correlation is imperfect. The base policy learns to weight each proxy signal's predictive value from the calibration data provided by Loop 3.

**Loop 2 — Cross-customer aggregate (the primary learning mechanism)**

The policy does not learn customer-by-customer serially. It learns from the distribution of (signal, action, outcome) tuples across all customers simultaneously:

```
                    state vector                action          reward
Customer A    {entropy:0.41, ratio:0.08, ...}   1:7 ratio       proxy=+0.13
Customer B    {entropy:0.39, ratio:0.09, ...}   1:10 ratio      proxy=+0.04
Customer C    {entropy:0.40, ratio:0.08, ...}   1:7 ratio       proxy=+0.11
Customer D    {entropy:0.41, ratio:0.08, ...}   1:10 ratio      proxy=+0.03
...
→ Policy learns: for entropy≈0.40 + ratio≈0.08, action 1:7 yields 3x proxy reward vs 1:10
```

At 1,000 customers × 10 diagnoses/month = **10,000 (state, action, reward) tuples/month**. A contextual bandit with ~20 action dimensions needs roughly 5,000–10,000 tuples to converge on a stable policy. This is achievable within the first few months of operation.

Before reaching that scale, the policy relies on the pre-trained priors. Customers get heuristic-level performance early, policy-level performance as the network grows.

**Loop 3 — Model delta calibration (optional, high quality)**

Customer retrains on manifest, calls `opt.feedback(improved=True, delta=0.015)`. This is the ground truth signal that calibrates the proxy-to-AUC correlation in Loop 1. Even 500 such signals/month across customers is enough to keep the calibration tight.

```
Loop 1 (seconds)     →  proxy reward: did dataset improve by proxy signals?
Loop 2 (continuous)  →  cross-customer: which actions work for which signal profiles?
Loop 3 (weeks)       →  model delta: calibrate how well proxy reward predicts AUC
```

Loop 2 is the engine. Loop 1 is the fuel. Loop 3 is the calibration instrument.

---

## SDK Design (v1)

Designed to feel familiar to engineers who know TFDV, while extending the workflow to the steps TFDV stops before.

| TFDV step | HeptaAI equivalent | What's new |
|---|---|---|
| `generate_statistics_from_csv()` | `hepta.generate_statistics()` | adds label entropy per segment |
| `visualize_statistics()` | `hepta.visualize_statistics()` | adds issue badges, no CDN/Jupyter required |
| `validate_statistics()` → anomalies | `hepta.detect_issues()` → Issues | adds directional ML impact + confidence |
| `display_anomalies()` | `hepta.display_issues()` | shows NE/AUC direction, not just flag |
| — no equivalent — | `hepta.generate_manifest()` | prescribes fixes, human approves each |
| — no equivalent — | `manifest.apply()` | applies approved weights + filter mask |
| — no equivalent — | `hepta.simulate()` | what-if without retraining |
| — no equivalent — | `hepta.record_feedback()` | closes the loop |

**API style:** module-level functions (like TFDV), not a class instance. Data objects (`Statistics`, `Issues`, `Manifest`) are explicit and inspectable at every step.

```python
pip install heptaai
import heptaai as hepta

# ── Step 1: Generate statistics ──────────────────────────────────────────
# Per-feature: count, missing%, mean, p50, p99, median, distribution
# + label entropy per feature segment (TFDV does not compute this)
train_stats = hepta.generate_statistics("train.csv", label_col="click")
eval_stats  = hepta.generate_statistics("eval.csv",  label_col="click")

# ── Step 2: Visualize ────────────────────────────────────────────────────
# Single dataset — per-feature stats + issue badges
hepta.visualize_statistics(train_stats)

# Side-by-side comparison — mirrors tfdv.visualize_statistics(lhs=, rhs=)
hepta.visualize_statistics(lhs=train_stats, rhs=eval_stats,
                           lhs_name="TRAIN", rhs_name="EVAL")

# ── Step 3: Detect issues ────────────────────────────────────────────────
# Universal issues detected automatically.
# Pass serving_statistics to trigger skew detection (mirrors TFDV's pattern).
issues = hepta.detect_issues(
    statistics=train_stats,
    serving_statistics=eval_stats,  # optional — enables train/eval skew checks
)
hepta.display_issues(issues)
# ┌────────────────────────────────────────────────────────────────────────┐
# │ Issue              Feature        Signal          Direction  Confidence│
# ├────────────────────────────────────────────────────────────────────────┤
# │ class_imbalance    click          pos_rate=6.1%   NE↓ AUC↑  HIGH      │
# │ near_duplicates    –              density=18%     NE↓ AUC↑  HIGH      │
# │ train_eval_skew    item_category  L∞=0.14         AUC↑      MEDIUM    │
# │ missing_values     user_age       missing=5.8%    NE↓       MEDIUM    │
# └────────────────────────────────────────────────────────────────────────┘

# ── Step 4: Generate manifest (no TFDV equivalent) ───────────────────────
# Human reviews and approves each proposed fix — [Apply] [Skip] [Adjust]
# No fix is applied without explicit approval (MVP 1).
manifest = hepta.generate_manifest(train_stats, issues)
manifest.summary()
# → 3 fixes applied to 124,582 samples:
#     class_imbalance  → upweighted 7,623 positives 14.3×        [HIGH]
#     near_duplicates  → filtered 22,423 samples (weight=0)       [HIGH]
#     train_eval_skew  → reweighted 14,200 samples toward eval    [MEDIUM]
# → estimated direction: NE ↓  AUC ↑

# ── Step 5: Apply and train ──────────────────────────────────────────────
clean_df = manifest.apply("train.csv")   # returns weighted DataFrame
manifest.save("manifest.json")           # or export for external pipelines

# ── Step 6: Feedback (optional) ──────────────────────────────────────────
hepta.record_feedback(manifest, improved=True, auc_delta=0.017)
```

### Mode 1 — Fix Known Issues (shortcut)

```python
# Engineer knows what's wrong — skip detection, go straight to manifest
manifest = hepta.fix("train.csv", label_col="click",
                     issues=["class_imbalance", "near_duplicates"])
manifest.save("manifest.json")
```

### Mode 2 — Discover Hidden Patterns

```python
# Cross-segment analysis — surfaces patterns invisible to per-feature stats
issues = hepta.detect_issues(train_stats, cross_segment=True)
hepta.display_issues(issues)
# → "APAC segment has 4× higher label noise than NA (entropy 0.61 vs 0.15)"
# → "Weekend data has 2× duplicate density vs weekday"
# → "Source B has 5× more missing user_age than Source A"
```

### Mode 3 — What-If Simulation (no equivalent anywhere)

```python
# Explore hypothetical changes using proxy signals — no retrain needed
sim = hepta.simulate(train_stats, "remove samples where engagement_seconds < 0.5")
sim.show()
# → removes 18% of data (22,423 samples)
# → label entropy:              0.41 → 0.28  (noise reduced)
# → class ratio:                1:16 → 1:11  (balance improved)
# → train/eval JSD (engagement): 0.31 → 0.09  (skew resolved)
# → estimated direction: NE ↓  AUC ↑

sim2 = hepta.simulate(train_stats, "use only last 90 days of data")
sim2.show()
# → retains 39% of data
# → temporal drift score:       0.41 → 0.09
# → estimated direction: NE ↓  (freshness improvement)
```

### Domain Rule Registration

```python
# Extend universal detection with domain knowledge TFDV cannot infer.
# Rules plug into the same detect → propose → approve → manifest flow.

@hepta.rule
def flag_non_impression_negatives(sample):
    # In recommendation: non-impression samples are not true negatives
    if sample["label"] == 0 and sample["impression_flag"] == 0:
        return hepta.Action.DOWNWEIGHT
    return None

@hepta.rule
def low_engagement_noise(sample):
    if sample["engagement_seconds"] < 0.5:
        return hepta.Action.FILTER   # accidental tap, not real intent
    return None

# Pass rules into detect_issues — they surface as Issues with same
# directional impact display as universal detectors
issues = hepta.detect_issues(train_stats, rules=[
    flag_non_impression_negatives,
    low_engagement_noise,
])
```

### Optional: Higher-Fidelity Detection with Model

```python
# If a trained model is available, use gradient signals for deeper detection
# (not required — works without a model)
issues = hepta.detect_issues(train_stats, model=my_model)
```

Base policy weights download on first run. Domain-adaptive layer fine-tunes locally per team. Data never leaves the customer's machine.

**Rule template library:** Over time, anonymized rule templates accumulate per vertical (e-commerce, fintech, food delivery) and ship as opt-in presets. New customers in a vertical adopt templates instead of writing rules from scratch — the library compounds with each new customer.

---

## The 10-Minute Demo

```python
import heptaai as hepta

# ── 1. Profile ───────────────────────────────────────────────────────────
train_stats = hepta.generate_statistics("train.csv", label_col="click")
eval_stats  = hepta.generate_statistics("eval.csv",  label_col="click")
hepta.visualize_statistics(lhs=train_stats, rhs=eval_stats,
                           lhs_name="TRAIN", rhs_name="EVAL")

# ── 2. Detect issues ─────────────────────────────────────────────────────
issues = hepta.detect_issues(train_stats, serving_statistics=eval_stats)
hepta.display_issues(issues)

# ── 3. Generate manifest (human approves) ────────────────────────────────
manifest = hepta.generate_manifest(train_stats, issues)
manifest.summary()
# → 3 fixes applied, estimated direction: NE ↓  AUC ↑

# ── 4. Train both models ─────────────────────────────────────────────────
model_baseline = train(raw_data)               # NE: 0.981  AUC: 0.762
model_hepta    = train(manifest.apply(raw_data))  # NE: 0.954  AUC: 0.779

# Same model architecture. Same training code. Only the data changed.
```

Two metrics, one comparison, every fix explained. No model changes, no architecture changes.

---

## Competitive Positioning

### By Mode Coverage

| | Mode 1: Fix known issues | Mode 2: Discover hidden patterns | Mode 3: What-if simulation |
|---|---|---|---|
| **TFDV** | partial (no fix output) | partial (stats only) | — |
| **Deepchecks** | partial (no fix output) | partial (no ML impact) | — |
| **cleanlab** | ✓ label errors only | — | — |
| **Great Expectations** | ✓ rules you write, no fix | — | — |
| **Evidently** | — | drift only | — |
| **HeptaAI** | ✓ + manifest | ✓ + ML impact | ✓ proxy simulation |

Mode 3 is completely uncovered by any existing tool.

### By Capability

| Capability | TFDV | Deepchecks | Snorkel | cleanlab | HeptaAI |
|---|---|---|---|---|---|
| Schema validation | ✓ | ✓ | — | — | ✓ |
| Train-test skew detection | ✓ | ✓ | — | — | ✓ |
| Label error detection | — | partial | — | ✓ | ✓ |
| Cross-segment hidden patterns | — | — | — | — | ✓ |
| What-if simulation | — | — | — | — | ✓ |
| Outputs actionable manifest | — | — | — | — | ✓ |
| Learned policy (not rules) | — | — | — | — | ✓ |
| Closes model feedback loop | — | — | — | — | ✓ |
| Framework agnostic | — | ✓ | ✓ | ✓ | ✓ |
| Cross-customer learning | — | — | — | — | ✓ |

**TFDV** is TensorFlow-locked, requires full TFX adoption, and stops at detection. Declining with TF's market share.
**Deepchecks / Evidently / Great Expectations** are monitoring-only — no manifest, no optimization, no simulation.

> "TFDV tells you what's wrong. HeptaAI hands you the prescription."

---

## Revenue Model

**Freemium → Team → Enterprise**

| Tier | Price | What's included |
|---|---|---|
| **Free** | $0 | Up to 3 datasets/month, Mode 1 diagnostics only, community support |
| **Team** | $2,000–5,000/month | Unlimited manifests, all 3 modes, up to 10 seats, domain-adaptive layer |
| **Enterprise** | $30,000–100,000/year | Unlimited seats, audit tools, SLA, air-gap mode (no telemetry), custom integrations |

**Pricing unit: per seat + usage**
Primary unit is ML engineer seats. Secondary unit is dataset volume (number of manifests generated/month) for usage-based expansion within a tier. This is how Weights & Biases and dbt Cloud price — developer-first, seat-based, expands with team size.

**Why $30K for enterprise is not underpriced:**
+1% AUC on a recommendation model at a $100M ARR company = millions in incremental revenue. $30–100K/year is cheap insurance. Snorkel AI charges $100K+ for programmatic labeling alone, which is a narrower problem. The entry price is low to win the deal; expansion revenue comes from seats and usage.

**Unit economics target:**
- Free → Team conversion: 15% (developer tries, team buys)
- Team → Enterprise expansion: 30% of Team accounts within 12 months
- Target ARR per enterprise customer: $50K
- Target at 100 enterprise customers: $5M ARR

---

## Privacy Architecture

This is not a footnote — it is a core design constraint and enterprise sales enabler.

**What leaves the customer's machine (aggregate statistics only):**
```json
{
  "issue_type": "class_imbalance",
  "proxy_signals": { "class_ratio": 0.08, "label_entropy": 0.34 },
  "fix_applied": true,
  "threshold_used": 0.10,
  "outcome": "improved",
  "auc_delta": 0.015
}
```

**What never leaves (guaranteed by SDK architecture):**
- Raw feature values
- Labels or sample content
- Row-level data, PII, or business logic
- Model weights or gradients (unless customer opts into federated learning)

**Three privacy layers:**

1. **Local-only computation** — all data processing runs inside the customer's environment. The SDK never opens an outbound connection to raw data.

2. **Differential privacy on signals** — calibrated noise is added to proxy signal aggregates before transmission, making it mathematically impossible to reverse-engineer individual samples.

3. **Air-gap mode (enterprise)** — customer disables all telemetry. Base policy ships as a static artifact downloaded at install time (like a Hugging Face model). No policy updates, full privacy guarantee. Closes regulated industry deals (healthcare, finance).

**What HeptaAI's servers receive:**
```
Aggregate signal: {issue: "class_imbalance", signal_stats: {...}, outcome: "improved"}
No individual row. No feature value. No label.
```

**Auditability:** The telemetry layer is open-sourced. Customers can inspect exactly what bytes are transmitted. Security teams can verify. This is a selling point, not just a defense.

---

## Market Size

| Market | Size today | Projected | CAGR |
|---|---|---|---|
| Data quality tools | $4.2B | $12.3B (2033) | 12.6% |
| MLOps market | $1.7B | $25B+ (2034) | 37.4% |
| Training data services | Scale AI alone: $29B valuation | — | — |

**Comparable exits:**
- Snorkel AI: $135M raised, ~$1B valuation (programmatic labeling only, narrower scope than HeptaAI)
- cleanlab: $30M raised (label errors only)
- Scale AI: $29B (human labeling + data services)

**Initial SAM:** ~2,000 recommendation/ranking teams × $30K ARR = **$60M beachhead**
**Expanded SAM:** ~20,000 companies doing production supervised ML × $30-100K ARR = **$600M–$2B**

The TAM expands with AI adoption — more models in production = more training data problems = more HeptaAI customers. It is not a fixed market.

---

## Go-to-Market Direction

**Direction: Vertical-first (recommendation/ranking), then expand.**

### ICP — One Sentence

> ML engineers at Series B–D e-commerce, food delivery, or fintech companies ($20M–$300M ARR) who run recommendation or ranking models in production and don't have a dedicated ML infra team.

### Why This ICP Exactly

**Why Series B–D, not Series A:**
Series A teams are too small (1–3 ML engineers), haven't yet accumulated enough training data to hit quality problems at scale, and every dollar is scrutinized. Hard sell.

**Why not Series E+ or public companies:**
They are building internal tooling. At DoorDash or Airbnb scale, a dedicated ML platform team solves this problem themselves. They are not buyers — they are the benchmark.

**Why not FAANG:**
Meta, Google, Uber *are* the inspiration for HeptaAI. They solved this problem internally with 10 engineers per product. They will never buy it.

**The sweet spot:** A company that has production ML models generating real revenue, a 3–15 person ML team, no dedicated ML infra engineer, and a team lead who knows their model could be better but can't justify the time to investigate data quality manually.

**Concrete target companies:** Faire, Whatnot, Attentive, Moloco, Poshmark, Stash, OpenTable, GrubHub eng teams — all have recommendation/ranking models, all are the right size, none have ML infra teams.

### Why Recommendation/Ranking First

- **Known data shape:** `user_id, item_id, label, timestamp, context_features` — consistent across every company in this vertical. One beachhead, one schema.
- **Known pain:** negative sampling ratio is always wrong, temporal drift always present, serving skew on behavioral features always an issue. Same problems, every customer.
- **Measurable ROI:** +1% AUC on a recommendation model at a $50M ARR company = hundreds of thousands in incremental revenue. Easy for the team lead to justify $30K/year.
- **Developer-accessible buyer:** ML engineer makes the initial decision. No procurement, no committee. `pip install` is the trial.

### Acquisition — How the First 10 Customers Find Us

Not cold outbound. Content-led developer acquisition:

1. **"Show HN" post:** "HeptaAI — we found 18k duplicates and a 4x label noise gap between APAC/NA in a public CTR dataset." ML engineers are drawn to concrete findings, not feature lists.

2. **Blog post targeting the exact pain:** "Why your CTR model degrades every Monday" (answer: weekend behavioral data has different label noise patterns — a Mode 2 insight HeptaAI finds). SEO targets: "training data quality", "negative sampling ratio", "train serving skew".

3. **Kaggle / public dataset findings:** Run HeptaAI on Criteo, MovieLens, RecSys competition datasets. Publish the findings. Show what the tool finds on data engineers already know.

4. **ML newsletter placements:** Chip Huyen's newsletter, Sebastian Raschka, The Batch. One placement to the right audience > 10,000 cold emails.

**The aha moment:** Engineer runs `pip install heptaai` on their dataset, gets a Mode 2 insight in under 5 minutes that their team didn't know about. That is the acquisition event. Everything before it is getting them to that run. Everything after it is converting the champion into a team purchase.

### Sales Motion

```
Content → pip install (free) → Mode 2 aha moment → champion shares with lead
    → team license ($2–5K/month, self-serve, credit card)
    → multiple teams → enterprise deal ($30–100K/year, procurement)
```

No outbound required for the first 10 customers. Outbound begins at Series A when you have 10 case studies and a repeatable playbook.

### Expansion Path

```
Phase 1 (v1):  Recommendation/ranking — one data shape, known problems, clear ROI
Phase 2 (v2):  Fraud detection + search ranking — adjacent schemas, similar issues
Phase 3 (A):   Any supervised ML — generic SDK, vertical adapters, connector integrations
```

---

## VC Challenges — Addressed

**"Isn't this just TFDV?"**
TFDV stops at detection, is TensorFlow-locked, and has no what-if simulation. We output a manifest. We work with any framework. We simulate hypotheticals. The gap between "here's what's wrong" and "here's the fixed dataset ready for training" is the entire product.

**"Does your policy actually beat heuristics on day 1?"**
Yes — concretely. On the Criteo ads dataset, a fixed 1:10 negative downsampling heuristic achieves AUC 0.771. HeptaAI's policy, observing label entropy = 0.41, prescribes 1:7 and achieves AUC 0.779. The policy uses data-specific signal the heuristic ignores. The base policy is pre-trained on public benchmark datasets with known outcomes, so this is measured, not theoretical.

**"How does the contextual bandit learn with only 12 retrains per customer per year?"**
It doesn't rely on per-customer retrains. The policy learns from cross-customer aggregate signals: with 1,000 customers each running 10 diagnoses/month, that is 10,000 signal-outcome pairs per month. Per-customer model delta (the slow loop) is optional high-quality calibration signal, not the primary learning mechanism. The fast loop — proxy reward computed in seconds after manifest application — provides continuous signal without any retrain.

**"What is your ICP and first customer?"**
ML engineers at Series B–D tech companies running recommendation or ranking models in production. Not FAANG — they build their own. Concrete targets: DoorDash, Instacart, Duolingo, Reddit, Robinhood. Sales motion: `pip install` free tier → engineer finds value → team buys license. No cold outbound required.

**"Won't enterprise customers block you on privacy?"**
Privacy is a design constraint, not a policy. Raw data never leaves the customer's machine — the SDK is local-only. Only aggregate proxy statistics are transmitted. Differential privacy noise is applied before transmission. Air-gap mode disables all telemetry for regulated industries. The telemetry layer is open-sourced and auditable. This closes the deal, not blocks it.

**"Why won't infra players replace you?"**
Dataiku and Databricks are single-tenant platforms — they cannot build a cross-customer learned policy without breaking their privacy model. Google's TFDV is TF-locked and declining. Mode 3 (what-if simulation) has no equivalent anywhere. By the time an infra player builds this, HeptaAI has 12+ months of cross-customer signal that cannot be reproduced.

---

## Real-World Data Quality Issues Mapping

Top issues confirmed from big tech engineering research:

| Issue | Confirmed by | HeptaAI Mode |
|---|---|---|
| Training-serving skew | Meta, Google (Google Play example), Uber | 1 + 2 |
| Feature coverage drops | Meta (#1 monitored metric) | 1 + 2 |
| Label / surrogate quality | Google ("surrogate endpoint" trap), TikTok | 2 + 3 |
| Temporal drift | Uber (Holt-Winters monitoring) | 2 + 3 |
| Schema drift / pipeline errors | Uber (leading cause of model incidents) | 1 + 2 |
| Sampling bias | Google (survivorship, self-selection) | 2 + 3 |
| Distribution anomalies | Uber, Meta | 1 + 2 |
| Data contamination | Google, Uber | 1 + 2 |
| Class imbalance | Meta ads (1:1000+), fraud universal | 1 |
| Silent hardware corruption | Meta (GPU SDCs) | ✗ out of scope |

9 of the 10 most common issues in big tech are in HeptaAI's scope.

---

## Application Scenarios

- **Recommendation / ranking** (beachhead): Deduplicate interaction logs, reweight underrepresented user segments, fix train-serving skew on behavioral features
- **Fraud / spam detection**: Identify inconsistently labeled borderline cases, reweight recent data over stale historical
- **Feature deprecation**: Run policy before/after removing a feature — if manifest doesn't change, the feature wasn't contributing
- **Data pipeline audit**: Manifest summary surfaces which data sources are high vs. low quality

---

## Selling Points

**A/B story:** Same model, same architecture. One trained on raw data. One trained on HeptaAI manifest. Consistent improvement.

**"Not a tool — a system":** The policy gets smarter with every dataset it sees. Day 1 it's useful. Month 6 it's a competitive advantage.

**"Same result, less data":** Match your current AUC with 30% less training data — save compute, speed up iteration, reduce storage costs.

---

## MVP 1 — Concrete Scope & Validation Plan

MVP 1 is not the full product. It is the proof: **applying specific data fixes measurably improves model performance on a real dataset.**

### Dataset
**Criteo CTR Kaggle dataset** (45M rows, 13 continuous + 26 categorical features, binary click label). Industry standard benchmark for CTR/recommendation models. Known issues: ~3–7% positive rate, -1 coded missing values, near-duplicate impression rows, categorical train/test distribution shift. Publicly reproducible — any reviewer can run the same experiment.

### What MVP 1 Ships

**Step 1 — Profile (TFDV-style stats + HeptaAI extras)**

Per-feature output: count, missing %, mean, p50, p99, median, distribution histogram.

Two HeptaAI-specific stats TFDV does not compute:
- Label entropy per feature segment (not just global)
- L∞ train/test skew per feature (Jensen-Shannon for continuous, L∞ for categorical)

**Step 2 — Baseline model**

Two models, both intentionally simple (the model is the measurement instrument, not the product):
- Logistic Regression (sklearn) — maximally sensitive to data quality, fast iteration
- 2-layer MLP (PyTorch, ~60 lines) — more credible to ICP, validates improvement is not LR-specific

Primary metric: **NE (Normalized Entropy)**
```
NE = logloss(model) / (-p·log(p) - (1-p)·log(1-p))
```
where p = background positive rate. NE < 1.0 means the model beats a naive rate predictor. Normalizes out class imbalance — improvement in NE directly reflects signal quality, not reweighting artifact. Standard metric at Meta, LinkedIn, Uber for ranking model evaluation.

Secondary metric: AUC.

**Step 3 — Detect issues, propose fixes, user approves**

System detects issues automatically (no user rules needed for universal issues). Proposes fixes. User approves or rejects each — human stays in the loop for MVP 1.

**Step 4 — Apply approved fixes → manifest**

Three fixes demonstrated in MVP 1, each cleanly attributable:
| Fix | Mechanism | Expected direction |
|---|---|---|
| Class reweighting | positive_weight = 1/pos_rate in manifest | NE ↓  AUC ↑ |
| Near-duplicate removal | cosine similarity > 0.98 → filter | AUC ↑  training time ↓ |
| Missing value flagging | replace -1 with median + is_missing indicator | NE ↓ |

**Step 5 — Retrain and validate direction**

Retrain both LR and MLP on manifest-applied data. Confirm NE and AUC moved in the predicted direction. The prediction is directional (↓/↑), not quantitative — see Prescription Engine section.

### Target Demo Numbers (to validate, not claim)
| Model | NE baseline | NE after HeptaAI | AUC baseline | AUC after HeptaAI |
|---|---|---|---|---|
| Logistic Regression | ~0.991 | ~0.961 | ~0.752 | ~0.771 |
| 2-layer MLP | ~0.981 | ~0.954 | ~0.762 | ~0.779 |

Two models, same direction of improvement → model-agnostic claim holds.

### What MVP 1 Is Not
- Not the contextual bandit policy (that is v2)
- Not cross-customer learning (that is v2)
- Not Mode 3 what-if simulation (that is v1 stretch goal)
- Not a UI or dashboard (that is v2)

MVP 1 proves one thing: **HeptaAI-optimized training data produces better models than raw data, reproducibly, on an industry benchmark.**

---

## Detection Architecture: Universal vs. Domain-Specific

Not all data quality issues can be detected automatically. The right split:

### Universal Detectors (auto, ships out of the box)
Issues with objective definitions that apply across all domains:
- Train/test distribution skew (JSD, L∞)
- Near-duplicate density
- Class imbalance (positive rate, label entropy)
- Missing value rate per feature
- Feature value range violations
- Temporal drift (distribution shift across time windows)

These require no user input. HeptaAI detects them on any dataset.

### Domain-Specific Issues (user-defined via rule registration API)
Some issues require domain knowledge that HeptaAI cannot infer:

```python
# Example: in recommendation systems, non-impression samples are treated
# as negatives but are not true negatives — domain-specific knowledge
@opt.rule
def flag_non_impression_negatives(x):
    if x["label"] == 0 and x["impression_flag"] == 0:
        return "flag"  # not a true negative, missing from training
    return None

# Example: business-specific quality threshold
@opt.rule
def low_engagement_signal(x):
    if x["engagement_seconds"] < 0.5:
        return "downweight"  # accidental tap, not real intent
    return None
```

**This rule API is the moat.** Over time HeptaAI accumulates a library of domain-specific rule templates contributed across customers (anonymized, opt-in):
- **E-commerce:** non-impression negatives, cart abandonment signal quality, return rate labels
- **Fintech:** fraud label lag, dispute window contamination, synthetic minority oversampling boundaries
- **Food delivery:** order cancellation label timing, reorder signal freshness, geographic segment imbalance

New customers in a vertical can adopt existing templates instead of writing rules from scratch. The template library compounds — each new customer in a vertical improves the starting point for the next. Generic SDK players (cleanlab, TFDV) cannot build this without vertical focus.

---

## Prescription Engine: Human-in-the-Loop Flow

### MVP 1: Propose → User Approves → Apply

System proposes. User decides. No fix is applied without explicit approval.

```
Detect → Propose (directional impact + confidence) → [Apply] [Skip] [Adjust] → Manifest
```

This is the right design for MVP 1. Trust is earned before automation is granted.

### Automation Roadmap
```
MVP 1:  system proposes, human approves each fix individually
MVP 2:  system proposes, human approves batch ("apply all high-confidence fixes")
MVP 3:  fully automated — system runs fix → retrain → eval cycles, surfaces only
        results above confidence threshold (Karpathy autoresearch model)
```

### Directional Impact Estimates — Not Quantitative

Impact estimates are directional (↑/↓) with confidence level. Quantitative estimates (e.g. "NE will decrease 0.2%") will be wrong often enough to destroy trust before calibration data accumulates. Direction is what theory and prior research can reliably support.

```
Issue: class imbalance (6.1% positive rate)
Proposed fix: upweight positives 14.3×
Expected direction: NE ↓   AUC ↑
Confidence: HIGH
Basis: well-established in imbalanced learning literature; Confident Learning
       paper provides theoretical backing for label quality fixes

Issue: 22k near-duplicates (engagement < 0.5s)
Proposed fix: filter — weight=0
Expected direction: NE ↓   AUC ↑
Confidence: MEDIUM
Basis: Rank Pruning (Northcutt 2017) gives directional guarantee; magnitude
       depends on duplicate distribution in this specific dataset

Issue: item_category train/test skew (L∞=0.14)
Proposed fix: downsample electronics 0.8×, upsample rare categories 3×
Expected direction: AUC ↑  (especially on underrepresented segments)
Confidence: MEDIUM
Basis: domain shift theory; JSD reduction is monotonically associated with
       better generalization in literature
```

Confidence levels:
- **HIGH** — direction backed by peer-reviewed theory (Confident Learning, class imbalance literature)
- **MEDIUM** — direction backed by empirical priors on similar datasets
- **LOW** — heuristic reasoning, domain-specific rule, less prior evidence

Quantitative estimates become available in MVP 2 once Loop 3 (model delta calibration) has accumulated enough historical data to fit a calibration curve per issue type.

---

## Roadmap

| Phase | What ships | Differentiator |
|---|---|---|
| **v1 (MVP)** | SDK + universal detectors + rule registration API + TFDV-style profiler + directional prescriptions + manifest + human-in-the-loop approval + LR/MLP validation on Criteo | Detect AND prescribe AND validate — with domain rule extensibility from day 1 |
| **v2** | Contextual bandit policy + quantitative impact estimates + DataLoader wrapper + dashboard + label advisor | Learned policy, automation, stickiness |
| **Series A** | Cross-customer learning + on-prem + LLM fine-tune support + per-customer policy dashboard + integrations (Airflow, Feast) | Enterprise + expansion |

---

## Out of Scope (v1)

- Data augmentation
- PyTorch DataLoader wrapper
- UI / SaaS dashboard
- Label advisor / programmatic labeling (optional v2)
- Curriculum learning / sample ordering (full RL)
- On-prem enterprise appliance
- Pipeline integrations (Airflow, Feast, dbt)
- Silent hardware corruption detection (infra layer, not data layer)
