---
name: check-completeness
description: Check dataset for completeness issues (missing values)
triggers:
  - completeness
  - missing
  - missing values
  - null
  - null values
  - incomplete
---

# Check Completeness

Analyzes the dataset for completeness issues - features with high missing value rates.

## When to Use
- User asks about completeness
- User wants to check missing values
- User asks "which columns have nulls?"
- User mentions "incomplete" or "missing data"

## What It Does
1. Runs CompletenessDetector via vint.profile()
2. Shows completeness percentage for all features
3. Identifies features with low completeness (< 80%)
4. Provides recommendations for handling missing values

## Execution

```python
import pandas as pd
import datavint as vint

# Check if CSV data is available
if 'df' not in locals():
    print("❌ No dataset loaded. Please provide a CSV file path or DataFrame.")
    exit()

print("Running completeness analysis...\n")

# Run profiling
stats, issues = vint.profile(df)

# Extract completeness issues
completeness_issues = [issue for issue in issues if issue.type.value == 'low_completeness']

print("="*60)
print("COMPLETENESS ANALYSIS")
print("="*60)

# Get completeness metrics for all features
completeness_data = []
for feat_name, feat_stats in stats.features.items():
    if feat_stats.completeness is not None:
        completeness_data.append({
            'feature': feat_name,
            'completeness': feat_stats.completeness,
            'missing_rate': 1 - feat_stats.completeness,
            'missing_count': int((1 - feat_stats.completeness) * feat_stats.count),
            'total_count': feat_stats.count
        })

# Sort by completeness (lowest first)
completeness_data.sort(key=lambda x: x['completeness'])

# Display all features
print(f"\n📊 Completeness by Feature ({len(completeness_data)} features):\n")
for data in completeness_data:
    comp_pct = data['completeness'] * 100
    miss_pct = data['missing_rate'] * 100

    # Visual bar
    if comp_pct >= 80:
        bar = "█" * int(comp_pct / 2)
        icon = "✅"
    elif comp_pct >= 50:
        bar = "▓" * int(comp_pct / 2)
        icon = "⚠️"
    else:
        bar = "░" * int(comp_pct / 2)
        icon = "🔴"

    print(f"{icon} {data['feature']:<30} {comp_pct:>5.1f}% complete {bar}")
    print(f"   {'':30} ({data['missing_count']:,} / {data['total_count']:,} missing)\n")

# Display completeness issues
if completeness_issues:
    print(f"⚠️  {len(completeness_issues)} Completeness Issue(s) Detected:\n")
    for issue in completeness_issues:
        severity_icon = "🔴" if issue.severity.value == "high" else "🟡"
        print(f"{severity_icon} [{issue.severity.value.upper()}] {issue.feature}")
        print(f"   {issue.description}")
        print(f"   Completeness: {issue.metric_value:.1%} (threshold: {issue.threshold:.1%})")
        print()
else:
    print("✅ No completeness issues detected")
    print("   All features have acceptable completeness (≥80%)")

# Summary stats
total_features = len(completeness_data)
complete_features = sum(1 for d in completeness_data if d['completeness'] >= 0.8)
incomplete_features = total_features - complete_features

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\nTotal features: {total_features}")
print(f"Complete features (≥80%): {complete_features}")
print(f"Incomplete features (<80%): {incomplete_features}")

avg_completeness = sum(d['completeness'] for d in completeness_data) / total_features
print(f"\nAverage completeness: {avg_completeness:.1%}")

# Recommendations
print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

if completeness_issues:
    print("\nFor features with low completeness:")

    print("\n1. **Imputation Strategies**")
    for data in completeness_data:
        if data['completeness'] < 0.8:
            print(f"   - {data['feature']}:")
            if data['completeness'] >= 0.5:
                print(f"     → Use mean/median imputation (numeric)")
                print(f"     → Use mode imputation (categorical)")
            elif data['completeness'] >= 0.3:
                print(f"     → Consider dropping rows with missing values")
                print(f"     → Or use advanced imputation (KNN, MICE)")
            else:
                print(f"     ⚠️  Consider dropping this feature (too sparse)")

    print("\n2. **Data Collection**")
    print("   - Investigate why data is missing")
    print("   - Fix data collection pipeline if possible")
    print("   - Consider if missingness is informative (MNAR)")

    print("\n3. **Feature Engineering**")
    print("   - Create 'is_missing' indicator features")
    print("   - Useful if missingness correlates with target")
else:
    print("\n✓ Dataset has good completeness")
    print("  No imputation needed")

print("\n" + "="*60)
```

## Expected Output

```
Running completeness analysis...

============================================================
COMPLETENESS ANALYSIS
============================================================

📊 Completeness by Feature (5 features):

✅ feature1                        100.0% complete ██████████████████████████████████████████████████
   (0 / 1,000 missing)

✅ feature2                        100.0% complete ██████████████████████████████████████████████████
   (0 / 1,000 missing)

✅ feature3                         95.0% complete █████████████████████████████████████████████████
   (50 / 1,000 missing)

⚠️ incomplete_col                   30.0% complete ███████████████
   (700 / 1,000 missing)

🔴 very_sparse_col                  5.0% complete ██
   (950 / 1,000 missing)

⚠️  2 Completeness Issue(s) Detected:

🔴 [HIGH] incomplete_col
   Only 30.0% of values are present (70.0% missing)
   Completeness: 30.0% (threshold: 50.0%)

🔴 [HIGH] very_sparse_col
   Only 5.0% of values are present (95.0% missing)
   Completeness: 5.0% (threshold: 50.0%)

============================================================
SUMMARY
============================================================

Total features: 5
Complete features (≥80%): 3
Incomplete features (<80%): 2

Average completeness: 66.0%

============================================================
RECOMMENDATIONS
============================================================

For features with low completeness:

1. **Imputation Strategies**
   - very_sparse_col:
     ⚠️  Consider dropping this feature (too sparse)
   - incomplete_col:
     → Consider dropping rows with missing values
     → Or use advanced imputation (KNN, MICE)

2. **Data Collection**
   - Investigate why data is missing
   - Fix data collection pipeline if possible
   - Consider if missingness is informative (MNAR)

3. **Feature Engineering**
   - Create 'is_missing' indicator features
   - Useful if missingness correlates with target

============================================================
```
