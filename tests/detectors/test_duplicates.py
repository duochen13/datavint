"""
Test suite for DuplicatesDetector.

Validates that:
1. High duplicate rates (>5%) are flagged as HIGH severity
2. Medium duplicate rates (>1%) are flagged as MEDIUM severity
3. Low duplicate rates (<1%) are not flagged
4. Datasets with 0% duplicates are not flagged
5. Custom thresholds work correctly
6. Dataset-level issue (feature=None) is created
"""

import pytest
import pandas as pd

from datavint.statistics import generate_statistics
from datavint.detectors.duplicates import DuplicatesDetector
from datavint.types import IssueSeverity, IssueType


class TestDuplicatesDetector:
    """Test DuplicatesDetector behavior."""

    def test_no_duplicates(self):
        """No issues when dataset has no duplicates."""
        df = pd.DataFrame({
            "user_id": [1, 2, 3, 4, 5],
            "clicks": [10, 20, 30, 40, 50],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Should not flag datasets with 0% duplicates"

    def test_high_duplicate_rate(self):
        """Datasets with >5% duplicates should be HIGH severity."""
        df = pd.DataFrame({
            "user_id": [1, 2, 2, 3, 3, 3, 4, 4, 4, 4],  # 60% duplicates
            "clicks": [5, 10, 10, 15, 15, 15, 20, 20, 20, 20],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1, "Should detect 1 duplicate issue"

        issue = issues[0]
        assert issue.type == IssueType.DUPLICATE_SAMPLES
        assert issue.severity == IssueSeverity.HIGH
        assert issue.feature is None  # Dataset-level issue
        assert issue.metric_value == 0.6  # 60% duplicates
        assert issue.threshold == 0.05  # Default HIGH threshold
        assert issue.ne_direction == "↑"
        assert issue.auc_direction == "↑"
        assert issue.affected_samples == 6  # 6 duplicate rows

    def test_medium_duplicate_rate(self):
        """Datasets with >2% but <5% duplicates should be MEDIUM severity."""
        df = pd.DataFrame({
            "user_id": list(range(100)) + [0, 1, 2],  # 3 duplicates out of 103 = 2.9%
            "clicks": list(range(100)) + [0, 1, 2],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1, "Should detect 1 duplicate issue"

        issue = issues[0]
        assert issue.severity == IssueSeverity.MEDIUM
        assert issue.metric_value == pytest.approx(0.029, rel=0.01)  # ~2.9% duplicates
        assert issue.threshold == 0.02  # Default MEDIUM threshold (2%)

    def test_low_duplicate_rate_not_flagged(self):
        """Datasets with <2% duplicates should not be flagged."""
        df = pd.DataFrame({
            "user_id": list(range(200)) + [0],  # 1 duplicate out of 201 = 0.5%
            "clicks": list(range(200)) + [0],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Should not flag datasets with <2% duplicates"

    def test_custom_thresholds(self):
        """Custom thresholds should override defaults."""
        df = pd.DataFrame({
            "user_id": [1, 2, 3, 4, 4],  # 20% duplicates
            "clicks": [10, 20, 30, 40, 40],
        })
        stats = generate_statistics(df)

        # Custom thresholds: 30% for HIGH, 10% for MEDIUM
        detector = DuplicatesDetector(
            config={"thresholds": {"high": 0.3, "medium": 0.1}}
        )
        issues = detector.detect(stats)

        # 20% is > 10% but < 30%, so MEDIUM severity
        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.MEDIUM
        assert issues[0].threshold == 0.1

    def test_100_percent_duplicates(self):
        """Dataset with all duplicates should be flagged as HIGH."""
        df = pd.DataFrame({
            "user_id": [1, 1, 1, 1, 1],
            "clicks": [10, 10, 10, 10, 10],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert issues[0].severity == IssueSeverity.HIGH
        assert issues[0].metric_value == 0.8  # 4 out of 5 are duplicates

    def test_description_formatting(self):
        """Issue description should be human-readable."""
        df = pd.DataFrame({
            "user_id": [1, 2, 2, 3, 4],  # 20% duplicates
            "clicks": [10, 20, 20, 30, 40],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert "20.0%" in issues[0].description
        assert "duplicate" in issues[0].description.lower()

    def test_serving_statistics_ignored(self):
        """serving_statistics parameter should be ignored (single-dataset issue)."""
        df1 = pd.DataFrame({
            "user_id": [1, 2, 2, 3, 3],  # 40% duplicates
            "clicks": [10, 20, 20, 30, 30],
        })
        df2 = pd.DataFrame({
            "user_id": [1, 2, 3, 4, 5],  # 0% duplicates
            "clicks": [10, 20, 30, 40, 50],
        })

        stats1 = generate_statistics(df1)
        stats2 = generate_statistics(df2)

        detector = DuplicatesDetector()

        # Should only check stats1, not stats2
        issues = detector.detect(stats1, serving_statistics=stats2)
        assert len(issues) == 1
        assert issues[0].metric_value == 0.4  # From stats1, not stats2

    def test_dataset_level_issue(self):
        """Duplicate issue should be dataset-level (feature=None)."""
        df = pd.DataFrame({
            "col1": [1, 2, 2, 3, 4],
            "col2": ["a", "b", "b", "c", "d"],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 1
        assert issues[0].feature is None, "Duplicate issue should be dataset-level"

    def test_edge_case_single_row(self):
        """Single-row dataset has 0% duplicates."""
        df = pd.DataFrame({
            "user_id": [1],
            "clicks": [10],
        })
        stats = generate_statistics(df)
        detector = DuplicatesDetector()
        issues = detector.detect(stats)

        assert len(issues) == 0, "Single-row dataset cannot have duplicates"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
