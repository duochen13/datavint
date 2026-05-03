# Gotchas & Things to Remember

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
