# DataVint Project Instructions

## Wiki Documentation

**At the start of each session, load the wiki to get all project documentation:**

Run this command to load all documentation:
```bash
./.claude/load-memory.sh
```

This loads:
- Memory files (patterns, decisions, gotchas, tips)
- All wiki documentation (18 markdown files covering architecture, API, guides, deployment, etc.)

The wiki contains:
- `wiki/architecture/` - System architecture
- `wiki/api/` - API reference docs
- `wiki/guides/` - Usage guides
- `wiki/deployment/` - Deployment documentation
- `wiki/features/` - Feature specifications
- `wiki/notebooks/` - Notebook documentation
- `wiki/changelog/` - Design decisions and history

## Memory System

Project knowledge is stored in the `memory/` folder:
- `patterns.md` - Coding patterns and conventions
- `decisions.md` - Architectural decisions
- `gotchas.md` - Common pitfalls
- `tips.md` - Useful commands

Update these files when you learn something new or make important decisions.

## Issue Review Protocol

**Automatically review every GitHub issue after creation.**

When a user creates a GitHub issue (via `gh issue create`), immediately run:
```bash
gh issue view <issue_number>
```

Then provide a comprehensive review covering:

### Review Structure

1. **✅ Strengths** (2-4 points)
   - What's well-defined
   - Clear value propositions
   - Good structure/organization

2. **⚠️ Concerns & Gaps** (3-6 points)
   - Ambiguities requiring clarification
   - Missing technical details
   - Incomplete specifications
   - Broken links or invalid assumptions

3. **🔍 Technical Feasibility Analysis**
   - Implementation estimate (hours/days)
   - Backend/frontend breakdown
   - Dependency requirements
   - Total effort calculation

4. **📝 Recommendations**
   - Explicit decisions needed (e.g., "Choose approach X for MVP")
   - Prerequisites to add
   - Simplifications to consider
   - Related issues to link

5. **✅ Final Verdict**
   - Issue quality score (X/10)
   - Blocking issues identified
   - Recommendation: Approve / Approve with modifications / Needs rework
   - Implementation priority (High/Medium/Low)

### Example Review Format

```markdown
## Issue #X Review: [Title]

### ✅ Strengths
- Clear user value proposition
- Well-structured proposal with mockups
- Security concerns identified upfront

### ⚠️ Concerns & Gaps
**1. Missing Detail X**
Current: [quote from issue]
Problem: [why this is incomplete]
Recommendation: [specific fix]

### 🔍 Technical Feasibility Analysis
**MVP Implementation Estimate:**
- Backend: 2-3 hours
- Frontend: 3-4 hours
- Total: 5-7 hours (1 day)

### 📝 Recommendations
1. Update issue with explicit MVP decision
2. Add prerequisites section
3. Validate demo datasets exist

### ✅ Final Verdict
**Issue Quality:** 8/10
**Blocking Issues:** [list]
**Recommendation:** ✅ Approve with modifications
**Implementation Priority:** Medium-High
```

### Phase 2: Engineering Review (Hybrid Approach)

**After completing the basic issue review, if the issue scores 7/10 or higher:**

1. **Convert issue to plan format:**
   - Extract implementation requirements from the issue
   - Structure as a markdown plan document
   - Save to `/tmp/issue-{number}-plan.md` with sections:
     - Problem Statement
     - Proposed Solution
     - Implementation Steps
     - Technical Considerations
     - Success Criteria

2. **Invoke /plan-eng-review:**
   - Use the Skill tool: `Skill("plan-eng-review")`
   - Point it to the converted plan document
   - Get deep architecture analysis covering:
     - Edge cases and error handling
     - Testing strategy
     - Performance considerations
     - Security implications
     - Maintenance burden

3. **Synthesize results:**
   - Combine issue review + engineering review findings
   - Highlight any critical concerns from engineering review
   - Provide unified implementation recommendations
   - Update issue quality score if engineering review reveals issues

**Skip Phase 2 if:**
- Score < 7/10 (needs issue refinement first)
- Issue is documentation-only
- Issue is a trivial bug fix (< 10 lines of code)
- User explicitly requests to skip engineering review

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore

**Data Quality Analysis Skills:**
- Class imbalance / balanced dataset / class distribution → invoke /check-imbalance
- Completeness / missing values / null values → invoke /check-completeness
- High cardinality / unique values / ID columns → invoke /check-cardinality
- Entropy / information content / constant features → invoke /check-entropy
- Uniqueness / duplicate values / low uniqueness → invoke /check-uniqueness
- Distinctness / distinct values / few distinct → invoke /check-distinctness

---

# Product Design Document

## ✅ ACTIVE DESIGN: DataVint - ML Execution Waste Control Layer (v2)

**Generated**: /plan-ceo-review on 2026-05-13
**Branch**: main
**Status**: APPROVED ✅
**Mode**: Startup - SELECTIVE EXPANSION
**Last Updated**: 2026-05-13
**Full Design**: `wiki/changelog/2026-05-13-datavint-gpu-waste-control-design-v2-expanded.md`

### Executive Summary

**Product**: Pre-execution CLI gate that prevents duplicate ML experiments before GPU allocation

**Timeline**: 10 weeks (1 engineer, expanded from 8 weeks for 2.3x higher success probability)

**Problem**: ML teams waste 20-30% of GPU training budget on duplicate experiments and preventable failures. Engineers running 20+ experiments lose track of what they already tried and accidentally rerun similar configurations, wasting thousands of dollars on redundant compute.

**Solution**: CLI tool (`datavint check`) that queries experiment database, blocks exact duplicates, warns on near-duplicates (95%+ similar), shows estimated cost, and displays outcomes from similar past experiments.

**Target Customer**: ML Team Lead at resource-constrained ML startup
- Company stage: ML-focused startup to Series B/C ($20K-$500K/month GPU spend)
- Team size: 5-20 person ML team
- Pain: Hitting GPU quota limits, forced to downsample data
- Has budget authority to buy tools that save GPU costs

**Value Prop**: "Stop wasting 1 in 4 training slots on duplicates when you're already running out of capacity"

**Economics**:
- Customer segment: ML-focused startups ($20K-$150K/month GPU spend)
- Conservative estimate: $50K/month on GPU training
- 20-30% waste = $10K-$15K/month = $120K-$180K/year wasted
- Potential pricing: 10-20% of savings = $1K-$3K/month per customer

**Demand Evidence**: 3 customer conversations (Physical.ai, Phia, startup) + 1 verbal commitment

### v2 Key Features (10-Week MVP)

**Week 1-2: Core CLI + Exact Duplicate Detection**
- `datavint check <dataset>` command
- `datavint history` command
- Dataset fingerprinting (<30s worst case)
- Local SQLite storage

**Week 3-4: Near-Duplicate Detection ⭐**
- 95%+ similarity detection via cosine similarity
- Show similar experiments: "95% similar experiment ran 2 weeks ago"
- Configurable threshold (`--similarity=0.95`)

**Week 5-6: Outcome Linkage + Cost Estimation ⭐**
- Store experiment outcome (success/failure/metrics)
- `datavint log-result <id> --status=success --metric=0.85`
- GPU cost configuration: `datavint config set-gpu-price 4.76`
- Show: "Estimated cost: $4200. Similar experiment failed with OOM."

**Week 7-8: Fast Path ⭐**
- Cached fingerprints (instant if path unchanged in 24h)
- Cloud metadata (S3 ETag, GCS md5Hash) for <5s checks
- Sampling fallback (30s worst case)
- Target: 90% of checks complete in <5 seconds

**Week 9: Optional Team Sync ⭐**
- `datavint init --team` enables cloud backend
- PostgreSQL hosted (Supabase/Render)
- Team collaboration: Engineer A's experiments visible to Engineer B

**Week 10: Polish + Documentation**
- Error handling, docs, pilot testing

### Moat & Competitive Advantage

**Positioning**: "Experiment governance" vs "experiment tracking" (MLflow/W&B are passive)

**Moat**:
1. **Outcome data** (success/failure/metrics) - unique to DataVint, MLflow doesn't have this
2. **Compounding value** - database becomes irreplaceable after 6 months
3. **Catastrophic prevention** - prevents one $40K mistake (immediate ROI)

**Why MLflow can't copy easily**:
- Outcome data requires user instrumentation (`datavint log-result`)
- Near-duplicate detection requires similarity engine
- Cost estimation requires GPU pricing configuration
- DataVint has 6 months head start on database

### Success Criteria

**Week 10 (Launch)**:
- 50 PyPI downloads in first week
- 10 users run `datavint check` at least once
- 3 users active (5+ checks)
- 1 user configures GPU pricing (activation)

**Month 1**:
- 200 total downloads
- 20 active users
- 5 users configure GPU pricing
- 2 users report "warned me about similar experiment"

**Month 2**:
- 60% retention
- 1 user refers to teammate
- 1 user reports "cost estimation prevented wasteful run"

**Month 3**:
- 1 customer converts to paid OR requests team deployment

### Implementation Status

**Current**: Design approved, Week 1 ready to start

**This Week**:
1. ✅ Validate pricing with committed customer
2. ✅ Start Week 1 implementation (CLI framework + fingerprinting)
3. ✅ Schedule Week 11 kickoff call

---

## SUPERSEDED DESIGNS

### Design: DataVint - Recommendation Systems Data Quality SDK

**Generated**: /office-hours on 2026-05-04
**Status**: SUPERSEDED (pivoted to GPU waste control on 2026-05-13)
**Full History**: See `wiki/changelog/` for design evolution

**Why Superseded**: Customer validation (3 ML team leads) revealed broader problem than data quality. Customers said "data quality is one aspect of avoiding unnecessary GPU runs" and pushed toward GPU waste control.

**Pivot History**:
- `2026-05-04`: Rec systems data quality SDK (original design)
- `2026-05-10`: Experiment-level data versioning pivot
- `2026-05-13`: GPU waste control layer (customer-driven pivot)
- `2026-05-13`: v2 expanded (CEO review + selective expansion)

For full details on superseded designs, see `wiki/changelog/`.
