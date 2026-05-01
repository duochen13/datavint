"""
Test suite for SchemaViolationDetector.

Validates that:
1. New categorical values in serving data are flagged
2. Out-of-range numeric values are flagged
3. Matching schemas are not flagged
4. Returns empty list if no serving_statistics provided
"""

import pytest
import pandas as pd

from heptaai.statistics import generate_statistics
from heptaai.detectors.schema import SchemaViolationDetector
from heptaai.types import IssueSeverity, IssueType


class TestSchemaViolationDetector:
    """Test SchemaViolationDetector behavior."""

    def test_no_serving_statistics(self):
        """No issues when serving_statistics not provided."""
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"],
        })
        stats = generate_statistics(df)
        detector = SchemaViolationDetector()
        issues = detector.detect(stats)  # No serving_statistics

        assert len(issues) == 0, "Should return empty list without serving_statistics"

    def test_matching_schemas(self):
        """No issues when train and test schemas match."""
        df_train = pd.DataFrame({
            "age": [25, 30, 35, 40, 45],
            "country": ["US", "UK", "CA", "FR", "DE"],
        })
        df_test = pd.DataFrame({
            "age": [27, 32, 38],
            "country": ["US", "CA", "UK"],  # Same categories
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 0, "Should not flag matching schemas"

    def test_new_categorical_value(self):
        """New categorical value in serving data should be HIGH severity."""
        df_train = pd.DataFrame({
            "country": ["US", "UK", "CA"],
        })
        df_test = pd.DataFrame({
            "country": ["US", "FR"],  # "FR" is new!
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1, "Should detect new categorical value"

        issue = issues[0]
        assert issue.type == IssueType.SCHEMA_VIOLATION
        assert issue.severity == IssueSeverity.HIGH
        assert issue.feature == "country"
        assert "FR" in issue.description or "'FR'" in issue.description
        assert "unexpected value" in issue.description.lower()
        assert issue.metric_value == 1.0  # 1 new value

    def test_multiple_new_categorical_values(self):
        """Multiple new categories should be listed in description."""
        df_train = pd.DataFrame({
            "region": ["NA", "EU"],
        })
        df_test = pd.DataFrame({
            "region": ["NA", "APAC", "LATAM", "MEA"],  # 3 new values
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.metric_value == 3.0  # 3 new values
        # Should show some examples
        assert "APAC" in issue.description or "LATAM" in issue.description or "MEA" in issue.description

    def test_type_mismatch_numeric_to_categorical(self):
        """Type mismatch (numeric → categorical) should be flagged."""
        df_train = pd.DataFrame({
            "age": [18, 20, 25, 30, 35],  # numeric
        })
        df_test = pd.DataFrame({
            "age": ["young", "old", "middle"],  # categorical
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1, "Should detect type mismatch"

        issue = issues[0]
        assert issue.type == IssueType.SCHEMA_VIOLATION
        assert issue.severity == IssueSeverity.HIGH
        assert issue.feature == "age"
        assert "numeric" in issue.description.lower()
        assert "categorical" in issue.description.lower()

    def test_type_mismatch_categorical_to_numeric(self):
        """Type mismatch (categorical → numeric) should be flagged."""
        df_train = pd.DataFrame({
            "status": ["active", "inactive", "pending"],  # categorical
        })
        df_test = pd.DataFrame({
            "status": [1, 0, 2],  # numeric
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 1
        issue = issues[0]
        assert "categorical" in issue.description.lower()
        assert "numeric" in issue.description.lower()

    def test_multiple_features_with_violations(self):
        """Multiple features with different schema violations."""
        df_train = pd.DataFrame({
            "age": [20, 30, 40],
            "country": ["US", "UK", "US"],
            "status": ["active", "inactive", "pending"],
        })
        df_test = pd.DataFrame({
            "age": ["young", "old"],  # Type mismatch
            "country": ["US", "FR"],  # FR is new
            "status": ["active", "pending"],  # No violation
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        assert len(issues) == 2, "Should detect violations in age (type) and country (new value)"

        issue_features = {i.feature for i in issues}
        assert "age" in issue_features
        assert "country" in issue_features
        assert "status" not in issue_features  # status is fine

    def test_missing_feature_in_serving(self):
        """Missing feature in serving data should not cause error."""
        df_train = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        })
        df_test = pd.DataFrame({
            "col1": [1, 2],  # col2 is missing
        })

        train_stats = generate_statistics(df_train)
        test_stats = generate_statistics(df_test)

        detector = SchemaViolationDetector()
        issues = detector.detect(train_stats, serving_statistics=test_stats)

        # Should not crash, just skip col2
        # No schema violation for col1
        assert len(issues) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
