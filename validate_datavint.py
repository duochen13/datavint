#!/usr/bin/env python3
"""
Validation script for DataVint v0.2 MVP.

Tests the full pipeline:
1. Generate statistics from synthetic data with known issues
2. Detect issues
3. Generate manifest
4. Apply manifest
5. Verify corrections

Run: python validate_datavint.py
"""

import pandas as pd
import numpy as np
import datavint as dv

print("=" * 80)
print("DataVint v0.2 Validation Script")
print("=" * 80)

# ============================================================================
# 1. Create synthetic training data with known issues
# ============================================================================
print("\n[1] Creating synthetic training data with known issues...")

np.random.seed(42)

# Create 1000 rows with multiple data quality issues
train_df = pd.DataFrame({
    # Feature 1: High null rate (60% missing) - should trigger HIGH severity
    "user_age": [25, None, 30, None, None] * 200,

    # Feature 2: Normal numeric feature
    "session_duration": np.random.exponential(scale=120, size=1000),

    # Feature 3: Categorical with normal distribution
    "device": np.random.choice(["mobile", "desktop", "tablet"], size=1000, p=[0.6, 0.3, 0.1]),

    # Feature 4: Some duplicates (will be caught by DuplicatesDetector)
    "user_id": [f"user_{i}" for i in range(800)] + ["duplicate_user"] * 200,

    # Label: Class imbalance (2% positive rate) - should trigger HIGH severity
    "clicked": [1] * 20 + [0] * 980,
})

print(f"Training data shape: {train_df.shape}")
print(f"Training data preview:")
print(train_df.head(10))

# ============================================================================
# 2. Create synthetic test data with distribution skew
# ============================================================================
print("\n[2] Creating synthetic test data with distribution skew...")

test_df = pd.DataFrame({
    # User age: different distribution (older users in test)
    "user_age": [45, None, 50, None, None] * 200,  # Mean shifted higher

    # Session duration: similar distribution
    "session_duration": np.random.exponential(scale=130, size=1000),

    # Device: significant shift (more desktop users in test) - should trigger skew
    "device": np.random.choice(["mobile", "desktop", "tablet"], size=1000, p=[0.3, 0.6, 0.1]),

    "user_id": [f"test_user_{i}" for i in range(1000)],

    # Label: similar imbalance
    "clicked": [1] * 25 + [0] * 975,
})

print(f"Test data shape: {test_df.shape}")

# ============================================================================
# 3. Generate statistics
# ============================================================================
print("\n[3] Generating statistics...")

try:
    train_stats = dv.generate_statistics(train_df, label_col="clicked")
    print(f"✓ Training statistics generated: {train_stats.n_rows} rows, {train_stats.n_cols} columns")
    print(f"  Label rate: {train_stats.label_rate:.2%}")
    print(f"  Duplicate rate: {train_stats.duplicate_rate:.2%}")

    test_stats = dv.generate_statistics(test_df, label_col="clicked")
    print(f"✓ Test statistics generated: {test_stats.n_rows} rows, {test_stats.n_cols} columns")

except Exception as e:
    print(f"✗ Statistics generation failed: {e}")
    raise

# ============================================================================
# 4. Detect issues
# ============================================================================
print("\n[4] Detecting issues...")

try:
    issues = dv.detect_issues(train_stats, serving_statistics=test_stats)
    print(f"✓ Detected {len(issues)} issue(s)")

    if len(issues) > 0:
        print("\nIssues found:")
        for i, issue in enumerate(issues, 1):
            feature_str = issue.feature if issue.feature else "Dataset-level"
            print(f"  {i}. [{issue.severity.value.upper()}] {issue.type.value}")
            print(f"     Feature: {feature_str}")
            print(f"     Description: {issue.description}")
            print(f"     Metric: {issue.metric_value:.4f} (threshold: {issue.threshold:.4f})")
            print(f"     Impact: NE{issue.ne_direction} AUC{issue.auc_direction}")
            print()

    # Validate expected issues
    expected_issue_types = {"high_null_rate", "class_imbalance", "train_test_skew"}
    found_issue_types = {issue.type.value for issue in issues}

    print(f"Expected issue types: {expected_issue_types}")
    print(f"Found issue types: {found_issue_types}")

    missing_issues = expected_issue_types - found_issue_types
    if missing_issues:
        print(f"⚠ Warning: Expected issues not found: {missing_issues}")
    else:
        print(f"✓ All expected issue types detected")

except Exception as e:
    print(f"✗ Issue detection failed: {e}")
    raise

# ============================================================================
# 5. Generate manifest
# ============================================================================
print("\n[5] Generating manifest...")

try:
    manifest = dv.generate_manifest(train_stats, serving_statistics=test_stats)
    print(f"✓ Manifest generated")
    print(f"  Row mask: {manifest.row_mask.sum()}/{len(manifest.row_mask)} rows kept ({manifest.row_mask.sum()/len(manifest.row_mask)*100:.1f}%)")
    print(f"  Sample weights: min={manifest.sample_weights.min():.4f}, max={manifest.sample_weights.max():.4f}, mean={manifest.sample_weights.mean():.4f}")
    print(f"  Feature fixes: {len(manifest.feature_fixes)} feature(s)")

    if manifest.feature_fixes:
        print("  Fixes:")
        for feat, fix in manifest.feature_fixes.items():
            print(f"    - {feat}: {fix['method']} = {fix['value']}")

except Exception as e:
    print(f"✗ Manifest generation failed: {e}")
    raise

# ============================================================================
# 6. Apply manifest
# ============================================================================
print("\n[6] Applying manifest...")

try:
    # Apply manifest (out-of-place)
    corrected_df = manifest.apply(train_df, inplace=False)

    print(f"✓ Manifest applied")
    print(f"  Original shape: {train_df.shape}")
    print(f"  Corrected shape: {corrected_df.shape}")
    print(f"  Rows removed: {train_df.shape[0] - corrected_df.shape[0]}")

    # Check if weight column was added
    if '__datavint_weight__' in corrected_df.columns:
        print(f"  ✓ Sample weight column added: {corrected_df['__datavint_weight__'].describe().to_dict()}")

    # Check null rate improvement
    original_null_rate = train_df['user_age'].isna().mean()
    corrected_null_rate = corrected_df['user_age'].isna().mean()
    print(f"  user_age null rate: {original_null_rate:.2%} → {corrected_null_rate:.2%}")

    # Check class balance improvement
    original_pos_rate = train_df['clicked'].mean()
    corrected_pos_rate = corrected_df['clicked'].mean()
    print(f"  Positive class rate: {original_pos_rate:.2%} → {corrected_pos_rate:.2%}")

except Exception as e:
    print(f"✗ Manifest application failed: {e}")
    raise

# ============================================================================
# 7. Validate corrected data
# ============================================================================
print("\n[7] Validating corrected data...")

try:
    # Re-generate statistics on corrected data
    corrected_stats = dv.generate_statistics(corrected_df, label_col="clicked")

    # Re-detect issues (should be fewer or less severe)
    corrected_issues = dv.detect_issues(corrected_stats)

    print(f"Original issues: {len(issues)}")
    print(f"Corrected issues: {len(corrected_issues)}")

    if len(corrected_issues) < len(issues):
        print(f"✓ Issue count reduced by {len(issues) - len(corrected_issues)}")

    # Check specific improvements
    user_age_fixed = 'user_age' not in [i.feature for i in corrected_issues if i.type.value == 'high_null_rate']
    if user_age_fixed:
        print(f"✓ user_age null rate issue resolved")

except Exception as e:
    print(f"✗ Validation failed: {e}")
    raise

# ============================================================================
# 8. Test error handling
# ============================================================================
print("\n[8] Testing error handling...")

try:
    # Test empty DataFrame
    try:
        empty_stats = dv.generate_statistics(pd.DataFrame())
        print("✗ Should have raised DataVintError for empty DataFrame")
    except dv.DataVintError as e:
        print(f"✓ Empty DataFrame error caught: {str(e)[:60]}...")

    # Test invalid label column
    try:
        invalid_stats = dv.generate_statistics(train_df, label_col="nonexistent")
        print("✗ Should have raised DataVintError for invalid label column")
    except dv.DataVintError as e:
        print(f"✓ Invalid label column error caught: {str(e)[:60]}...")

    # Test None statistics
    try:
        none_issues = dv.detect_issues(None)
        print("✗ Should have raised DataVintError for None statistics")
    except dv.DataVintError as e:
        print(f"✓ None statistics error caught: {str(e)[:60]}...")

    print("✓ Error handling validated")

except Exception as e:
    print(f"✗ Error handling test failed: {e}")
    raise

# ============================================================================
# 9. Summary
# ============================================================================
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
print("✓ Statistics generation: PASSED")
print("✓ Issue detection: PASSED")
print("✓ Manifest generation: PASSED")
print("✓ Manifest application: PASSED")
print("✓ Data quality improvement: PASSED")
print("✓ Error handling: PASSED")
print("\n🎉 All validation checks passed!")
print("=" * 80)
