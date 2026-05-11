# Memory Update System - Demo

This document demonstrates the memory update enforcement system.

## Quick Start

### Adding Memory Entries

Use the helper script to add dated entries:

```bash
# Add a pattern
./.claude/scripts/update-memory.sh patterns "New architectural pattern"

# Add a decision
./.claude/scripts/update-memory.sh decisions "Why we chose approach X"

# Add a gotcha
./.claude/scripts/update-memory.sh gotchas "Watch out for this edge case"

# Add a tip
./.claude/scripts/update-memory.sh tips "Useful command or shortcut"
```

**Output:**
```
✓ Added to patterns.md:
  ## [2026-05-11] New architectural pattern

File: /Users/duochen/Desktop/career/datavint/memory/patterns.md
Open file in editor? (y/n)
```

## Pre-Push Hook Demo

### Scenario 1: Push WITH Memory Updates ✅

```bash
# Make changes and commit with memory update
echo "n" | ./.claude/scripts/update-memory.sh patterns "E2E testing pattern"
git add memory/patterns.md
git commit -m "Document E2E testing pattern"
git push
```

**Output:**
```
═══════════════════════════════════════════════════════════
📚 PRE-PUSH: Memory Update Check
═══════════════════════════════════════════════════════════

✓ Memory files updated in this push:
  - memory/patterns.md

═══════════════════════════════════════════════════════════
✓ Proceeding with push to main
═══════════════════════════════════════════════════════════
```

### Scenario 2: Push WITHOUT Memory Updates ⚠️

```bash
# Make changes without updating memory
git add some-file.js
git commit -m "Fix bug"
git push
```

**Output:**
```
═══════════════════════════════════════════════════════════
📚 PRE-PUSH: Memory Update Check
═══════════════════════════════════════════════════════════

⚠️  WARNING: No memory files updated in this push

You are pushing to main without updating memory/*.md files.
This may cause loss of context in future sessions.

Modified files in this push:
  - some-file.js

Memory files you can update:
  memory/patterns.md   - Coding patterns and architectural decisions
  memory/decisions.md  - Key decisions and their rationale
  memory/gotchas.md    - Common pitfalls and gotchas
  memory/tips.md       - Useful commands and tips

Quick update command:
  ./.claude/scripts/update-memory.sh patterns 'What you learned'

Options:
  [a] Abort push - update memory files first
  [c] Continue anyway - skip memory update (not recommended)
  [e] Edit memory file now

Choose [a/c/e]:
```

#### Option A: Abort and Update

```bash
Choose [a/c/e]: a

✗ Push aborted. Please update memory files.

# Update memory
./.claude/scripts/update-memory.sh decisions "Fixed edge case in validation"
git add memory/decisions.md
git commit -m "Document validation fix decision"
git push
# Now push succeeds with memory update ✓
```

#### Option C: Continue Anyway

```bash
Choose [a/c/e]: c

⚠️  Continuing without memory update...

═══════════════════════════════════════════════════════════
✓ Proceeding with push to main
═══════════════════════════════════════════════════════════
```

#### Option E: Edit Now

```bash
Choose [a/c/e]: e

Which file to edit?
  1) patterns.md
  2) decisions.md
  3) gotchas.md
  4) tips.md

Choose [1-4]: 1

Opening memory/patterns.md...
Tip: Add entries with date like: ## [2026-05-11] Your entry

# Editor opens, you add entry, save and close

Staging memory/patterns.md...

Commit message: Document bug fix pattern

✓ Memory file updated and committed
✓ Continuing with push...
```

## Why This System Exists

### Problem Without Memory Updates

**Session 1:**
- Implement feature X
- Learn that approach Y doesn't work
- Fix with approach Z
- Commit and push
- ❌ Don't document learning

**Session 2 (next day):**
- New Claude Code session
- Try to implement similar feature
- Try approach Y (doesn't remember it failed)
- Waste time debugging same issue
- 😞 Context lost

### Solution With Memory Updates

**Session 1:**
- Implement feature X
- Learn that approach Y doesn't work
- Fix with approach Z
- Try to push → **Pre-push hook triggers**
- Add memory entry: "Approach Y fails because..."
- Commit memory update and push
- ✅ Learning documented

**Session 2 (next day):**
- New Claude Code session
- Memory auto-loads via `.claude/load-memory.sh`
- See entry: "Approach Y fails because..."
- Implement correctly from the start
- 🎉 Context preserved!

## Date Format

All entries use `[YYYY-MM-DD]` format:

```markdown
## [2026-05-11] Entry Title

Details about the entry...
```

**Why dates matter:**
- Plans change over time
- Old decisions may no longer apply
- Shows evolution of the codebase
- Helps identify outdated patterns

**Example:**
```markdown
## [2026-01-15] Use REST API for all endpoints

We chose REST for simplicity and compatibility.

## [2026-05-11] Migrated critical endpoints to GraphQL

Updated high-traffic endpoints to GraphQL for better performance.
REST endpoints remain for backward compatibility.
```

Without dates, these would conflict. With dates, we see the evolution.

## Memory File Types

### patterns.md
**What to add:**
- Architectural patterns
- Code organization strategies
- Design patterns used in the codebase
- Best practices discovered

**Example:**
```markdown
## [2026-05-11] Bipartite Graph for Lineage Visualization

Two-column layout with SVG Bezier curves connecting data commits to model runs.

**Files:**
- `client/src/views/ExperimentView.vue`
- `client/src/components/LineageGraph.vue`
```

### decisions.md
**What to add:**
- Technology choices
- Architectural decisions
- Trade-offs considered
- Why one approach was chosen over another

**Example:**
```markdown
## [2026-05-11] Chose Lowest NE = Best for Rec Systems

**Decision:** Lower NE (Normalized Entropy) indicates better model.

**Rationale:** Industry standard for recommendation systems, matches Meta's metrics.

**Impact:** Updated frontend, backend, and tests.
```

### gotchas.md
**What to add:**
- Bugs that were hard to find
- Configuration issues
- Framework quirks
- Things that tripped you up

**Example:**
```markdown
## [2026-05-11] Router Base Path Must Match Vite Config

**Problem:** Frontend routing failed at /playground/.

**Root Cause:** Vue Router base path didn't match Vite's base.

**Solution:** Keep them in sync:
```javascript
// vite.config.js: base: '/playground/'
// router/index.js: createWebHistory('/playground/')
```
```

### tips.md
**What to add:**
- Useful commands
- Shortcuts
- Development workflows
- Testing commands

**Example:**
```markdown
## [2026-05-11] Run E2E Tests

```bash
python3 tests/e2e/test_playground_page.py
```

Auto-runs when client/ files change via `.claude/hooks/client-change-hook.sh`.
```

## Best Practices

1. **Update before pushing** - Let the hook remind you
2. **Be specific** - Include file paths and code snippets
3. **Use dates** - Prevents conflicts with old context
4. **Keep it actionable** - Write for your future self
5. **Update regularly** - Don't batch updates at session end

## Testing the System

### Test the Helper Script

```bash
# Should show usage help
./.claude/scripts/update-memory.sh

# Should add entry with today's date
echo "n" | ./.claude/scripts/update-memory.sh patterns "Test pattern"

# Verify entry was added
head -10 memory/patterns.md
```

### Test the Pre-Push Hook

```bash
# Create test commit without memory update
echo "test" > test.txt
git add test.txt
git commit -m "Test commit"

# Try to push (hook should warn)
git push
# Choose [a] to abort, [c] to continue, or [e] to edit

# Clean up test
git reset --hard HEAD~1
rm test.txt
```

## Integration with Session Loading

Memory files are automatically loaded at session start:

```bash
# .claude/load-memory.sh loads:
- memory/patterns.md
- memory/decisions.md
- memory/gotchas.md
- memory/tips.md
- All wiki/*.md files
```

This ensures every session starts with full historical context.
