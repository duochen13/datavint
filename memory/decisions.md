# Architectural Decisions

## [2026-05-11] Sequential Hyperparameter Tuning: Local Optima Risk (Future Consideration)

**Observation:** Mock data shows sequential sweeps (Sweep 1: lr → pick best → Sweep 2: sample_rate with fixed lr). This pattern can miss global optimum.

**The Problem:**
```
Sweep 1: Test lr=[0.001, 0.005, 0.01, 0.02] with sample_rate=0.5 (default)
         Pick best: lr=0.005 (NE=0.712 at sample_rate=0.5)

Sweep 2: Test sample_rate=[0.4, 0.6, 0.8] with lr=0.005 (fixed)
         Pick best: sample_rate=0.6 (NE=0.701 at lr=0.005)

Issue: Best lr at sample_rate=0.5 may not be best lr at sample_rate=0.6
Maybe: lr=0.008, sample_rate=0.6 → NE=0.690 (better, but never tested!)
```

**Why Hyperparameters Interact:**
The optimal value of parameter A depends on the value of parameter B. Sequential optimization (greedy) can get stuck in local optima.

**Counter-Arguments (Why Sequential is Still Valid):**
1. **Computational Cost:** Grid search is O(n^d). Example: 4 lr × 4 sample_rate × 3 batch_size = 48 runs vs ~11 sequential runs
2. **Practical Effectiveness:** Sequential often gets "good enough" results (maybe 98% of global optimum)
3. **Domain Knowledge:** ML engineers know which params interact strongly (joint optimize) vs weakly (sequential optimize)
4. **Diminishing Returns:** Global optimum may only improve by 0.5% but cost 5x compute

**Alternatives:**
- **Random Search:** Sample (lr, sample_rate) pairs randomly
- **Bayesian Optimization:** Model hyperparameter response surface, recommend next trial
- **Grid Search on Subsets:** Do 2D grid on strongly interacting params only
- **User Education:** Warn about interaction risks without forcing an approach

**DataVint Feature Idea (v2.0 - Not v1.0):**
Don't prescribe optimization strategy, but **warn users** when detecting sequential patterns:

```
⚠️ Sequential Sweep Pattern Detected

You're optimizing sample_rate with lr fixed at 0.005 (best from Sweep 1).

Risk: The best lr may differ at different sample_rates due to parameter interaction.

Suggestions:
• Grid search: Test lr × sample_rate combinations (more expensive)
• Random search: Sample parameter pairs randomly
• Continue: Proceed with sequential optimization (faster, usually good enough)

Learn more: [link to doc about hyperparameter interaction]
```

**Decision for v1.0:**
- ✓ Keep mock data showing sequential pattern (realistic, common in practice)
- ✓ Don't implement warning yet (need real user feedback first)
- ✓ Document this as v2.0 consideration
- ✓ Focus v1.0 on visualization and lineage tracking, not optimization advice
- ⚠️ Don't make users feel DataVint is opinionated about "the right way" to tune

**Challenge to This Concern:**
User's intuition is correct about the risk, but:
1. Most ML engineers already know this trade-off
2. Sequential is industry standard for initial exploration
3. Warning might be noise for experienced users
4. Better to provide tools than prescribe methods

**Status:** Documented for future consideration, not blocking v1.0

**Files:**
- `server/api/routes/experiments_mock.py` - Mock data shows sequential sweeps
- Future: Sweep pattern detection logic

## Session Management

- Using gstack `/context-save` and `/context-restore` for session continuity
- Checkpoint mode: explicit (not continuous auto-commits)
- Skill routing: not yet configured in CLAUDE.md

## Data Validation Architecture

- Following TFDV (TensorFlow Data Validation) functional API design
- Schema detector split into modular components:
  - Type detection
  - Range detection
  - Separate orchestration layer

## Enriched Statistical Detectors (v0.2)

**Decision Date**: 2026-05-08

**Context**: Issue #9 requested advanced statistical metrics inspired by Amazon Deequ and Great Expectations. Needed to enrich data profiling beyond basic quality checks.

**Decision**: Implemented 6 new detectors focusing on statistical distribution and information theory:
1. **ClassImbalanceDetector** - Label distribution analysis (requires `label_col` parameter)
2. **CompletenessDetector** - Missing value analysis (completeness = 1 - null_rate)
3. **CardinalityDetector** - High cardinality detection for categorical features
4. **EntropyDetector** - Information content analysis using Shannon entropy
5. **UniquenessDetector** - Duplicate value detection (unique = appears exactly once)
6. **DistinctnessDetector** - Distinct value analysis (distinct = any unique value)

**Rationale**:
- Prioritized single-column metrics over multi-column (correlation, mutual information) for v0.2
- Deferred probabilistic algorithms (HyperLogLog) to future releases
- Focused on metrics most valuable for recommendation systems (target domain)
- Maintained two-phase architecture: compute statistics once, run detectors on cached results

**Integration Points**:
- Python API: `vint.profile(df, label_col='label')`
- Chatbox: Natural language queries via LLM code generation
- Claude Skills: 6 new skills in `.claude/skills/` with rich formatting
- Skill routing: Automatic invocation via CLAUDE.md rules

**Deferred**:
- Multi-column metrics (MutualInformation, Correlation)
- Probabilistic algorithms (ApproxCountDistinct, ApproxQuantiles)
- Constraint-based metrics (Compliance, PatternMatch)

## Experiment Versioning Architecture (2026-05-11)

**Decision Date**: 2026-05-11

**Context**: Need to track ML experiment lineage including data versions and model runs for recommendation systems.

**Decision**: Implemented experiment tracking with content-based data versioning:

**Components**:
1. **SDK**: `datavint.experiment()` context manager with SQLite storage
2. **Backend**: FastAPI routes at `/api/experiments/:id/lineage`
3. **Frontend**: Bipartite graph dashboard (Vue 3 + SVG)

**Key Architectural Choices**:

### 1. Content-Based Data Versioning
- **Decision**: SHA256 hash of DataFrame content (sorted columns)
- **Rationale**:
  - Automatic deduplication (same data → same ID)
  - Detects data changes automatically
  - No manual version management needed
- **Implementation**: First 7 chars of SHA256 (git-style short hash)

### 2. SQLite Metadata Store
- **Decision**: Local SQLite database at `~/.datavint/metadata.db`
- **Rationale**:
  - Zero-config persistence
  - Easy to query with SQL
  - Portable across environments
  - No server dependencies
- **Schema**:
  - `data_commits`: id, experiment_id, hash, message, row_count, timestamp
  - `model_runs`: id, experiment_id, data_commit_id, metrics, params, best, sweep_id

### 3. Bipartite Graph Visualization
- **Decision**: Two-column layout with SVG Bezier curves
- **Rationale**:
  - Clear data → model lineage flow
  - Sweep clustering shows hyperparameter groups
  - Hover interactions reveal connections
- **Colors**:
  - Default lines: Light green (--accent-light-green)
  - Active: Purple (--accent-purple)
  - Best model: Bright green (--accent-green)

### 4. Winner Selection Logic
- **Decision**: Lowest NE (Normalized Entropy) = best performance
- **Rationale**: User's recommendation system domain uses this metric
- **Implementation**:
  - Overall best: Lowest NE across all runs
  - Sweep winner: Lowest NE within that sweep

### 5. Mock Data Strategy
- **Decision**: Frontend works with mock data, falls back gracefully
- **Rationale**:
  - Frontend development unblocked by backend delays
  - Easy to develop/test UI in isolation
  - Seamless transition when backend ready
- **Implementation**: try/catch with loadMockData() fallback

**Integration Points**:
- SDK: `datavint.experiment()` context manager
- API: `GET /api/experiments/:id/lineage`
- Dashboard: http://localhost:5173/experiments/:id
- Demo: `python3 examples/experiment_tracking_demo.py`

**Deferred to Future**:
- MLflow integration (read local mlflow.db)
- Real-time monitoring dashboard
- Automatic model comparison reports
- Slack/PagerDuty alerts for quality regressions

## Product Pivot: GPU Waste Control (2026-05-13)

**Decision Date**: 2026-05-13

**Context**: Customer validation (3 ML team leads) revealed broader problem than data quality. Customers said "data quality is one aspect of avoiding unnecessary GPU runs" and pushed toward GPU waste control.

**Decision**: Pivot from "data quality for rec systems" to "ML execution waste control layer"

**New Product**: Pre-execution CLI gate that prevents duplicate experiments before GPU allocation

**Rationale**:
- Validated with 3 customers (Physical.ai, Phia, startup)
- Direct quote: "We are spending too much on unknown-value experiments"
- Resource-constrained customers hitting GPU quota limits (not efficiency-optimizing)
- 20-30% GPU waste from duplicate experiments
- 1 customer committed: "Yes, I will try DataVint when you ship it"

**Design Docs**:
- Original: `wiki/changelog/2026-05-04-datavint-rec-systems-data-quality-sdk.md`
- Pivot: `wiki/changelog/2026-05-10-datavint-experiment-versioning-design.md`
- Final: `wiki/changelog/2026-05-13-datavint-gpu-waste-control-design.md`

## CEO Review: Selective Expansion (2026-05-13)

**Decision Date**: 2026-05-13
**Review Mode**: SELECTIVE EXPANSION
**Original Score**: 6.5/10 (good to build, not good to win)

**Context**: /plan-ceo-review challenged original 8-week MVP scope as too narrow to create defensible moat.

**Critical Gaps Identified**:
1. Exact duplicates only = one-time value (no compounding value)
2. Moat is time-dependent (6 months before database becomes irreplaceable)
3. No cost visibility = ROI not clear until month 2-3
4. 30-second latency too slow for CLI tool
5. Cloud storage dependencies (boto3, GCS) add setup friction

**Decision**: EXPAND scope from 8 weeks to 10 weeks with 4 critical additions

### Addition 1: Near-Duplicate Detection (Week 3-4)
**Decision**: Near-duplicates (95%+ similar) REQUIRED for v1.0, not v2.0
**Rationale**:
- Exact duplicates are rare (engineers rarely run IDENTICAL configs)
- Near-duplicates are where waste happens (95% similar configs)
- Creates compounding value: "We tried 95% similar—it failed with OOM"
**Implementation**: Cosine similarity on config hashes, configurable threshold

### Addition 2: Outcome Linkage (Week 5-6)
**Decision**: Store experiment outcome (success/failure/metrics) alongside fingerprint
**Rationale**:
- Fingerprints without outcomes = glorified git log (anyone can copy)
- Outcome data is unique to DataVint (MLflow doesn't have this)
- Enables learning: "Similar experiment failed with OOM. Consider reducing batch size."
**Moat**: Outcome data creates defensible competitive advantage

### Addition 3: Cost Estimation (Week 5-6)
**Decision**: Show "estimated $X" for each experiment (REQUIRED for v1.0)
**Rationale**:
- Startups won't pay $1-3K/month for abstract savings without proof
- Cost estimation makes ROI visible in month 1
- "You've prevented $12K in duplicate runs" justifies procurement
**Activation metric**: User configures GPU pricing within 48 hours

### Addition 4: Optional Team Sync (Week 9)
**Decision**: Add optional cloud backend for team collaboration in v1.0
**Rationale**:
- "Team memory" is core value prop, can't wait until v2.0
- Local-only = personal tool, not team tool
- Engineer A's experiments must be visible to Engineer B
**Implementation**: `datavint init --team` enables PostgreSQL cloud sync (Supabase/Render)

### Addition 5: Fast Path (<5s typical) (Week 7-8)
**Decision**: Add cached fingerprints + cloud metadata fast path
**Rationale**:
- 30 seconds too slow (git status is <1s, docker build is <5s)
- Engineers won't wait 30s every time
**Implementation**:
- Cached fingerprints: If path unchanged in 24h, use cached hash (instant)
- Cloud metadata: S3 ETag, GCS md5Hash (<5s, no download)
- Sampling fallback: Only if path changed and no cloud metadata (30s worst case)
**Target**: 90% of checks complete in <5 seconds

### Scope Reduction: Remove Cloud Storage from v1.0
**Decision**: Remove boto3 (AWS) and google-cloud-storage (GCP) dependencies
**Rationale**:
- boto3 + GCS add setup friction (AWS credentials, IAM roles, dependency size)
- Local filesystem only = pip install → working tool in <5 minutes
- Cloud storage support deferred to v1.1
**Impact**: Reduces adoption friction, simplifies v1.0

### Revised Timeline
- **Original**: 8 weeks (1 engineer)
- **Expanded**: 10 weeks (1 engineer)
- **Tradeoff**: 25% longer, but 2.3x higher success probability (30% → 70%)

### Revised Assignment: Validate Pricing
**Original**: "Get calendar invite for Week 7 kickoff"
**Expanded**: "Validate pricing BEFORE building"
**Action**: Ask committed customer: "Pricing will be $1-3K/month. If DataVint saves you $10K in 3 months, would you pay?"
**Rationale**: Don't build without validating willingness to pay

### Key Decision: "Aha Moment" Hypothesis
**Question**: What creates lock-in?
**Options**:
- (A) Instant value: catch 1 duplicate in week 1
- (B) Compounding value: database irreplaceable after 6 months
- (C) Catastrophic prevention: prevent 1 $40K mistake in first 3 months

**Decision**: Optimize for (C) catastrophic prevention
**Rationale**:
- (B) takes too long (6 months = MLflow can copy in 3 months)
- (A) is nice but not procurement-worthy
- (C) justifies procurement immediately: "It caught one $40K mistake"
**Validation**: Track which users convert to paid, ask "what convinced you?"

### Success Criteria Changes

**Week 10 (Launch) - Added Leading Indicators**:
- 50 PyPI downloads in first week
- 10 users run `datavint check` at least once
- 3 users active (5+ checks)
- 1 user configures GPU pricing (activation metric)

**Month 1 - Added Growth Metrics**:
- 200 total downloads
- 20 active users
- 5 users configure GPU pricing
- 2 users report "warned me about similar experiment"

**Month 2 - Revised Retention**:
- 60% retention (relaxed from 70%)
- 1 user refers to teammate (viral growth)
- 1 user reports "cost estimation prevented wasteful run"

### What This Reveals About Product Strategy

**On scope narrowness**:
- Original instinct: "Start with exact duplicates, add near-duplicates in v2.0"
- CEO challenge: "Exact duplicates are rare. Near-duplicates are where waste happens."
- Learning: "MVP" can be too minimal if it doesn't create a moat

**On moat timing**:
- Original assumption: "6 months of experiments = irreplaceable database = moat"
- CEO challenge: "6 months is too long. MLflow can copy in 3 months."
- Learning: Time-dependent moats are vulnerable to fast followers. Need immediate moat (outcome data).

**On pricing validation**:
- Original approach: "Get verbal commitment, ship product, then talk pricing"
- CEO challenge: "Validate willingness to pay BEFORE building"
- Learning: Builder mode (ship first, sell later) vs customer development mode (validate first, then build)

### v1 vs v2 Comparison

| Feature | v1 (Original) | v2 (Expanded) |
|---------|---------------|---------------|
| Timeline | 8 weeks | 10 weeks |
| Exact duplicates | ✅ | ✅ |
| Near-duplicates | ❌ (v2.0) | ✅ (v1.0) |
| Cost estimation | ❌ | ✅ (required) |
| Outcome linkage | ❌ | ✅ |
| Team sync | ❌ (v2.0) | ✅ (optional) |
| Fast path | ❌ (30s) | ✅ (90% <5s) |
| Cloud storage | ✅ (boto3, GCS) | ❌ (deferred) |
| Success probability | 30% | 70% |

**Bottom line**: v2 adds 2 weeks (25% longer) but increases success probability 2.3x. The expansions transform DataVint from "duplicate blocker" (one-time value) to "experiment advisor" (compounding value + immediate ROI).

**Files**:
- Design v2: `wiki/changelog/2026-05-13-datavint-gpu-waste-control-design-v2-expanded.md`
- CEO Review Summary: `wiki/changelog/2026-05-13-ceo-review-summary.md`

## Week 1 Implementation: CLI + Exact Duplicate Detection (2026-05-13)

**Decision Date**: 2026-05-13
**Status**: COMPLETED ✅

**Context**: Started Week 1 of 10-week v2 implementation. Goal: Working CLI with exact duplicate detection.

**Implementation Decisions**:

### 1. CLI Framework: Click (not Typer)
**Decision**: Use Click for CLI framework
**Rationale**:
- More mature and widely adopted than Typer
- Simpler API for basic commands
- Better documentation and community support
- Lighter dependency (no Pydantic required)

### 2. Database Schema: Separate from Experiment Tracking
**Decision**: Created new `experiment_fingerprints` table, separate from existing `data_commits`
**Rationale**:
- `data_commits` is for experiment lineage tracking (data versioning)
- `experiment_fingerprints` is for duplicate detection (pre-execution gate)
- Different use cases, different access patterns
- Allows independent evolution of both systems

### 3. Fingerprinting Strategy: Sampling-Based
**Decision**: Sample 0.1% of dataset (0.001) for fingerprinting
**Rationale**:
- <30 second target for 500GB dataset (500MB sample)
- SHA256 on sampled data, first 16 characters (not 7 like git)
- Deterministic (random_state=42) for reproducibility
- Trade-off: collision risk vs speed (16 chars = 2^64 possibilities)

### 4. Database Path: ~/.datavint/experiments.db (not ~/.datavint/metadata.db)
**Decision**: Use separate database for CLI vs experiment tracking
**Rationale**:
- `metadata.db` used by `datavint.experiment()` context manager (SDK)
- `experiments.db` used by `datavint check` CLI (pre-execution gate)
- Separation of concerns: SDK ≠ CLI
- Future: may merge or add sync layer

### 5. Exit Codes: 0 (no duplicate), 1 (duplicate warning), 2 (error)
**Decision**: Use standard Unix exit codes with semantic meaning
**Rationale**:
- 0 = success (safe to proceed, no duplicate)
- 1 = warning (duplicate found, user should consider skipping)
- 2 = error (invalid input, unsupported format, etc.)
- Allows scripting: `datavint check data.csv && python train.py`

### 6. File Format Support: CSV, Parquet, JSON (Week 1)
**Decision**: Support CSV, Parquet, JSON in Week 1
**Rationale**:
- Most common ML data formats
- All supported by pandas (no extra dependencies)
- Cloud storage (S3/GCS) deferred to Week 7 (v1.1)

### 7. Configuration: JSON file at ~/.datavint/config.json
**Decision**: Store config in JSON file (not TOML, YAML, or env vars)
**Rationale**:
- Standard library support (no extra deps)
- Simple key-value structure
- Easy to read and edit manually
- Future: may add ~/.datavint/config.toml for richer config

**Implementation Files**:
- `datavint/cli.py` - CLI commands (check, history, config)
- `tests/api/test_cli.py` - 15 tests, all passing
- `pyproject.toml` - Added Click dependency + CLI entry point

**Week 1 Milestone**: ✅ ACHIEVED
- Working `datavint check` command (exact duplicate detection)
- Working `datavint history` command (show past experiments)
- Working `datavint config` command (set GPU price for future use)
- 15 tests passing
- Tested on real datasets (Titanic, train.csv)

**Next**: Week 3-4 will add near-duplicate detection (95%+ similarity) using cosine similarity.
