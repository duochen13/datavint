"""
Test suite for histogram storage approach.

Validates that:
1. Histograms are stored correctly during statistics generation
2. JS divergence can be computed from stored histograms
3. Results match raw data computation
4. Statistics are serializable
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from heptaai.statistics import generate_statistics
from heptaai.utils.divergence import js_divergence_categorical, js_divergence_numeric
from heptaai.types import DatasetStatistics


# Fixture: Path to test data
@pytest.fixture
def movielens_train_path():
    """Path to MovieLens training data."""
    return Path("/Users/duochen/Desktop/career/heptaAI/playground/raw_data/movielens_train.csv")


@pytest.fixture
def movielens_test_path():
    """Path to MovieLens test data."""
    return Path("/Users/duochen/Desktop/career/heptaAI/playground/raw_data/movielens_test.csv")


@pytest.fixture
def train_stats(movielens_train_path):
    """Generate statistics from training data."""
    if not movielens_train_path.exists():
        pytest.skip(f"Test data not found: {movielens_train_path}")
    return generate_statistics(movielens_train_path, label_col="label")


@pytest.fixture
def test_stats(movielens_test_path):
    """Generate statistics from test data."""
    if not movielens_test_path.exists():
        pytest.skip(f"Test data not found: {movielens_test_path}")
    return generate_statistics(movielens_test_path, label_col="label")


class TestHistogramStorage:
    """Test histogram storage during statistics generation."""

    def test_numeric_histogram_stored(self, train_stats):
        """Verify histogram is stored for numeric features."""
        # Check that 'rating' feature exists and has histogram
        assert "rating" in train_stats.features, "rating feature not found"

        rating_stats = train_stats.features["rating"]
        assert rating_stats.type == "numeric"
        assert rating_stats.histogram is not None, "Histogram not stored for numeric feature"

        # Verify histogram structure
        hist = rating_stats.histogram
        assert "counts" in hist, "Histogram missing 'counts'"
        assert "edges" in hist, "Histogram missing 'edges'"
        assert len(hist["counts"]) == 20, f"Expected 20 bins, got {len(hist['counts'])}"
        assert len(hist["edges"]) == 21, f"Expected 21 edges, got {len(hist['edges'])}"

    def test_categorical_histogram_stored(self, train_stats):
        """Verify histogram is stored for categorical features."""
        # Check that 'genre' feature exists and has histogram
        assert "genre" in train_stats.features, "genre feature not found"

        genre_stats = train_stats.features["genre"]
        assert genre_stats.type == "categorical"
        assert genre_stats.histogram is not None, "Histogram not stored for categorical feature"

        # Verify histogram structure
        hist = genre_stats.histogram
        assert hist.get("type") == "categorical", "Histogram type not marked as categorical"
        assert "value_counts" in hist, "Histogram missing 'value_counts'"
        assert len(hist["value_counts"]) > 0, "Value counts is empty"

    def test_histogram_bins_match_data_range(self, train_stats):
        """Verify histogram bins span the data range correctly."""
        rating_stats = train_stats.features["rating"]
        hist = rating_stats.histogram

        edges = hist["edges"]
        assert edges[0] <= rating_stats.min, "First bin edge should be <= min value"
        assert edges[-1] >= rating_stats.max, "Last bin edge should be >= max value"


class TestJSDivergenceFromHistograms:
    """Test JS divergence computation from stored histograms."""

    def test_numeric_js_divergence_matches_raw(self, movielens_train_path, movielens_test_path, train_stats, test_stats):
        """JS divergence from histograms should match raw data computation."""
        # Load raw data for comparison
        train_df = pd.read_csv(movielens_train_path)
        test_df = pd.read_csv(movielens_test_path)

        # Method 1: JS divergence from raw data
        js_from_raw = js_divergence_numeric(train_df["rating"], test_df["rating"], bins=20)

        # Method 2: JS divergence from stored histograms
        train_hist = train_stats.features["rating"].histogram
        test_hist = test_stats.features["rating"].histogram

        # Reconstruct distributions from histograms
        from scipy.spatial.distance import jensenshannon
        train_counts = np.array(train_hist["counts"])

        # Bin test data using train edges
        test_counts, _ = np.histogram(test_df["rating"].dropna(), bins=train_hist["edges"])

        # Normalize
        train_dist = train_counts / train_counts.sum()
        test_dist = test_counts / test_counts.sum()

        js_from_histogram = float(jensenshannon(train_dist, test_dist) ** 2)

        # Should match closely (allowing small floating point differences)
        assert abs(js_from_raw - js_from_histogram) < 0.001, \
            f"JS divergence mismatch: raw={js_from_raw:.6f}, histogram={js_from_histogram:.6f}"

    def test_categorical_js_divergence_matches_raw(self, movielens_train_path, movielens_test_path, train_stats, test_stats):
        """JS divergence for categorical features should be exact."""
        # Load raw data
        train_df = pd.read_csv(movielens_train_path)
        test_df = pd.read_csv(movielens_test_path)

        # Method 1: From raw data
        js_from_raw = js_divergence_categorical(train_df["genre"], test_df["genre"])

        # Method 2: From stored value counts
        train_value_counts = train_stats.features["genre"].histogram["value_counts"]
        test_value_counts = test_stats.features["genre"].histogram["value_counts"]

        all_values = sorted(set(train_value_counts.keys()) | set(test_value_counts.keys()))
        train_counts = np.array([train_value_counts.get(v, 0) for v in all_values], dtype=float)
        test_counts = np.array([test_value_counts.get(v, 0) for v in all_values], dtype=float)

        from scipy.spatial.distance import jensenshannon
        train_dist = train_counts / train_counts.sum()
        test_dist = test_counts / test_counts.sum()
        js_from_histogram = float(jensenshannon(train_dist, test_dist) ** 2)

        # Categorical should be EXACT (no binning approximation)
        assert abs(js_from_raw - js_from_histogram) < 1e-9, \
            f"Categorical JS should be exact: raw={js_from_raw:.9f}, histogram={js_from_histogram:.9f}"


class TestStatisticsSerialization:
    """Test that statistics can be serialized and deserialized."""

    def test_to_dict_serialization(self, train_stats):
        """Statistics should serialize to dict."""
        stats_dict = train_stats.to_dict()

        assert isinstance(stats_dict, dict)
        assert "n_rows" in stats_dict
        assert "n_cols" in stats_dict
        assert "features" in stats_dict
        assert len(stats_dict["features"]) == len(train_stats.features)

    def test_from_dict_deserialization(self, train_stats):
        """Statistics should deserialize from dict."""
        # Serialize
        stats_dict = train_stats.to_dict()

        # Deserialize
        reloaded_stats = DatasetStatistics.from_dict(stats_dict)

        # Verify key fields match
        assert reloaded_stats.n_rows == train_stats.n_rows
        assert reloaded_stats.n_cols == train_stats.n_cols
        assert reloaded_stats.label_col == train_stats.label_col
        assert len(reloaded_stats.features) == len(train_stats.features)

    def test_json_serialization(self, train_stats):
        """Statistics should be JSON-serializable."""
        import json

        stats_dict = train_stats.to_dict()

        # Should not raise exception
        json_str = json.dumps(stats_dict)
        assert len(json_str) > 0

        # Should deserialize back
        loaded_dict = json.loads(json_str)
        reloaded_stats = DatasetStatistics.from_dict(loaded_dict)

        assert reloaded_stats.n_rows == train_stats.n_rows


class TestMemoryEfficiency:
    """Test that histogram approach is memory efficient."""

    def test_statistics_are_compact(self, train_stats):
        """Statistics should be much smaller than raw data."""
        import json

        # Serialize to JSON
        stats_dict = train_stats.to_dict()
        json_str = json.dumps(stats_dict)
        json_size_bytes = len(json_str.encode('utf-8'))

        # JSON should be small (< 10KB for 7 features)
        assert json_size_bytes < 10_000, \
            f"Statistics JSON too large: {json_size_bytes:,} bytes"

        # Confirm it's much smaller than raw data
        # Raw data: 80K rows × 8 cols × ~8 bytes ≈ 5MB
        # Statistics: should be ~3-5KB
        assert json_size_bytes < 100_000, "Statistics should be <100KB"


class TestDataQualityMetrics:
    """Test that duplicate and label statistics are computed correctly."""

    def test_duplicate_statistics_present(self, train_stats):
        """Duplicate count and rate should be computed."""
        assert hasattr(train_stats, "duplicate_count")
        assert hasattr(train_stats, "duplicate_rate")
        assert train_stats.duplicate_count >= 0
        assert 0.0 <= train_stats.duplicate_rate <= 1.0

    def test_label_statistics_present(self, train_stats):
        """Label rate and entropy should be computed when label_col provided."""
        assert train_stats.label_col == "label"
        assert train_stats.label_rate is not None
        assert train_stats.label_entropy is not None
        assert 0.0 <= train_stats.label_rate <= 1.0
        assert train_stats.label_entropy >= 0.0


class TestEdgeCases:
    """Test edge cases in histogram storage."""

    def test_all_null_feature_handled(self):
        """Features with 100% nulls should be handled gracefully."""
        df = pd.DataFrame({
            "all_null": [None, None, None, None, None],
            "label": [0, 1, 0, 1, 0],
        })

        stats = generate_statistics(df, label_col="label")

        # Should not crash
        assert "all_null" in stats.features
        all_null_stats = stats.features["all_null"]
        assert all_null_stats.null_rate == 1.0
        # Histogram might be None or empty for all-null features
        # (implementation handles this gracefully)

    def test_single_value_feature(self):
        """Features with single unique value should work."""
        df = pd.DataFrame({
            "constant": [5.0] * 100,
            "label": [0, 1] * 50,
        })

        stats = generate_statistics(df, label_col="label")

        # Should not crash
        assert "constant" in stats.features
        const_stats = stats.features["constant"]
        assert const_stats.mean == 5.0
        assert const_stats.std == 0.0
        assert const_stats.histogram is not None


if __name__ == "__main__":
    # Allow running directly with: python test_histogram_storage.py
    pytest.main([__file__, "-v"])
