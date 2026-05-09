---
name: check-distinctness
description: Check for features with few distinct values
triggers:
  - distinctness
  - distinct values
  - few distinct
  - low distinctness
---

# Check Distinctness

Analyzes features for low distinctness - features with few distinct values (many repeated values).

## When to Use
- User asks about distinctness or distinct values
- User wants to find features with few unique categories

## Execution

```python
import pandas as pd
import datavint as vint

if 'df' not in locals():
    print("❌ No dataset loaded.")
    exit()

print("Running distinctness analysis...\n")
stats, issues = vint.profile(df)

distinctness_issues = [issue for issue in issues if issue.type.value == 'high_cardinality' and 'distinct' in issue.description.lower()]

print("="*60)
print("DISTINCTNESS ANALYSIS")
print("="*60)

distinctness_data = []
for feat_name, feat_stats in stats.features.items():
    if feat_stats.distinctness is not None:
        distinctness_data.append({
            'feature': feat_name,
            'distinctness': feat_stats.distinctness,
            'distinct_count': feat_stats.distinct_count,
            'total_count': feat_stats.count,
        })

distinctness_data.sort(key=lambda x: x['distinctness'])

print(f"\n📊 Distinctness by Feature ({len(distinctness_data)} features):\n")
for data in distinctness_data:
    dist_pct = data['distinctness'] * 100

    icon = "🔴" if dist_pct < 10 else ("🟡" if dist_pct < 30 else "✅")
    bar = "█" * int(dist_pct / 2)

    print(f"{icon} {data['feature']:<30} {dist_pct:>5.1f}% distinct {bar}")
    print(f"   ({data['distinct_count']:,} distinct / {data['total_count']:,} total)\n")

if distinctness_issues:
    print(f"⚠️  {len(distinctness_issues)} Low Distinctness Issue(s):\n")
    for issue in distinctness_issues:
        print(f"🔴 {issue.feature}: {issue.description}")
else:
    print("\n✅ No low distinctness issues")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)
print("\nLow distinctness (<10%) indicates:")
print("  - Very few distinct values (e.g., 2-3 categories)")
print("  - Could be boolean or near-boolean feature")
print("  - Consider if this provides enough information")
print("="*60)
```
