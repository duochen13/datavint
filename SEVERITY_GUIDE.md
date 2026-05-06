# Data Quality Severity Levels Guide

## Overview

DataVint analyzes your dataset and reports issues with three severity levels:
- 🔴 **HIGH** - Critical issues that will likely hurt model performance
- 🟡 **MEDIUM** - Important issues that should be addressed
- 🟢 **LOW** - Minor issues to be aware of

---

## Issue Types and Thresholds

### 1. Missing Values 🕳️

**What it checks**: Percentage of null/NaN values in each column

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🔴 HIGH | > 60% missing | Most data is gone - column is nearly useless |
| 🟡 MEDIUM | > 30% missing | Significant data loss - will impact model training |

**Example**:
- Column with 5,000 rows, 3,500 are NaN → 70% missing → HIGH severity
- Column with 5,000 rows, 2,000 are NaN → 40% missing → MEDIUM severity

---

### 2. Duplicate Rows 📋

**What it checks**: Percentage of exact duplicate rows in the dataset

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🔴 HIGH | ≥ 30% duplicates | Nearly 1/3 of data is redundant - severe data leakage risk |
| 🟡 MEDIUM | > 10% and < 30% | Significant redundancy - can bias model training |

**Example**:
- Dataset with 10,000 rows, 3,500 duplicates → 35% → HIGH severity
- Dataset with 10,000 rows, 1,500 duplicates → 15% → MEDIUM severity

---

### 3. High Cardinality 🔢

**What it checks**: For categorical features, ratio of unique values to total rows

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🟢 LOW | > 90% unique | Almost every value is unique - may need special encoding |

**Example**:
- User ID column: 9,500 unique values in 10,000 rows → 95% unique → LOW severity
- This flags features that might be IDs rather than meaningful categorical features

---

### 4. Constant Features ⚠️

**What it checks**: Features with only one unique value

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🟡 MEDIUM | Exactly 1 unique value | Feature has zero variance - provides no information |

**Example**:
- Column "country" but all 10,000 rows have "USA" → MEDIUM severity
- These features should be removed as they don't help the model learn

---

### 5. Class Imbalance ⚖️

**What it checks**: For classification labels, ratio of smallest class to largest class

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🔴 HIGH | < 0.05 (< 5%) | Extreme imbalance - model will ignore minority class |
| 🟡 MEDIUM | < 0.10 (< 10%) | Significant imbalance - needs resampling or weighting |

**Example**:
- Fraud detection: 50 fraud cases, 9,950 normal → ratio = 50/9,950 = 0.005 → HIGH severity
- Churn prediction: 800 churned, 9,200 retained → ratio = 800/9,200 = 0.087 → MEDIUM severity

**How to fix**: Use SMOTE, class weights, or undersampling

---

### 6. Infinite Values ♾️

**What it checks**: Presence of +inf or -inf values in numeric columns

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🔴 HIGH | Any inf values detected | Will crash most ML algorithms or produce NaN results |

**Example**:
- Division by zero created inf values
- Log of zero created -inf values
- These must be handled before training

---

### 7. Outliers 📊

**What it checks**: Percentage of values beyond 3 standard deviations from the mean (z-score > 3)

| Severity | Threshold | Why it matters |
|----------|-----------|----------------|
| 🟢 LOW | > 5% outliers | Unusual distribution - may want to clip or transform |

**Example**:
- Age column: Most values 20-80, but 600 values are 999 (missing data coded as 999)
- Income column: Most values $30k-$200k, but 700 values are $10M+ (real outliers or errors?)

**Note**: Not all outliers are errors - domain expertise required!

---

## Quick Reference Table

| Issue Type | LOW | MEDIUM | HIGH |
|------------|-----|--------|------|
| Missing Values | - | > 30% | > 60% |
| Duplicate Rows | - | 10-30% | ≥ 30% |
| High Cardinality | > 90% | - | - |
| Constant Features | - | 100% same value | - |
| Class Imbalance | - | 5-10% ratio | < 5% ratio |
| Infinite Values | - | - | Any inf detected |
| Outliers (z>3) | > 5% | - | - |

---

## Severity Philosophy

**🔴 HIGH**: Fix before training or your model will fail/perform poorly
**🟡 MEDIUM**: Should fix - will significantly improve model quality
**🟢 LOW**: Nice to address - may provide incremental improvement

---

## Example Analysis Output

```
📊 Summary:
  Total Issues: 5
  🔴 High: 2
  🟡 Medium: 2
  🟢 Low: 1

🔍 Detected Issues:

  1. 🔴 [missing_values] user_age
     65.0% of values are missing
     Severity: HIGH
     → Action: Drop column or impute carefully

  2. 🔴 [infinite_values] purchase_amount
     12 infinite values detected
     Severity: HIGH
     → Action: Replace inf with max value or NaN

  3. 🟡 [class_imbalance] is_fraud
     Label distribution is imbalanced (ratio: 0.08)
     Severity: MEDIUM
     → Action: Use SMOTE or class_weight='balanced'

  4. 🟡 [constant_feature] country
     Feature has only one unique value: USA
     Severity: MEDIUM
     → Action: Drop this column

  5. 🟢 [outliers] income
     7.2% of values are outliers (>3 std)
     Severity: LOW
     → Action: Review domain - may be real or errors
```

---

## Notes

- Thresholds are based on common ML best practices
- Your domain may have different tolerance levels
- Always review issues with business context
- Severity helps prioritize what to fix first
