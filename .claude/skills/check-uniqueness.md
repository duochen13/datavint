---
name: check-uniqueness
description: Check for features with many duplicate values
triggers:
  - uniqueness
  - duplicates
  - duplicate values
  - low uniqueness
---

# Check Uniqueness

Analyzes features for low uniqueness - features where most values appear multiple times (many duplicates).

## When to Use
- User asks about uniqueness or duplicate values
- User wants to find features with many repeated values

## Execution

```python
import pandas as pd
import datavint as vint

if 'df' not in locals():
    print("❌ No dataset loaded.")
    exit()

print("Running uniqueness analysis...\n")
stats, issues = vint.profile(df)

uniqueness_issues = [issue for issue in issues if issue.type.value == 'low_uniqueness']

print("="*60)
print("UNIQUENESS ANALYSIS")
print("="*60)

uniqueness_data = []
for feat_name, feat_stats in stats.features.items():
    if feat_stats.uniqueness is not None:
        uniqueness_data.append({
            'feature': feat_name,
            'uniqueness': feat_stats.uniqueness,
        })

uniqueness_data.sort(key=lambda x: x['uniqueness'])

print(f"\n📊 Uniqueness by Feature ({len(uniqueness_data)} features):\n")
for data in uniqueness_data:
    uniq_pct = data['uniqueness'] * 100

    icon = "🔴" if uniq_pct < 10 else ("🟡" if uniq_pct < 30 else "✅")
    bar = "█" * int(uniq_pct / 2)

    print(f"{icon} {data['feature']:<30} {uniq_pct:>5.1f}% unique {bar}")

if uniqueness_issues:
    print(f"\n⚠️  {len(uniqueness_issues)} Low Uniqueness Issue(s):\n")
    for issue in uniqueness_issues:
        print(f"🔴 {issue.feature}: {issue.description}")
else:
    print("\n✅ No low uniqueness issues")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)
print("\nLow uniqueness (<10%) indicates:")
print("  - Many repeated values")
print("  - Potentially limited information content")
print("  - Consider feature engineering or dropping")
print("="*60)
```
