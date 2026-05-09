---
name: check-cardinality
description: Check for high cardinality features (potential ID columns)
triggers:
  - cardinality
  - high cardinality
  - unique values
  - ID column
  - ID columns
  - distinct values
---

# Check Cardinality

Analyzes categorical features for high cardinality - features where most/all values are unique, which often indicates ID columns or features that need special handling.

## When to Use
- User asks about cardinality
- User wants to find ID columns
- User mentions "too many unique values"
- User asks "which features have high cardinality?"

## What It Does
1. Runs CardinalityDetector via vint.profile()
2. Shows cardinality ratio for all categorical features
3. Identifies features with >90% unique values
4. Provides recommendations for handling high cardinality

## Execution

```python
import pandas as pd
import datavint as vint

# Check if CSV data is available
if 'df' not in locals():
    print("❌ No dataset loaded. Please provide a CSV file path or DataFrame.")
    exit()

print("Running cardinality analysis...\n")

# Run profiling
stats, issues = vint.profile(df)

# Extract cardinality issues
cardinality_issues = [issue for issue in issues if issue.type.value == 'high_cardinality']

print("="*60)
print("CARDINALITY ANALYSIS")
print("="*60)

# Get cardinality data for categorical features
cardinality_data = []
for feat_name, feat_stats in stats.features.items():
    if feat_stats.type == 'categorical' and feat_stats.distinct_count is not None:
        cardinality_ratio = feat_stats.distinct_count / feat_stats.count
        cardinality_data.append({
            'feature': feat_name,
            'distinct_count': feat_stats.distinct_count,
            'total_count': feat_stats.count,
            'cardinality_ratio': cardinality_ratio,
        })

if not cardinality_data:
    print("\n❌ No categorical features found in dataset")
    exit()

# Sort by cardinality ratio (highest first)
cardinality_data.sort(key=lambda x: x['cardinality_ratio'], reverse=True)

# Display all categorical features
print(f"\n📊 Cardinality by Feature ({len(cardinality_data)} categorical features):\n")
for data in cardinality_data:
    card_pct = data['cardinality_ratio'] * 100

    # Categorize cardinality
    if card_pct > 90:
        icon = "🔴"  # Very high - likely ID column
        category = "ID-LIKE"
    elif card_pct > 50:
        icon = "🟡"  # High - needs encoding
        category = "HIGH"
    elif card_pct > 20:
        icon = "⚠️"  # Medium
        category = "MEDIUM"
    else:
        icon = "✅"  # Low - OK
        category = "LOW"

    bar = "█" * int(card_pct / 2)

    print(f"{icon} {data['feature']:<30} {card_pct:>5.1f}% unique {bar}")
    print(f"   [{category:8}] {data['distinct_count']:,} distinct / {data['total_count']:,} total\n")

# Display cardinality issues
if cardinality_issues:
    print(f"⚠️  {len(cardinality_issues)} High Cardinality Issue(s) Detected:\n")
    for issue in cardinality_issues:
        print(f"🔴 {issue.feature}")
        print(f"   {issue.description}")
        print(f"   Cardinality: {issue.metric_value:.1%} (threshold: {issue.threshold:.1%})")
        print()
else:
    print("✅ No high cardinality issues detected")

# Summary
total_categorical = len(cardinality_data)
id_like_features = sum(1 for d in cardinality_data if d['cardinality_ratio'] > 0.9)
high_card_features = sum(1 for d in cardinality_data if 0.5 < d['cardinality_ratio'] <= 0.9)
normal_features = total_categorical - id_like_features - high_card_features

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\nTotal categorical features: {total_categorical}")
print(f"ID-like features (>90% unique): {id_like_features}")
print(f"High cardinality (50-90% unique): {high_card_features}")
print(f"Normal cardinality (<50% unique): {normal_features}")

# Recommendations
print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

if cardinality_issues:
    print("\nFor high cardinality features:\n")

    for data in cardinality_data:
        if data['cardinality_ratio'] > 0.9:
            print(f"🔴 {data['feature']} ({data['cardinality_ratio']:.1%} unique):")
            print(f"   ⚠️  Likely an ID column - consider dropping")
            print(f"   → If needed, use target encoding or hashing")
            print()
        elif data['cardinality_ratio'] > 0.5:
            print(f"🟡 {data['feature']} ({data['cardinality_ratio']:.1%} unique):")
            print(f"   → Use target encoding or embeddings")
            print(f"   → Consider grouping rare categories")
            print(f"   → Or use hash encoding (feature hashing)")
            print()

    print("\n**Encoding Strategies:**")
    print("1. **Target Encoding** - Encode by target variable mean")
    print("2. **Hash Encoding** - Map to fixed-size hash space")
    print("3. **Embeddings** - Learn dense representations (deep learning)")
    print("4. **Grouping** - Combine rare categories into 'Other'")

    print("\n**When to Drop:**")
    print("- >95% unique values (almost certainly an ID)")
    print("- No clear relationship to target variable")
    print("- Can't be meaningfully encoded")
else:
    print("\n✅ All categorical features have reasonable cardinality")
    print("  Standard one-hot encoding should work fine")

print("\n" + "="*60)
```

## Expected Output

```
Running cardinality analysis...

============================================================
CARDINALITY ANALYSIS
============================================================

📊 Cardinality by Feature (4 categorical features):

🔴 user_id                         100.0% unique ██████████████████████████████████████████████████
   [ID-LIKE ] 1,000 distinct / 1,000 total

🟡 email_domain                     45.0% unique ██████████████████████████
   [MEDIUM  ] 450 distinct / 1,000 total

✅ country                           5.0% unique ██
   [LOW     ] 50 distinct / 1,000 total

✅ category                          2.0% unique █
   [LOW     ] 20 distinct / 1,000 total

⚠️  1 High Cardinality Issue(s) Detected:

🔴 user_id
   100.0% of values are unique (potential ID column)
   Cardinality: 100.0% (threshold: 90.0%)

============================================================
SUMMARY
============================================================

Total categorical features: 4
ID-like features (>90% unique): 1
High cardinality (50-90% unique): 0
Normal cardinality (<50% unique): 3

============================================================
RECOMMENDATIONS
============================================================

For high cardinality features:

🔴 user_id (100.0% unique):
   ⚠️  Likely an ID column - consider dropping
   → If needed, use target encoding or hashing

**Encoding Strategies:**
1. **Target Encoding** - Encode by target variable mean
2. **Hash Encoding** - Map to fixed-size hash space
3. **Embeddings** - Learn dense representations (deep learning)
4. **Grouping** - Combine rare categories into 'Other'

**When to Drop:**
- >95% unique values (almost certainly an ID)
- No clear relationship to target variable
- Can't be meaningfully encoded

============================================================
```
