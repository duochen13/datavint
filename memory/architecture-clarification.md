# Architecture Clarification - Detector Directories

**Date**: 2026-05-08

## The Confusion

Two detector directories exist:
- `/datavint/detectors/` - **13 files** (v0.1 + v0.2 enriched detectors)
- `/server/core/detectors/` - **7 files** (v0.1 detectors only - LEGACY)

## Actual Architecture Flow

**Chatbox → API → DataVint Library**

```
User enters prompt in chatbox
    ↓
/server/api/routes/chat.py
    ↓
Imports: import datavint as vint
    ↓
Calls: vint.profile(df)
    ↓
Uses: /datavint/detectors/* (SOURCE OF TRUTH)
```

## Which Routes Use Which Detectors

**Using `/datavint/detectors/` (CORRECT):**
- ✅ `/server/api/routes/chat.py` - chatbox
- ✅ `/server/api/routes/data.py` - statistics endpoint
- ✅ `/server/api/routes/visualization.py` - visualization
- ✅ `/server/api/routes/code_playground.py` - code playground
- ✅ `/server/api/routes/diagnostics.py` - diagnostics

**Using `/server/core/detectors/` (LEGACY):**
- ❌ `/server/api/routes/playground.py` - old playground (line 37)

## Recommendation

**DELETE `/server/core/detectors/` entirely** - it's legacy code that's out of sync with the main library.

The only route using it (`playground.py`) should be updated to use `datavint` instead, or removed if it's no longer needed.

## Why This Confusion Exists

The project started with server-side detectors in `/server/core/`, then extracted them into a standalone `datavint` package. The old server-side code wasn't cleaned up.
