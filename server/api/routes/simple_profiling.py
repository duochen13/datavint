"""
Simple profiling endpoint that doesn't require DataVint core
(workaround for NumPy 2.0 compatibility issues)
"""

import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, Query

from ..services.analysis import dataset_cache

router = APIRouter()


def detect_simple_issues(df: pd.DataFrame, label_col: str = None) -> list:
    """
    Simple data quality checks without using DataVint's detect_issues
    """
    issues = []

    # 1. Check for missing values
    for col in df.columns:
        null_rate = df[col].isnull().sum() / len(df)
        if null_rate > 0.6:
            issues.append({
                'type': 'missing_values',
                'feature': col,
                'severity': 'HIGH',
                'metric_value': null_rate,
                'threshold': 0.6,
                'description': f'{null_rate:.1%} of values are missing',
                'impact': {'ne_direction': None, 'auc_direction': None}
            })
        elif null_rate > 0.3:
            issues.append({
                'type': 'missing_values',
                'feature': col,
                'severity': 'MEDIUM',
                'metric_value': null_rate,
                'threshold': 0.3,
                'description': f'{null_rate:.1%} of values are missing',
                'impact': {'ne_direction': None, 'auc_direction': None}
            })

    # 2. Check for duplicate rows
    duplicate_rate = df.duplicated().sum() / len(df)
    if duplicate_rate > 0.1:
        issues.append({
            'type': 'duplicates',
            'feature': None,
            'severity': 'MEDIUM' if duplicate_rate < 0.3 else 'HIGH',
            'metric_value': duplicate_rate,
            'threshold': 0.1,
            'description': f'{duplicate_rate:.1%} of rows are duplicates',
            'impact': {'ne_direction': None, 'auc_direction': None}
        })

    # 3. Check for high cardinality in categorical features
    for col in df.select_dtypes(include=['object']).columns:
        unique_ratio = df[col].nunique() / len(df)
        if unique_ratio > 0.9:
            issues.append({
                'type': 'high_cardinality',
                'feature': col,
                'severity': 'LOW',
                'metric_value': unique_ratio,
                'threshold': 0.9,
                'description': f'{df[col].nunique()} unique values out of {len(df)} rows',
                'impact': {'ne_direction': None, 'auc_direction': None}
            })

    # 4. Check for constant features
    for col in df.columns:
        if df[col].nunique() == 1:
            issues.append({
                'type': 'constant_feature',
                'feature': col,
                'severity': 'MEDIUM',
                'metric_value': 1.0,
                'threshold': 1.0,
                'description': f'Feature has only one unique value: {df[col].iloc[0]}',
                'impact': {'ne_direction': None, 'auc_direction': None}
            })

    # 5. Check for class imbalance (if label column exists)
    if label_col and label_col in df.columns:
        value_counts = df[label_col].value_counts()
        if len(value_counts) >= 2:
            imbalance_ratio = value_counts.min() / value_counts.max()
            if imbalance_ratio < 0.1:
                issues.append({
                    'type': 'class_imbalance',
                    'feature': label_col,
                    'severity': 'HIGH' if imbalance_ratio < 0.05 else 'MEDIUM',
                    'metric_value': imbalance_ratio,
                    'threshold': 0.1,
                    'description': f'Label distribution is imbalanced (ratio: {imbalance_ratio:.2f})',
                    'impact': {'ne_direction': None, 'auc_direction': None}
                })

    # 6. Check for numeric range anomalies
    for col in df.select_dtypes(include=[np.number]).columns:
        if col != label_col:
            # Check for infinite values
            inf_count = np.isinf(df[col]).sum()
            if inf_count > 0:
                issues.append({
                    'type': 'infinite_values',
                    'feature': col,
                    'severity': 'HIGH',
                    'metric_value': inf_count / len(df),
                    'threshold': 0.0,
                    'description': f'{inf_count} infinite values detected',
                    'impact': {'ne_direction': None, 'auc_direction': None}
                })

            # Check for outliers (simple z-score method)
            if df[col].std() > 0:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outlier_rate = (z_scores > 3).sum() / len(df)
                if outlier_rate > 0.05:
                    issues.append({
                        'type': 'outliers',
                        'feature': col,
                        'severity': 'LOW',
                        'metric_value': outlier_rate,
                        'threshold': 0.05,
                        'description': f'{outlier_rate:.1%} of values are outliers (>3 std)',
                        'impact': {'ne_direction': None, 'auc_direction': None}
                    })

    return issues


@router.get("/simple-issues")
async def get_simple_issues(dataset_id: str = Query(..., description="Dataset ID")):
    """
    Get data quality issues using simple pandas-based checks
    (Workaround for DataVint NumPy 2.0 compatibility)
    """
    df, label_col = dataset_cache.get(dataset_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        issues = detect_simple_issues(df, label_col)

        # Count by severity
        severity_count = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for issue in issues:
            severity_count[issue['severity']] += 1

        return {
            'dataset_id': dataset_id,
            'issues': issues,
            'summary': {
                'total': len(issues),
                'high': severity_count['HIGH'],
                'medium': severity_count['MEDIUM'],
                'low': severity_count['LOW']
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze data: {str(e)}")
