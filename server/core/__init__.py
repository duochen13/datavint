"""
DataVint: Data Quality Detection & Optimization for ML

A lightweight SDK for detecting and fixing data quality issues in ML datasets.

Public API (v0.2):
    Detection:
    - profile_dataset: Quick dataset overview before quality checks
    - compare_datasets: Compare train vs test datasets side-by-side
    - generate_statistics: Compute dataset statistics
    - detect_issues: Run all detectors on statistics
    - display_issues: Pretty-print detected issues

    Optimization (NEW in v0.2):
    - generate_manifest: Generate data quality manifest from statistics
    - generate_manifest_from_path: Single-pass manifest generation from CSV
    - Manifest: Data quality manifest (row_mask, sample_weights, feature_fixes)

    Configuration:
    - config: Global configuration for detection thresholds

    Types:
    - DatasetStatistics: Statistics dataclass
    - Issue: Issue dataclass
    - DataVintError: Base exception for all DataVint errors
"""

from .profiling import profile_dataset, compare_datasets
from .statistics import generate_statistics
from .issues import detect_issues, display_issues
from .manifest import Manifest, generate_manifest, generate_manifest_from_path
from .types import DatasetStatistics, Issue, IssueSeverity, IssueType, DataVintError
from .config import config

__version__ = "0.2.0"

__all__ = [
    # Detection (v0.1)
    "profile_dataset",
    "compare_datasets",
    "generate_statistics",
    "detect_issues",
    "display_issues",
    # Optimization (v0.2)
    "Manifest",
    "generate_manifest",
    "generate_manifest_from_path",
    # Configuration
    "config",
    # Types
    "DatasetStatistics",
    "Issue",
    "IssueSeverity",
    "IssueType",
    "DataVintError",
]
