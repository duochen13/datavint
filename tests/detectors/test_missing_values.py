"""
Test suite for MissingValuesDetector.

Validates that:
1. High null rates (>50%) are flagged as HIGH severity
2. Medium null rates (>20%) are flagged as MEDIUM severity
3. Low null rates (<20%) are not flagged
4. Features with 0% nulls are not flagged
5. Custom thresholds work correctly
"""

import pytest
import pandas as pd

from datavint.statistics import generate_statistics
from datavint.detectors.missing_values import MissingValuesDetector
from datavint.types import IssueSeverity, IssueType


class TestMissingValuesDetector:
    """Test MissingValuesDetector behavior."""

    def test_no_missing_values(self):
        """No issues when all features are complete."""
        df = pd.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": ["a", "b", "c", "d", "e"],
        })
        stats = generate_statistics(df)
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Should not flag features with 0% nulls"

    def test_high_null_rate(self):
        """Features with >50% nulls should be HIGH severity."""
        df = pd.DataFrame({
            "user_age": [25, None, None, None, None],  # 80% null
            "user_id": [1, 2, 3, 4, 5],  # 0% null
        })
        stats = generate_statistics(df)
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1, "Should detect 1 high-null feature"

        issue = issues[0]
        assert issue.type == IssueType.HIGH_NULL_RATE
        assert issue.severity == IssueSeverity.HIGH
        assert issue.feature == "user_age"
        assert issue.metric_value == 0.8  # 80% null
        assert issue.threshold == 0.5  # Default HIGH threshold
        assert issue.ne_direction == "↑"
        assert issue.auc_direction == "↓"
        assert issue.affected_samples == 4  # 4 out of 5 are null

    def test_medium_null_rate(self):
        """Features with >20% but <50% nulls should be MEDIUM severity."""
        df = pd.DataFrame({
            "user_country": [None, None, "US", "CA", "UK"],  # 40% null
            "user_id": [1, 2, 3, 4, 5],  # 0% null
        })
        stats = generate_statistics(df)
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1, "Should detect 1 medium-null feature"

        issue = issues[0]
        assert issue.severity == IssueSeverity.MEDIUM
        assert issue.feature == "user_country"
        assert issue.metric_value == 0.4  # 40% null
        assert issue.threshold == 0.2  # Default MEDIUM threshold

    def test_low_null_rate_not_flagged(self):
        """Features with <20% nulls should not be flagged."""
        df = pd.DataFrame({
            "user_city": [None, "NYC", "LA", "SF", "BOS"],  # 20% null (exactly at threshold)
            "user_id": [1, 2, 3, 4, 5],
        })
        stats = generate_statistics(df)
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        # 20% is NOT > 20%, so should not be flagged
        assert len(issues) == 0, "Should not flag features at exactly 20% null"

    def test_multiple_features_with_nulls(self):
        """Multiple features with different null rates."""
        df = pd.DataFrame({
            "f1": [1, None, None, None, None],  # 80% null → HIGH
            "f2": [1, 2, None, None, 5],  # 40% null → MEDIUM
            "f3": [1, 2, 3, None, 5],  # 20% null → not flagged (exactly at threshold)
            "f4": [1, 2, 3, 4, 5],  # 0% null → not flagged
        })
        stats = generate_statistics(df)
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 2, "Should detect f1 (HIGH) and f2 (MEDIUM)"

        # Check HIGH severity issue
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        assert len(high_issues) == 1
        assert high_issues[0].feature == "f1"

        # Check MEDIUM severity issue
        medium_issues = [i for i in issues if i.severity == IssueSeverity.MEDIUM]
        assert len(medium_issues) == 1
        assert medium_issues[0].feature == "f2"

    def test_custom_thresholds(self):
        """Custom thresholds should override defaults."""
        df = pd.DataFrame({
            "col1": [1, None, None, 4, 5],  # 40% null
        })
        stats = generate_statistics(df)

        # Custom thresholds: 60% for HIGH, 30% for MEDIUM
        detector = MissingValuesDetector(
            config={"thresholds": {"high": 0.6, "medium": 0.3}}
        )
        issues = detector.detect(stats)

        # 40% is > 30% but < 60%, so MEDIUM severity
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.MEDIUM
        assert issues[0].threshold == 0.3

    def test_100_percent_null(self):
        """Features with 100% nulls should be flagged as HIGH."""
        df = pd.DataFrame({
            "all_null": [None, None, None, None, None],
            "label": [0, 1, 0, 1, 0],
        })
        stats = generate_statistics(df, label_col="label")
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert issues[0].feature == "all_null"
        assert issues[0].metric_value == 1.0  # 100% null
        assert issues[0].severity == IssueSeverity.HIGH

    def test_description_formatting(self):
        """Issue description should be human-readable."""
        df = pd.DataFrame({
            "col1": [1, None, None, 4, 5],  # 40% null
        })
        stats = generate_statistics(df)
        detector = MissingValuesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert "40.0%" in issues[0].description
        assert "missing" in issues[0].description.lower()

    def test_serving_statistics_ignored(self):
        """serving_statistics parameter should be ignored (single-dataset issue)."""
        df1 = pd.DataFrame({"col1": [1, None, None, None, None]})  # 80% null
        df2 = pd.DataFrame({"col1": [1, 2, 3, 4, 5]})  # 0% null

        stats1 = generate_statistics(df1)
        stats2 = generate_statistics(df2)

        detector = MissingValuesDetector()

        # Should only check stats1, not stats2
        issues = detector.detect(stats1, serving_statistics=stats2)
        assert len(issues) == 1
        assert issues[0].metric_value == 0.8  # From stats1, not stats2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
