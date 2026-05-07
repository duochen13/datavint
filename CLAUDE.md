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

---

# Product Design Document

## Design: DataVint - Recommendation Systems Data Quality SDK

**Generated**: /office-hours on 2026-05-04
**Branch**: main
**Status**: APPROVED
**Mode**: Startup
**Last Updated**: 2026-05-07

## Problem Statement

DataVint is a data quality detection and optimization tool for ML training pipelines. The core problem: **ML teams at recommendation system companies lose critical model metrics (0.1-0.3 NE) due to data quality issues that take 1-2 weeks to debug manually.**

Current positioning addresses 80% data quality detection/optimization, 10% model validation, 10% traceability. Target customer and go-to-market strategy focus exclusively on **recommendation systems** as the initial vertical.

## Demand Evidence

**Primary source: Lived experience at Meta**
- Senior Software Engineer at Meta working on ML training data pipeline for modern recommendation systems (Facebook Feed Ranking, Instagram Feed Ranking, Reels)
- **Specific incident**: 0.2 NE (Normalized Entropy) metric loss across all recommendation models
- **Root cause**: Data quality issues - duplication ratio, missing features, low feature coverage, O2O (one-to-one) issues, train-test skew, poor label design
- **Time to find**: 1-2 weeks (offline training and QE validation takes long with huge datasets)
- **Fix**: Upstream ML data pipeline correction
- **Recovery**: 0.2 NE improvement = millions in ad revenue + saved compute at Meta scale

**Quote**: "Modeling engineer doesn't have e2e picture of how data is generated, infra engineer doesn't know what model needs or how model works. There is gap between MLE and SWE working on ML pipeline. We have seen model perform poorly, and after we fix data quality issue, the model recovered and even became better."

## Status Quo

**Current approach at Meta (and elsewhere)**:
- Mostly manual Jupyter notebooks for data quality inspection
- Sometimes engineers cannot discover what's wrong
- Takes significant time to debug because company culture focuses on short-term goals
- People rush to try different enumerations without deep thinking
- **No systematic way to expose and fix problems** - even at Meta with unlimited resources

## Target User & Narrowest Wedge

**Target User**: ML Team Lead (Staff/Principal MLE or Engineering Manager)
- Company stage: Series B-D ($20M-$300M ARR)
- Team size: 5-15 person ML team
- Domain: **Recommendation systems** (feed ranking, content recommendations, e-commerce)
- Has all three: (1) feels the pain directly, (2) has budget authority, (3) can implement changes

**Validated via LinkedIn search**: ICP exists and is reachable at companies like DoorDash, Instacart, Reddit, Faire, Duolingo, Spotify, Pinterest, Snap.

**Narrowest Wedge**: Manifest generation + apply (universal prescription)
- Force-ranked as the ONE feature that moves the needle in 8 weeks
- Not just diagnosis (like TFDV) - actual prescription with sample weights + filter masks
- Universal issues (80%): train-test skew, feature coverage, label imbalance
- Domain-specific support (20%): duplication ratios, custom label designs

**User quote**: "I don't want datavint to only be a data quality diagnosis tool, I want to provide suggestion data operation on data to make data in better shape and make model better."

## Constraints

1. **Timeline**: 8 weeks to MVP that delivers real value
2. **Universal vs Domain Split**: 80% universal problems (train-test skew, feature coverage, label imbalance), 20% domain-specific (user-definable rules)
3. **Privacy**: Cannot share learnings publicly across different products except common data ops - requires differential privacy + air-gap mode for enterprises
4. **Continuous Value**: Data quality is ongoing monitoring problem, not one-time fix - new issues appear every data refresh/pipeline change
5. **Integration**: Must work with existing training pipelines - cannot require full platform migration
6. **Sales Cycle**: Developer-led but may take 2-3 months (free → eval → procurement)

## Premises (All Validated)

1. **0.2 NE loss caused by data quality, not architecture/hyperparameters** ✓
   - Confirmed: issues were duplication, missing features, coverage, O2O, skew, poor labels

2. **Universal manifest works across domains WITHOUT deep domain knowledge** ✓ (with nuance)
   - Train-test skew, feature coverage, label imbalance ARE universal
   - Duplication ratios ARE domain-specific (user can define rules)
   - 80/20 split confirms this premise holds for core value prop

3. **Engineers will change training pipeline to apply manifest** ✓
   - Confirmed no blocking concern after seeing single-read API design
   - At Meta, they DO fix pipelines when issues are found - the gap is systematic detection

4. **Cold start works with hardcoded rules before learned policy** ✓
   - v0.2 ships with hardcoded rules, v1.0 adds learned policy
   - Committed to 8-week timeline with hardcoded approach

5. **TFDV stopped at detection for organizational reasons, not technical** ✓
   - Quote: "Google has many ML teams, different team have different context and different problems to solve, they may try different ways to fix the gap, there is no only one correct solution"
   - This IS the market opportunity - smaller companies need prescription, not just detection

6. **Can acquire via developer content without enterprise sales** ✓ (with timeline caveat)
   - Developer-led acquisition works
   - Reality check: 2-3 month sales cycles even for dev tools
   - Target buyers reachable on LinkedIn (recommendation system engineers)

## Approaches Considered

### Approach A: 8-Week MVP - Detection + Hardcoded Prescription
**Summary**: Extend existing 6 detectors to generate manifest (sample weights + filter masks). Hardcoded rules per issue type. No learned policy. Recommendation systems only initially.

**Effort**: M (2-3 engineers, 8 weeks)
**Risk**: Low (building on existing codebase)

**Pros**:
- Ships in 8 weeks with real value (manifest generation + apply)
- Reuses all existing detector infrastructure
- Low technical risk - proven patterns

**Cons**:
- Hardcoded rules less sophisticated than learned policy
- Generic across recommendation systems (not hyper-specific to architectures)
- May need iteration on manifest format based on customer feedback

**Reuses**: All existing detector infrastructure (missing values, duplicates, schema, range, skew, imbalance)

### Approach B: Full Vision - Learned Policy Platform
**Summary**: All 20 detectors from taxonomy, differential privacy, cross-customer federated learning, domain-adaptive policy. Multi-domain from day 1 (rec + fraud + search).

**Effort**: XL (5+ engineers, 16-20 weeks)
**Risk**: High (complex privacy + policy learning + multi-domain)

**Pros**:
- Complete v1.0 vision with learned policy intelligence
- Cross-customer learning creates moat
- Multi-domain positioning from launch
- Most sophisticated technical architecture

**Cons**:
- 16-20 weeks delays customer validation - risk building wrong thing
- Complex privacy architecture may delay shipping
- Multi-domain positioning dilutes message (violates "narrow beats wide" principle)
- High risk - many moving parts

**Reuses**: Core detection patterns, extends significantly with policy engine

### Approach C: Rec Systems SDK - Vertical Deep Dive ⭐ **RECOMMENDED**
**Summary**: Hyper-specific to recommendation systems. Pre-built knowledge of rec-specific patterns (O2O issues, behavioral feature skew, watch-time vs like-click label design). Ready-made manifest templates for common rec architectures (TikTok-style feed, e-commerce, social feed ranking).

**Effort**: M (2-3 engineers, 8 weeks)
**Risk**: Medium (very narrow positioning, but faster adoption in target market)

**Pros**:
- Fastest path to customer validation (8 weeks)
- Domain expertise advantage (years of Meta rec systems knowledge)
- Pre-built templates = immediate value for target customers
- Speaks the language of rec system engineers (O2O, NE, behavioral features)
- Differentiated positioning vs generic tools
- Enables premium pricing (vertical expertise)

**Cons**:
- Extremely narrow positioning - locks out fraud/search/other ML domains initially
- Requires deep recommendation systems domain knowledge (but we have this)
- Templates may not cover all rec architectures (requires iteration)
- Expansion to other domains requires significant rework

**Reuses**: Existing detector core + profiling infrastructure, adds rec-specific knowledge layer

## Recommended Approach

**Approach C: Rec Systems SDK - Vertical Deep Dive**

**Rationale**: Committed to "recommendation systems for v1.0 positioning" and doubled down by choosing the hyper-vertical approach over the broader MVP. This is the right call for three reasons:

1. **Domain expertise moat**: Years at Meta on FBR/IGR/Reels = deep knowledge that competitors can't easily replicate. Pre-built templates for common architectures (feed ranking, content discovery, e-commerce rec) create immediate value.

2. **Clearest customer conversation**: "I hit 0.2 NE loss at Meta on Reels ranking due to data quality. Does your team hit train-test skew on behavioral features?" beats "We detect data quality issues across any ML domain."

3. **Expansion path exists**: Year 1 = recommendation systems → Year 2 = fraud detection + search ranking → Year 3 = any supervised ML. Wedge enables expansion, but generic positioning has no wedge.

The focused pitch wins. **Narrow beats wide, early.**

## Open Questions

1. **Sales cycle acceleration**: How to compress 2-3 month developer-led cycles? Free tier with instant value? PLG motion?

2. **Privacy architecture**: Air-gap mode details for enterprises who won't send any telemetry - how does this affect cold start quality?

3. **Expansion timing**: When to add fraud detection / search ranking domains? After X customers? After $Y ARR? After learning what?

4. **Distribution channel priority**: PyPI vs conda vs GitHub vs custom installer? What do rec system engineers expect?

5. **Manifest template coverage**: Which rec architectures to cover first? TikTok-style feed, e-commerce, social feed ranking, discovery systems?

## Success Criteria

**8-week validation**:
- 5 ML Team Leads at rec companies (DoorDash, Instacart, Reddit, Faire, Duolingo, etc.) validate the "0.2 NE loss + 1-2 week debugging" pain point
- 3 companies commit to trying DataVint when it ships (verbal + calendar commitment)

**First customer success** (Month 3):
- 1 customer achieves measurable metric improvement (NE, AUC, CTR, watch time) using DataVint manifest
- Customer can articulate the specific data quality issue DataVint found and the impact of fixing it

**Retention validation** (Month 4):
- Month 2 retention > 70% (validates continuous monitoring value, not one-time diagnostic)
- At least 2 customers run DataVint on every training data refresh

## Distribution Plan

**Initial distribution** (v1.0):
- Python SDK via PyPI (`pip install datavint`)
- GitHub repository for issues/community/examples
- Documentation site with recommendation systems examples (feed ranking, content discovery, e-commerce)
- No hosted SaaS service initially - pure SDK model

**Content-led acquisition**:
- Blog posts on rec system data quality patterns (O2O issues, behavioral feature skew, label design)
- Case study: "How we recovered 0.2 NE at Meta by fixing data quality"
- Example notebooks for common rec architectures

**Later** (v2.0+):
- Hosted monitoring service (continuous data quality dashboard)
- Slack/PagerDuty integration for quality alerts
- Pre-built integrations with common training orchestration (Airflow, Kubeflow, Metaflow)

## Dependencies

**Technical**:
- Existing DataVint codebase (6 detectors, profiling, statistics modules)
- Recommendation system domain knowledge (have this from Meta experience)
- Manifest format definition (sample weights + filter masks schema)

**Go-to-market**:
- Access to 5+ ML Team Leads at rec companies for validation calls
- Case study content from first customer success
- Community building (Slack workspace, GitHub discussions)

**Blockers**:
- None identified - have domain expertise, working codebase, and target customer access

## The Assignment

**Your one concrete action this week**:

Find 3 ML Team Leads at recommendation system companies (not Meta).

**How to find them**: LinkedIn search for "Staff Machine Learning Engineer" OR "Principal MLE" OR "Engineering Manager Machine Learning" at companies with known recommendation systems (DoorDash, Instacart, Reddit, Faire, Duolingo, Spotify, Pinterest, Snap, etc.)

**The call**:
1. Introduce yourself: "I'm building DataVint, a data quality tool for recommendation systems. I spent years at Meta on feed ranking and saw 0.2 NE losses that took 1-2 weeks to debug."
2. Ask: "Have you ever lost metric points to data quality issues and spent days debugging it?"
3. If yes: "I'm shipping DataVint in 8 weeks - it detects these issues automatically and generates fixes. Would you try it when it's ready?"
4. Get verbal commitment + follow-up date.

**Success metric**: 3 calls completed, at least 2 validate the pain point, at least 1 commits to trying DataVint.

This is not research. This is customer development. Every conversation teaches you how to pitch, what language resonates, and what objections you'll face. Do it before you build more.

## Design Philosophy & Founder Mindset

**On narrowing vs expanding**: When uncertain about the customer, the instinct was to make the product bigger - "a platform for engineers to build toolkits." Most founders do this. When you don't know the customer, the temptation is to add scope so you're "covering more bases." Resisted this and narrowed instead.

**On vertical positioning**: Initially resisted "I don't want to only do recommendation" even after finding recommendation system buyers on LinkedIn. The fear was real - what if you pick wrong? What if the market is too small? What if you need to pivot? But narrow beats wide early.

**On challenging premises with specifics**: When presented with "universal manifest works across domains," didn't just agree. Articulated the 80/20 split: train-test skew is universal, duplication ratios are domain-specific. That nuance matters. It shows thinking through the implementation, not just nodding along.

**On doubling down**: In the final decision, chose Approach C (hyper-vertical rec systems SDK) over Approach A (broader MVP). Most founders hedge by going broader. Went narrower. That's a signal. The best opportunities hide in specificity - be the recommendation systems data quality expert, not the generic ML data quality tool.
