"""
Statistics generation for datasets.

This module implements the generate_statistics() function, which computes
per-feature statistics and global dataset metrics.
"""

from typing import Union, Optional
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import entropy

from .types import DatasetStatistics, FeatureStats
from .config import logger


def generate_statistics(
    data: Union[str, Path, pd.DataFrame],
    label_col: Optional[str] = None,
) -> DatasetStatistics:
    """
    Generate statistics from dataset.

    Args:
        data: DataFrame or path to CSV file
        label_col: Target column name (None for unsupervised)

    Returns:
        DatasetStatistics dataclass with per-feature and global statistics

    Raises:
        FileNotFoundError: If path doesn't exist
        ValueError: If DataFrame has 0 rows
        KeyError: If label_col not in DataFrame columns

    Example:
        >>> import heptaai as hepta
        >>> stats = hepta.generate_statistics("train.csv", label_col="click")
        >>> print(f"{stats.n_rows:,} rows, {stats.n_cols} columns")
        80,668 rows, 8 columns
    """
    # 1. Load data
    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        logger.info(f"Loading data from {path}")
        df = pd.read_csv(path)
    else:
        df = data.copy()

    # 2. Validation
    if len(df) == 0:
        raise ValueError("Cannot generate statistics from empty DataFrame")

    if label_col and label_col not in df.columns:
        raise KeyError(f"Label column '{label_col}' not found in DataFrame columns")

    logger.info(f"Computing statistics for {len(df):,} rows, {len(df.columns)} columns")

    # 3. Compute duplicate statistics (for DuplicatesDetector)
    duplicate_count = df.duplicated().sum()
    duplicate_rate = duplicate_count / len(df)

    # 4. Compute per-feature stats
    features = {}
    for col in df.columns:
        if col == label_col:
            continue  # Skip label column in feature stats

        features[col] = _compute_feature_stats(df, col)

    # 5. Compute global label statistics (if label_col provided)
    label_rate = None
    label_entropy_val = None
    if label_col:
        label_series = df[label_col]
        # Compute label rate (mean for binary classification)
        label_rate = float(label_series.mean())
        # Compute label entropy
        label_entropy_val = _compute_entropy(label_series)

    logger.info(f"Generated statistics for {len(features)} features")

    return DatasetStatistics(
        n_rows=len(df),
        n_cols=len(df.columns),
        features=features,
        label_col=label_col,
        label_rate=label_rate,
        label_entropy=label_entropy_val,
        duplicate_count=int(duplicate_count),
        duplicate_rate=float(duplicate_rate),
    )


def _compute_feature_stats(df: pd.DataFrame, col: str) -> FeatureStats:
    """
    Compute statistics for a single feature.

    Args:
        df: DataFrame
        col: Column name

    Returns:
        FeatureStats with computed statistics
    """
    s = df[col]

    # Basic stats
    count = len(s)
    null_count = int(s.isna().sum())
    null_rate = null_count / count

    # Type-specific stats
    if pd.api.types.is_numeric_dtype(s):
        # Numeric feature
        s_clean = s.dropna()
        if len(s_clean) > 0:
            # Store histogram for skew detection
            hist_counts, hist_edges = np.histogram(s_clean, bins=20)
            histogram = {
                "counts": hist_counts.tolist(),
                "edges": hist_edges.tolist(),
            }

            return FeatureStats(
                name=col,
                type="numeric",
                count=count,
                null_count=null_count,
                null_rate=null_rate,
                mean=float(s_clean.mean()),
                std=float(s_clean.std()),
                min=float(s_clean.min()),
                max=float(s_clean.max()),
                median=float(s_clean.median()),
                p25=float(s_clean.quantile(0.25)),
                p75=float(s_clean.quantile(0.75)),
                p99=float(s_clean.quantile(0.99)),
                histogram=histogram,
            )
        else:
            # All null
            logger.warning(f"Feature '{col}' has 100% null values")
            return FeatureStats(
                name=col,
                type="numeric",
                count=count,
                null_count=null_count,
                null_rate=null_rate,
            )
    else:
        # Categorical feature
        s_clean = s.dropna()
        top_vals = s_clean.value_counts(normalize=True).head(10).to_dict()

        # For skew detection, store value counts (histogram equivalent for categorical)
        value_counts = s_clean.value_counts().to_dict()
        histogram = {
            "type": "categorical",
            "value_counts": value_counts,
        }

        return FeatureStats(
            name=col,
            type="categorical",
            count=count,
            null_count=null_count,
            null_rate=null_rate,
            unique_count=int(s_clean.nunique()),
            top_values=top_vals,
            histogram=histogram,
        )


def _compute_entropy(series: pd.Series) -> float:
    """
    Compute Shannon entropy of a series.

    Args:
        series: Pandas series (typically label column)

    Returns:
        Shannon entropy value
    """
    value_counts = series.value_counts(normalize=True)
    return float(entropy(value_counts))
