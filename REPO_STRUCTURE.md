# HeptaAI Repository Structure

Clean, organized structure for the HeptaAI project.

## 📁 Directory Layout

```
heptaAI/
├── README.md                           # Project overview, quick start
├── .gitignore
├── requirements.txt
├── LICENSE
│
├── heptaai/                            # Core Python package
│   ├── __init__.py                    # Public API exports
│   ├── profiling.py                   # Data profiling (v0.1)
│   ├── statistics.py                  # Statistics generation (v0.1)
│   ├── issues.py                      # Issue detection orchestration (v0.1)
│   ├── types.py                       # Dataclasses (DatasetStatistics, Issue, etc.)
│   ├── config.py                      # Configuration, logging
│   ├── detectors/                     # Issue detectors
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseDetector abstract class
│   │   ├── missing_values.py         # v0.1
│   │   ├── duplicates.py             # v0.1
│   │   ├── schema.py                 # v0.1
│   │   ├── range.py                  # v0.1 (numeric range violations)
│   │   ├── skew.py                   # v0.1 (train-test skew)
│   │   └── imbalance.py              # v0.1 (class imbalance)
│   └── manifest.py                    # v0.2 (coming soon)
│
├── docs/                               # Documentation
│   ├── README.md                      # Docs overview, quick links
│   ├── api/                           # Public API reference
│   │   ├── profiling.md              # Profiling API docs
│   │   └── detectors.md              # Issue detection API docs
│   ├── features/                      # Feature specs & implementation notes
│   │   └── data-profiling.md         # Profiling feature summary
│   └── changelog/                     # Design specs & architecture decisions
│       └── 2026-04-27-heptaai-design.md  # Main design spec
│
├── notebooks/                          # Jupyter notebooks
│   ├── README.md                      # Notebook directory guide
│   ├── GETTING_STARTED.md             # Setup instructions
│   ├── quickstart.ipynb               # 5-minute intro
│   └── data_profiling_demo.ipynb      # Complete profiling guide
│
├── examples/                           # Python code examples
│   ├── demo_profiling.py              # 4 profiling examples
│   └── quick_profile.py               # Simple workflow
│
├── tests/                              # Unit & integration tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── detectors/
│   │   ├── test_missing_values.py
│   │   ├── test_duplicates.py
│   │   ├── test_schema.py
│   │   ├── test_range.py
│   │   ├── test_skew.py
│   │   └── test_imbalance.py
│   └── test_statistics.py
│
├── playground/                         # Development & testing
│   ├── raw_data/
│   │   ├── movielens_train.csv
│   │   ├── movielens_test.csv
│   │   └── movielens_anomalous.csv
│   └── download_movielens.py
│
└── benchmarks/                         # Performance benchmarks
    └── bench_statistics.py
```

## 📚 Documentation Organization

### `docs/` - All Documentation

**Structure:**
```
docs/
├── README.md           # Docs overview, navigation
├── api/               # Public API reference (user-facing)
├── features/          # Feature specs & notes (developer-facing)
└── changelog/         # Product design & architecture decisions
```

**Guidelines:**

**`docs/api/`** - API Reference
- For: End users
- Content: Function signatures, parameters, examples
- Format: Clear, concise, example-driven
- Example: `api/profiling.md`

**`docs/features/`** - Feature Documentation
- For: Developers, contributors
- Content: Implementation details, design decisions, testing status
- Format: Technical, comprehensive
- Example: `features/data-profiling.md`

**`docs/changelog/`** - Design Specs & Architecture
- For: Product planning, architecture decisions
- Content: Vision, roadmap, competitive analysis, design history
- Format: Long-form, strategic, timestamped
- Example: `changelog/2026-04-27-heptaai-design.md`

## 🗂️ File Naming Conventions

**Python modules:** `snake_case.py`
- ✅ `profiling.py`
- ✅ `missing_values.py`
- ❌ `ProfilingAPI.py`

**Documentation:** `kebab-case.md`
- ✅ `data-profiling.md`
- ✅ `getting-started.md`
- ❌ `data_profiling.md`
- ❌ `DataProfiling.md`

**Notebooks:** `snake_case.ipynb`
- ✅ `quickstart.ipynb`
- ✅ `data_profiling_demo.ipynb`

**Examples:** `snake_case.py`
- ✅ `demo_profiling.py`
- ✅ `quick_profile.py`

## 📝 Adding New Features

**Checklist when adding a feature:**

1. **Code:**
   - [ ] Add implementation to `heptaai/`
   - [ ] Export from `heptaai/__init__.py`
   - [ ] Add tests to `tests/`

2. **Documentation:**
   - [ ] Add API docs to `docs/api/`
   - [ ] Add feature summary to `docs/features/`
   - [ ] Update `docs/README.md` with quick links

3. **Examples:**
   - [ ] Add Python example to `examples/`
   - [ ] Add Jupyter notebook to `notebooks/` (optional)

4. **README:**
   - [ ] Update main `README.md` with feature
   - [ ] Add to features list
   - [ ] Update examples

## 🔍 Finding Things

**"I want to use HeptaAI"**
→ Start with `README.md`
→ Then `notebooks/quickstart.ipynb`
→ Reference `docs/api/`

**"I want to understand a feature"**
→ Check `docs/api/` for usage
→ Check `docs/features/` for implementation
→ Check `examples/` for working code

**"I want to understand the product vision"**
→ Read `docs/changelog/2026-04-27-heptaai-design.md`

**"I want to contribute"**
→ Read `README.md` contributing section
→ Check `docs/features/` for existing patterns
→ See `tests/` for testing approach

## 🧹 What Changed (Reorganization)

### Files Moved

```bash
# API docs moved to api/ subdirectory
docs/PROFILING.md  →  docs/api/profiling.md

# Feature summary moved from root to features/
PROFILING_FEATURE_SUMMARY.md  →  docs/features/data-profiling.md
```

### New Files Created

```bash
# Root
README.md                     # Project overview

# Docs
docs/README.md               # Docs navigation

# Notebooks
notebooks/README.md
notebooks/GETTING_STARTED.md
notebooks/quickstart.ipynb
notebooks/data_profiling_demo.ipynb

# Examples
examples/demo_profiling.py
examples/quick_profile.py

# Core
heptaai/profiling.py
```

### Why This Structure?

**Before (messy root):**
```
heptaAI/
├── PROFILING_FEATURE_SUMMARY.md  ← Root cluttered
├── docs/
│   └── PROFILING.md              ← No organization
```

**After (clean organization):**
```
heptaAI/
├── README.md                     ← Project entry point
├── docs/
│   ├── README.md                ← Docs navigation
│   ├── api/                     ← User docs
│   │   └── profiling.md
│   └── features/                ← Dev docs
│       └── data-profiling.md
```

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Easy to navigate
- ✅ Scalable (add more features easily)
- ✅ Professional structure
- ✅ GitHub-friendly

## 🎯 Best Practices

**Keep root clean:**
- Only essential files in root (README, LICENSE, requirements.txt)
- No feature summaries or random docs
- No code files (except setup.py if needed)

**Organize by audience:**
- `docs/api/` → For users
- `docs/features/` → For developers
- `docs/changelog/` → For product planning & architecture history

**Link generously:**
- README links to quickstart
- Docs link to examples
- Examples link to API docs
- Create a web of navigation

**Update docs with code:**
- Don't let docs drift
- Update API docs when changing functions
- Update examples when adding features

## 📊 Directory Size Guidelines

**Keep it manageable:**
- `heptaai/` - Core package (~10-20 files per version)
- `docs/api/` - One file per major API module
- `docs/features/` - One file per major feature
- `notebooks/` - 2-5 high-quality notebooks
- `examples/` - 5-10 focused examples

**Don't:**
- Create deeply nested directories
- Add files without clear purpose
- Duplicate information across files
- Create one-line files

## 🔄 Maintenance

**Weekly:**
- Check for broken links in docs
- Update README if features changed
- Keep notebooks working

**Per release:**
- Update version numbers
- Update CHANGELOG
- Verify all docs are current
- Test all examples

**As needed:**
- Reorganize if structure becomes unwieldy
- Archive old docs to `docs/archive/`
- Consolidate redundant files

---

**Last updated:** 2026-05-02
**Maintained by:** HeptaAI Team
