# Gotchas & Things to Remember

## [2026-05-17] Rebranding: Don't Forget Static Assets

**Context**: When rebranding DataVint → NanoML, updated HTML to reference `nanoml-dashboard.png` but forgot to rename the actual image file.

**Problem**:
- Updated `docs/index.html` to reference `nanoml-dashboard.png`
- But image file was still named `datavint-dashboard.png`
- Result: Broken image on website

**Fix**:
```bash
mv docs/datavint-dashboard.png docs/nanoml-dashboard.png
```

**Lesson**: When doing text replacements during rebranding, remember to also:
1. Rename actual asset files (images, fonts, etc.)
2. Check for hardcoded URLs in CSS/JavaScript
3. Update favicons and meta images
4. Test the website locally to catch broken references

**Prevention**:
- After text replacement, grep for old brand name in file names: `find . -name "*datavint*"`
- Check for broken images: open website and inspect network tab for 404s

## [2026-05-14] Frontend router uses /playground/:experimentId not /playground/experiments/:experimentId - correct URL is localhost:5175/playground/titanic_survival

## Gstack

- `/context-save` and `/context-restore` are separate from `/checkpoint`
- Learnings stored in `~/.gstack/projects/{project}/learnings.jsonl`
- Upgrade available: 1.21.1.0 → 1.26.0.0 (not yet applied)

## Validation Files

- New untracked validation files in working directory:
  - `validation/` directory
  - `docs/features/validation.md`
  - `examples/demo_validation.py`
  - `examples/demo_validation_corrupted.py`
## Amazon Dataset Test Results

**Date**: 2026-05-02
**Dataset**: Amazon Electronics (100K reviews, 1.4GB)

### Key Findings

1. **Data Quality**: Very clean - no issues detected
   - No missing values
   - No duplicates
   - All fields populated

2. **Data Leakage Issue**: Using 'rating' as a feature creates leakage
   - Label = (rating >= 4.0)
   - Model achieves perfect AUC=1.0
   - Not a realistic test

3. **Class Imbalance**: 80.7% positive, typical for product reviews

### Recommendations

- Use movielens_anomalous.csv for realistic quality issue testing
- Or inject quality issues into Amazon dataset
- Remove rating feature to avoid leakage


## Training Performance

### Why Validation Training is So Fast (3ms)

**Titanic Demo:**
- Dataset: 712 rows × 7 features (fits in CPU cache)
- Model: LogisticRegression (8 parameters)
- Runs: 1 (no hyperparameter search)
- Time: **3.3 milliseconds**

**Production Reality:**
- Dataset: 10M+ rows × 100+ features
- Model: XGBoost/Neural Net (50K+ parameters)
- Runs: 500+ (grid search + cross-validation)
- Time: **Hours to days**

**Scale Factors:**
- Data: 200,000× larger
- Model: 10,000× more complex
- Runs: 500× more iterations
- Total: ~1,000,000,000× slower

**Key Insight:** Demo is intentionally tiny for fast iteration. Real ML at scale requires distributed training (Spark, Ray, etc.)

## Architecture - Single Source of Truth

### Detector Implementation
- **ONLY** `/datavint/detectors/` - 11 detectors (v0.1 + v0.2 enriched)
- **NEVER** import from `server.core` - removed in 2026-05-08

### API Flow
```
User chatbox → /server/api/routes/chat.py
            → import datavint as vint
            → vint.profile(df)
            → /datavint/statistics.py (computes stats)
            → /datavint/detectors/* (runs all detectors)
            → returns (stats, issues)
```

All routes import `datavint` as a library dependency. No duplicate implementations.

## Common API Errors & Fixes

### "Issue object is not subscriptable" Error

**Fixed**: 2026-05-08 (commit 5c169b0)

**Error Message**: `'Issue' object is not subscriptable`

**Root Cause**:
- `Issue` is a dataclass that only supports attribute access (`issue.type`)
- Frontend expects dictionaries that support bracket notation (`issue['type']`)
- LLM-generated code calls `vint.profile(df)` without `return_dict=True`
- Raw Issue objects were being returned in JSON API responses

**Fix**:
- Convert Issue objects to dictionaries using `issue.to_dict()` in chat.py
- Convert DatasetStatistics objects using `stats.to_dict()` in chat.py
- Added serialization logic at lines 203-221 in server/api/routes/chat.py

**Prevention**:
- Always use `vint.profile(df, return_dict=True)` in API endpoints
- Or manually serialize Issue objects before JSON response

## Import Best Practices

### Use Absolute Imports in Routes Directory

**Fixed**: 2026-05-08 (commit 7667bde)

**Problem**:
- Relative imports (`from ..services.llm_client`) break when file structure changes
- Hard to understand where modules come from
- Refactoring-unfriendly

**Solution**:
- Use absolute imports: `from server.api.services.llm_client`
- Applied to all files in `server/api/routes/` directory

**Benefits**:
- More explicit and easier to understand
- No dependency on file location - safer refactoring
- Consistent import style across all route modules

## Missing Value Detection Thresholds

**Configuration**: `datavint/config.py`

**Default Thresholds**:
- `null_rate_high = 0.05` (5% missing → HIGH severity)
- `null_rate_medium = 0.02` (2% missing → MEDIUM severity)

**Important**: The threshold is **5%, not 50%**. This means:
- Any column with >5% missing values triggers HIGH severity
- Columns with 2-5% missing values trigger MEDIUM severity
- Very strict thresholds for production ML pipelines

**Override Example**:
```python
import datavint as dv

# Use more lenient thresholds
dv.config.null_rate_high = 0.50  # 50% instead of 5%
dv.config.null_rate_medium = 0.20  # 20% instead of 2%

# Now run detection with custom thresholds
stats, issues = dv.profile(df)
```

## NumPy Boolean Subtract Error

**Fixed**: 2026-05-09 (skill_executor.py + datavint/statistics.py)

**Error Message**: `numpy boolean subtract, the '-' operator, is not supported, use the bitwise_xor, the '^' operator, or the logical_xor function instead.`

**Root Causes:**

### 1. Boolean Column Quantile Calculation (PRIMARY FIX)
NumPy 2.0+ cannot calculate quantiles (p25, p50, p75) for boolean dtype columns. When `vint.profile(df)` processes a dataset with boolean columns (e.g., `is_active: bool`), the error occurs during `series.quantile()` calls.

**Fix in `datavint/statistics.py:204`**:
```python
# ❌ BAD - boolean dtypes incorrectly treated as numeric
if pd.api.types.is_numeric_dtype(s):
    # This fails for boolean columns
    p25=float(s_clean.quantile(0.25))

# ✅ GOOD - check boolean dtype first
if pd.api.types.is_bool_dtype(s):
    # Boolean feature - treat as categorical
    # Boolean dtypes can't have quantiles calculated on them in NumPy 2.0+
    top_vals = s_clean.value_counts(normalize=True).head(10).to_dict()
    return FeatureStats(type="categorical", ...)
elif pd.api.types.is_numeric_dtype(s):
    # Now safe to calculate quantiles
    p25=float(s_clean.quantile(0.25))
```

### 2. Arithmetic on NumPy Arrays
In `skill_executor.py`, calculating `missing_rate = 1 - completeness` where `completeness` is a NumPy boolean/array triggers this error.

**Fix**:
```python
# ❌ BAD - Can trigger error with NumPy booleans
missing_rate = 1 - feat_stats.completeness

# ✅ GOOD - Convert to float first
completeness_val = float(feat_stats.completeness)
missing_rate = 1.0 - completeness_val
```

**Where to apply**:
- Always check for boolean dtype before calculating quantiles
- Convert NumPy values to Python `float()` before arithmetic operations
- Applied in: `datavint/statistics.py` (primary), `skill_executor.py` (defensive)

## Hybrid Routing Implementation (2026-05-09)

**Location**: `server/api/services/skill_router.py` + `skill_executor.py`

**Key Decisions**:
- Skills route at 70% confidence threshold (keyword matches)
- Command matches (`/check-*`) get highest confidence (1.0)
- LLM fallback always available if skill execution fails
- Routing metadata included in API response for debugging

**Monitoring**:
- Use `/api/chat/metrics` to track skill vs LLM usage
- Expect 70-90% skill routing for healthy performance
- Cost savings should be 60-80% vs all-LLM approach

**See**: `memory/hybrid-routing.md` for implementation details

## Experiment Tracking Gotchas (2026-05-11)

### 1. Pandas to_json() Doesn't Accept sort_keys Parameter

**Error**: `TypeError: to_json() got an unexpected keyword argument 'sort_keys'`

**Problem**:
```python
# ❌ BAD - sort_keys is not a valid parameter
df.to_json(orient='split', sort_keys=True)
```

**Fix**:
```python
# ✅ GOOD - Sort columns first, then convert to JSON
df_sorted = df[sorted(df.columns)]
json_str = df_sorted.to_json(orient='split')
```

**Where**: `datavint/experiment.py:147` (_compute_dataframe_hash method)

### 2. Vue Error State Blocks Graph Rendering

**Problem**: When API fetch fails, setting `error.value = err.message` causes the error state to persist even after loading mock data. The `v-else-if="error"` template blocks the `v-else` that renders the graph.

**Fix**:
```javascript
// ❌ BAD - Error blocks graph rendering
} catch (err) {
  console.error('Failed to fetch experiment lineage:', err)
  error.value = err.message  // This blocks rendering!
  loadMockData()
}

// ✅ GOOD - Clear error after mock data loads
} catch (err) {
  console.error('Failed to fetch experiment lineage:', err)
  loadMockData()
  error.value = null  // Clear so v-else renders graph
}
```

**Where**: `client/src/views/ExperimentView.vue:39`

### 3. Vite Base Path for Experiments

**Problem**: Setting `base: '/playground/'` in vite.config.js breaks experiment view routing.

**Fix**:
```javascript
// ❌ BAD - Wrong base path
export default defineConfig({
  base: '/playground/',  // Breaks /experiments route
  // ...
})

// ✅ GOOD - Root base path
export default defineConfig({
  base: '/',  // Supports all routes
  // ...
})
```

**Where**: `client/vite.config.js:8`

### 4. Vue Router Catch-All for Old URLs

**Problem**: Accessing old URLs like `/playground/` results in "No match found" warnings.

**Fix**: Add catch-all route that redirects to new structure:
```javascript
{
  path: '/:pathMatch(.*)*',
  redirect: '/experiments',
}
```

**Where**: `client/src/router/index.js:32`

### 5. Winner Logic: Metric Directionality Matters

**Context**: Different metrics optimize in different directions.

**Examples**:
- **Lower is better**: NE (Normalized Entropy), loss, error rate
- **Higher is better**: accuracy, AUC, precision, recall

**Implementation**: User's recommendation system uses NE where **lowest = best**. Document this clearly in code comments:
```javascript
// Winner Selection Logic:
//   - Lower NE (Normalized Entropy) = better model performance
//   - Overall best: Lowest NE across all runs
//   - Sweep winner: Lowest NE within that sweep
```

**Where**: `client/src/views/ExperimentView.vue:46`

### 6. Removing Vue Composable Import But Not Usage

**Fixed**: 2026-05-16 (commit 076a508)

**Problem**: When removing unused Vue Router composables from imports, forgot to remove the corresponding variable declaration. This causes a runtime error and blank graph rendering.

**Error Symptoms**:
- Lineage graph area completely black
- No data visualization rendering
- JavaScript error: "useRouter is not defined"
- Silent failure (no error message to user)

**Fix**:
```javascript
// ❌ BAD - Removed from imports but still used
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
// useRouter removed from imports ↑

const route = useRoute()
const router = useRouter()  // ← ERROR: useRouter not imported!
```

```javascript
// ✅ GOOD - Remove both import and usage
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
// router declaration removed ✓
```

**Prevention**:
- When removing imports, search for all usages of that import in the file
- Use IDE "Find Usages" before removing imports
- Run dev server to catch runtime errors immediately

**Where**: `client/src/views/ExperimentView.vue:9`
