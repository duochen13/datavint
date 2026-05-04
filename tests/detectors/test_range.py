"""
Test suite for NumericRangeDetector.

Validates that:
1. Values above training max are flagged
2. Values below training min are flagged
3. Both above and below violations are detected
4. Values within range are not flagged
5. Returns empty list if no serving_statistics provided
"""

import pytest
import pandas as pd

from datavint.statistics import generate_statistics
from datavint.detectors.range import NumericRangeDetector
from datavint.types import IssueSeverity, IssueType


class TestNumericRangeDetector:
    """Test NumericRangeDetector behavior."""

    def test_no_serving_statistics(self):
        """No issues when serving_statistics not provided."""
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"],
        })
        stats = generate_statistics(df)
        detector = NumericRangeDetector()
        issues = detector.detect(stats)  # No serving_statistics

        assert len(issues) == 0, "Should return empty list without serving_statistics"

    def test_values_within_range(self):
        """Values within training range should not be flagged."""
        df_train = pd.DataFrame({
            "value": [0, 50, 100],  # min=0, max=100
        })
        df_test = pd.DataFrame({
            "value": [25, 75],  # Within [0, 100]
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 0, "Should not flag values within range"

    def test_value_above_training_max(self):
        """Values above training max should be flagged as HIGH."""
        df_train = pd.DataFrame({
            "age": [18, 20, 25, 30, 35],  # max = 35
        })
        df_test = pd.DataFrame({
            "age": [20, 25, 100],  # max = 100 > 35
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1, "Should detect out-of-range value"

        issue = issues[0]
        assert issue.type == IssueType.OUT_OF_RANGE
        assert issue.severity == IssueSeverity.HIGH
        assert issue.feature == "age"
        assert "outside training range" in issue.description.lower()
        assert "100" in issue.description  # Shows max value
        assert "35" in issue.description  # Shows train max

    def test_value_below_training_min(self):
        """Values below training min should be flagged as HIGH."""
        df_train = pd.DataFrame({
            "price": [100, 200, 300, 400, 500],  # min = 100
        })
        df_test = pd.DataFrame({
            "price": [50, 150, 250],  # min = 50 < 100
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1
        issue = issues[0]
        assert "50" in issue.description  # Shows test min
        assert "100" in issue.description  # Shows train min

    def test_values_both_below_and_above(self):
        """Values both below and above range should show both violations."""
        df_train = pd.DataFrame({
            "score": [40, 50, 60, 70, 80],  # min=40, max=80
        })
        df_test = pd.DataFrame({
            "score": [10, 50, 60, 120],  # min=10 < 40, max=120 > 80
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1
        issue = issues[0]
        # Should mention both violations
        assert "10" in issue.description
        assert "120" in issue.description
        assert issue.metric_value == 2.0  # 2 violations (below + above)

    def test_multiple_features_with_violations(self):
        """Multiple numeric features with range violations."""
        df_train = pd.DataFrame({
            "age": [20, 30, 40],
            "income": [50000, 60000, 70000],
            "score": [50, 60, 70],
        })
        df_test = pd.DataFrame({
            "age": [25, 150],  # 150 out of range
            "income": [55000, 65000],  # Within range
            "score": [10, 65],  # 10 out of range
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 2, "Should detect violations in age and score"

        issue_features = {i.feature for i in issues}
        assert "age" in issue_features
        assert "score" in issue_features
        assert "income" not in issue_features  # income is fine

    def test_categorical_features_ignored(self):
        """Categorical features should be ignored (only numeric checked)."""
        df_train = pd.DataFrame({
            "age": [20, 30, 40],
            "country": ["US", "UK", "CA"],
        })
        df_test = pd.DataFrame({
            "age": [25, 35],  # Within range
            "country": ["US", "FR"],  # FR is new, but not range issue
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # Should not flag categorical features
        assert len(issues) == 0

    def test_missing_feature_in_serving(self):
        """Missing feature in serving data should not cause error."""
        df_train = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": [10, 20, 30],
        })
        df_test = pd.DataFrame({
            "col1": [1, 2],  # col2 is missing
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # Should not crash, just skip col2
        assert len(issues) == 0

    def test_type_mismatch_ignored(self):
        """Type mismatches should be ignored (handled by SchemaViolationDetector)."""
        df_train = pd.DataFrame({
            "col1": [1, 2, 3],  # numeric
        })
        df_test = pd.DataFrame({
            "col1": ["a", "b", "c"],  # categorical
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # Type mismatch is skipped
        assert len(issues) == 0

    def test_description_includes_percentage(self):
        """Description should show both absolute and percentage difference."""
        df_train = pd.DataFrame({
            "value": [100, 200, 300],
        })
        df_test = pd.DataFrame({
            "value": [50, 450],  # 50% below min, 50% above max
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = NumericRangeDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1
        # Should include percentage in description
        assert "%" in issues[0].description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
