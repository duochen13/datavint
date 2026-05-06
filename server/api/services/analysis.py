"""
Analysis service - dataset cache and business logic
"""

import time
from typing import Dict, Optional, Tuple
import pandas as pd


class DatasetCache:
    """
    In-memory cache for uploaded datasets

    Stores datasets temporarily without a database.
    Each dataset has a TTL (time-to-live) of 1 hour.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[pd.DataFrame, Optional[str], float]] = {}
        self._ttl = ttl_seconds

    def store(self, dataset_id: str, df: pd.DataFrame, label_col: Optional[str] = None):
        """Store dataset with timestamp"""
        timestamp = time.time()
        self._cache[dataset_id] = (df, label_col, timestamp)
        self._cleanup()

    def get(self, dataset_id: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Get dataset if it exists and hasn't expired"""
        self._cleanup()

        if dataset_id not in self._cache:
            return None, None

        df, label_col, timestamp = self._cache[dataset_id]

        # Check if expired
        if time.time() - timestamp > self._ttl:
            del self._cache[dataset_id]
            return None, None

        return df, label_col

    def _cleanup(self):
        """Remove expired datasets"""
        current_time = time.time()
        expired_ids = [
            dataset_id
            for dataset_id, (_, _, timestamp) in self._cache.items()
            if current_time - timestamp > self._ttl
        ]
        for dataset_id in expired_ids:
            del self._cache[dataset_id]

    def delete(self, dataset_id: str):
        """Manually delete a dataset"""
        if dataset_id in self._cache:
            del self._cache[dataset_id]

    def size(self) -> int:
        """Get number of cached datasets"""
        self._cleanup()
        return len(self._cache)


# Singleton instance to be shared across all routes
dataset_cache = DatasetCache()
