---
name: check-imbalance
description: Check dataset for class imbalance issues
triggers:
  - imbalance
  - class imbalance
  - imbalance rate
  - balanced
  - unbalanced
  - class distribution
---

# Check Class Imbalance

Analyzes the dataset for class imbalance issues in the target/label column.

## When to Use
- User asks about imbalance rate
- User wants to check if dataset is balanced
- User asks about class distribution
- User mentions "imbalance" or "balanced"

## What It Does
1. Auto-detects label column (label, target, y, class, is_*, has_*)
2. Runs ClassImbalanceDetector via vint.profile()
3. Returns class distribution and imbalance severity
4. Provides actionable recommendations

## Execution

```python
import pandas as pd
import datavint as vint

# Check if CSV data is available
if 'df' not in locals():
    print("❌ No dataset loaded. Please provide a CSV file path or DataFrame.")
    exit()

# Auto-detect label column
label_col = None
common_label_names = ['label', 'target', 'y', 'class', 'is_fraud', 'churn', 'clicked', 'converted', 'is_', 'has_']
for col in df.columns:
    col_lower = col.lower()
    if col_lower in common_label_names or col_lower.startswith(('is_', 'has_')):
        label_col = col
        break

if not label_col:
    print("❌ No label column detected.")
    print(f"Available columns: {', '.join(df.columns)}")
    print("\nTo manually specify: vint.profile(df, label_col='your_column')")
    exit()

print(f"✓ Detected label column: '{label_col}'\n")

# Run profiling with label column
stats, issues = vint.profile(df, label_col=label_col)

# Extract imbalance issues
imbalance_issues = [issue for issue in issues if issue.type.value == 'class_imbalance']

# Calculate class distribution
class_counts = df[label_col].value_counts()
class_dist = df[label_col].value_counts(normalize=True)

print("="*60)
print("CLASS IMBALANCE ANALYSIS")
print("="*60)

# Display class distribution
print(f"\n📊 Class Distribution ({label_col}):")
for cls, count in class_counts.items():
    pct = class_dist[cls] * 100
    bar = "█" * int(pct / 2)
    print(f"  Class {cls}: {count:,} samples ({pct:.1f}%) {bar}")

print(f"\nTotal samples: {len(df):,}")

# Display imbalance issues
if imbalance_issues:
    print(f"\n⚠️  {len(imbalance_issues)} Imbalance Issue(s) Detected:\n")
    for issue in imbalance_issues:
        severity_icon = "🔴" if issue.severity.value == "high" else "🟡"
        print(f"{severity_icon} [{issue.severity.value.upper()}] {issue.description}")
        print(f"   Positive rate: {issue.metric_value:.2%}")
        print(f"   Threshold: {issue.threshold:.2%}")
else:
    print("\n✅ No class imbalance issues detected")
    print(f"   Dataset appears balanced (positive rate: {stats.label_rate:.2%})")

# Recommendations
print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

if imbalance_issues:
    print("\n1. **Data Collection**")
    print("   - Collect more samples from minority class")
    print("   - Use data augmentation for minority class")

    print("\n2. **Training Techniques**")
    print("   - Use class weights in model training")
    print("   - Try SMOTE or other resampling techniques")
    print("   - Use stratified train/test splits")

    print("\n3. **Evaluation Metrics**")
    print("   - Don't rely on accuracy alone")
    print("   - Use precision, recall, F1-score")
    print("   - Consider PR-AUC instead of ROC-AUC")

    # Calculate recommended sample sizes
    minority_class = class_counts.idxmin()
    majority_class = class_counts.idxmax()
    minority_count = class_counts[minority_class]
    majority_count = class_counts[majority_class]

    print(f"\n4. **Target Sample Sizes (50/50 balance)**")
    print(f"   - Keep {majority_count:,} samples from class {majority_class}")
    print(f"   - Need {majority_count - minority_count:,} more samples from class {minority_class}")
    print(f"   - Or downsample class {majority_class} to {minority_count:,} samples")
else:
    print("\n✓ Dataset is well-balanced")
    print("  No special handling needed for class imbalance")

print("\n" + "="*60)
```

## Expected Output

```
✓ Detected label column: 'is_fraud'

============================================================
CLASS IMBALANCE ANALYSIS
============================================================

📊 Class Distribution (is_fraud):
  Class 0: 995 samples (99.5%) ██████████████████████████████████████████████████
  Class 1: 5 samples (0.5%)

Total samples: 1,000

⚠️  1 Imbalance Issue(s) Detected:

🔴 [HIGH] Positive class rate is 0.50% (target: ~50%)
   Positive rate: 0.50%
   Threshold: 1.00%

============================================================
RECOMMENDATIONS
============================================================

1. **Data Collection**
   - Collect more samples from minority class
   - Use data augmentation for minority class

2. **Training Techniques**
   - Use class weights in model training
   - Try SMOTE or other resampling techniques
   - Use stratified train/test splits

3. **Evaluation Metrics**
   - Don't rely on accuracy alone
   - Use precision, recall, F1-score
   - Consider PR-AUC instead of ROC-AUC

4. **Target Sample Sizes (50/50 balance)**
   - Keep 995 samples from class 0
   - Need 990 more samples from class 1
   - Or downsample class 0 to 5 samples

============================================================
```

## Usage

From command line:
```bash
# With CSV file
claude-code /check-imbalance data.csv

# With existing DataFrame
claude-code /check-imbalance
```

From chatbox:
```
User: "Check the imbalance rate of my dataset"
System: [Invokes /check-imbalance skill]
```
