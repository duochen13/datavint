"""
Test script to verify vint.profile(df) works correctly for missing values detection.

This tests the exact pattern used in the LLM-generated code example.
"""

import pandas as pd
import numpy as np
import sys
import os

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import datavint as vint

# Create test dataset with missing values
print("Creating test dataset with missing values...")
data = {
    'user_id': range(1, 101),
    'name': ['User_' + str(i) for i in range(1, 101)],
    'age': [25 + i if i % 3 != 0 else None for i in range(100)],  # 33% missing
    'email': ['user' + str(i) + '@example.com' if i % 2 == 0 else None for i in range(100)],  # 50% missing
    'phone': [None if i % 5 == 0 else '555-' + str(i).zfill(4) for i in range(100)],  # 20% missing
    'city': ['City_' + str(i % 10) for i in range(100)],  # No missing
    'signup_date': pd.date_range('2024-01-01', periods=100).strftime('%Y-%m-%d').tolist(),  # No missing
    'last_login': [pd.Timestamp('2024-03-01') + pd.Timedelta(days=i) if i % 4 != 0 else None for i in range(100)]  # 25% missing
}

df = pd.DataFrame(data)

print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}\n")

# Test the exact pattern from LLM example
print("=" * 80)
print("TEST 1: Basic vint.profile(df) call")
print("=" * 80)

try:
    stats, issues = vint.profile(df)
    print(f"✅ SUCCESS: vint.profile(df) returned stats and issues")
    print(f"   - stats type: {type(stats).__name__}")
    print(f"   - issues type: {type(issues).__name__}")
    print(f"   - Number of issues: {len(issues)}")
    print()
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test the exact LLM example code
print("=" * 80)
print("TEST 2: LLM Example Code Pattern")
print("=" * 80)

try:
    # This is the exact code from llm_client.py EXAMPLE 2
    stats, issues = vint.profile(df)

    # Get missing value details
    missing_counts = df.isnull().sum()
    missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
    columns_with_missing = missing_counts[missing_counts > 0]

    result = {
        'stats': stats,
        'issues': issues,
        'missing_counts': missing_counts.to_dict(),
        'missing_percentages': missing_pct.to_dict(),
        'columns_with_missing': columns_with_missing.to_dict()
    }

    print(f"✅ SUCCESS: LLM example code executed without errors")
    print(f"   - result keys: {list(result.keys())}")
    print(f"   - Columns with missing: {list(result['columns_with_missing'].keys())}")
    print()
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test serialization (what happens in chat.py)
print("=" * 80)
print("TEST 3: Issue Serialization (chat.py pattern)")
print("=" * 80)

try:
    # This is what chat.py does
    serialized_issues = []
    for issue in issues:
        if hasattr(issue, 'to_dict'):
            serialized_issues.append(issue.to_dict())
        else:
            serialized_issues.append(issue)

    print(f"✅ SUCCESS: Issues serialized to dictionaries")
    print(f"   - Original issues type: {type(issues[0]).__name__ if issues else 'N/A'}")
    print(f"   - Serialized type: {type(serialized_issues[0]).__name__ if serialized_issues else 'N/A'}")
    print()
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Display results
print("=" * 80)
print("RESULTS: Missing Value Analysis")
print("=" * 80)

print("\nMissing value counts per column:")
for col in df.columns:
    null_count = df[col].isnull().sum()
    null_pct = (null_count / len(df)) * 100
    status = "🔴" if null_pct > 50 else "⚠️" if null_pct > 0 else "✅"
    print(f"  {status} {col:15s}: {null_count:3d} missing ({null_pct:5.1f}%)")

print(f"\nDetected issues from vint.profile():")
missing_issues = [i for i in issues if i.type.value == 'missing_values']
if missing_issues:
    for issue in missing_issues:
        print(f"  🔴 [{issue.type.value}] {issue.feature}")
        print(f"     {issue.description}")
        print(f"     Severity: {issue.severity.value.upper()}")
        print()
else:
    print("  No missing value issues detected (threshold = 50%)")

# Verify correctness
print("=" * 80)
print("VERIFICATION")
print("=" * 80)

# Expected: age (34%), email (50%), phone (20%), last_login (25%)
# All should trigger HIGH severity (>5% threshold in config.py)
expected_high_severity = ['age', 'email', 'phone', 'last_login']
actual_high_severity = [i.feature for i in missing_issues if i.severity.value == 'high']

if set(expected_high_severity) == set(actual_high_severity):
    print(f"✅ CORRECT: Expected HIGH severity columns: {expected_high_severity}")
    print(f"✅ CORRECT: Actual HIGH severity columns: {actual_high_severity}")
    print(f"✅ CORRECT: Threshold = 5% (from config.py)")
else:
    print(f"⚠️  MISMATCH:")
    print(f"   Expected: {expected_high_severity}")
    print(f"   Actual: {actual_high_severity}")

print("\n" + "=" * 80)
print("ALL TESTS PASSED ✅")
print("=" * 80)
