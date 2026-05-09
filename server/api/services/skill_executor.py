"""
Skill Executor Service

Executes pre-defined DataVint skills with consistent output format.
Skills are deterministic, fast, and cost-free compared to LLM generation.
"""

import pandas as pd
from typing import Dict, Any, List
import datavint as vint


class SkillExecutor:
    """Executes DataVint skills and returns formatted results"""

    def __init__(self):
        self.execution_count = {}

    def execute(self, skill_name: str, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Execute a skill and return results.

        Args:
            skill_name: Name of skill to execute (e.g., "check-completeness")
            df: DataFrame to analyze
            **kwargs: Additional parameters for skill execution

        Returns:
            Dict with execution results:
            {
                "success": bool,
                "skill_name": str,
                "output": str,  # Human-readable output
                "data": Dict,   # Structured data
                "error": str | None
            }
        """
        # Track execution
        self.execution_count[skill_name] = self.execution_count.get(skill_name, 0) + 1

        try:
            # Route to appropriate skill handler
            if skill_name == "check-completeness":
                return self._execute_completeness(df)
            elif skill_name == "check-imbalance":
                return self._execute_imbalance(df, kwargs.get('label_col'))
            elif skill_name == "check-cardinality":
                return self._execute_cardinality(df)
            elif skill_name == "check-distinctness":
                return self._execute_distinctness(df)
            elif skill_name == "check-entropy":
                return self._execute_entropy(df)
            elif skill_name == "check-uniqueness":
                return self._execute_uniqueness(df)
            else:
                return {
                    "success": False,
                    "skill_name": skill_name,
                    "output": "",
                    "data": {},
                    "error": f"Unknown skill: {skill_name}"
                }

        except Exception as e:
            return {
                "success": False,
                "skill_name": skill_name,
                "output": "",
                "data": {},
                "error": f"Skill execution failed: {str(e)}"
            }

    def _execute_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute completeness check skill"""
        # Run profiling
        stats, issues = vint.profile(df)

        # Extract completeness issues
        completeness_issues = [issue for issue in issues if issue.type.value == 'low_completeness']

        # Get completeness metrics for all features
        completeness_data = []
        for feat_name, feat_stats in stats.features.items():
            if feat_stats.completeness is not None:
                # Convert to float to avoid NumPy boolean subtract error
                completeness_val = float(feat_stats.completeness)
                completeness_data.append({
                    'feature': feat_name,
                    'completeness': completeness_val,
                    'missing_rate': 1.0 - completeness_val,
                    'missing_count': int((1.0 - completeness_val) * feat_stats.count),
                    'total_count': feat_stats.count
                })

        # Sort by completeness (lowest first)
        completeness_data.sort(key=lambda x: x['completeness'])

        # Format output
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("COMPLETENESS ANALYSIS")
        output_lines.append("=" * 80)
        output_lines.append(f"\nDataset: {df.shape[0]} rows × {df.shape[1]} columns\n")

        if completeness_issues:
            output_lines.append(f"🔴 Found {len(completeness_issues)} features with low completeness:\n")
            for issue in completeness_issues:
                output_lines.append(f"  • {issue.feature}: {issue.description}")
        else:
            output_lines.append("✅ No low completeness issues detected\n")

        output_lines.append("\nCompleteness by feature (lowest first):")
        output_lines.append("-" * 80)
        for item in completeness_data[:10]:  # Top 10
            status = "🔴" if item['completeness'] < 0.95 else "⚠️" if item['completeness'] < 0.98 else "✅"
            output_lines.append(
                f"  {status} {item['feature']:30s}: {item['completeness']*100:5.1f}% complete "
                f"({item['missing_count']:,} missing / {item['total_count']:,} total)"
            )

        if len(completeness_data) > 10:
            output_lines.append(f"\n  ... and {len(completeness_data) - 10} more features")

        output_lines.append("\n" + "=" * 80)
        output_lines.append("RECOMMENDATIONS")
        output_lines.append("=" * 80)

        if completeness_issues:
            output_lines.append("• Consider imputation strategies for features with <95% completeness")
            output_lines.append("• Features with >50% missing may be better dropped")
            output_lines.append("• Check if missingness is random (MCAR) or systematic (MAR/MNAR)")
        else:
            output_lines.append("• Dataset has good completeness - no action needed")

        return {
            "success": True,
            "skill_name": "check-completeness",
            "output": "\n".join(output_lines),
            "data": {
                "completeness_data": completeness_data,
                "issues": [issue.to_dict() for issue in completeness_issues],
                "summary": {
                    "total_features": len(completeness_data),
                    "features_with_issues": len(completeness_issues),
                    "avg_completeness": sum(item['completeness'] for item in completeness_data) / len(completeness_data) if completeness_data else 1.0
                }
            },
            "error": None
        }

    def _execute_imbalance(self, df: pd.DataFrame, label_col: str = None) -> Dict[str, Any]:
        """Execute class imbalance check skill"""
        # Auto-detect label column if not provided
        if label_col is None:
            common_label_names = ['label', 'target', 'y', 'class', 'is_fraud', 'churn', 'clicked', 'converted']
            for col in df.columns:
                col_lower = col.lower()
                if col_lower in common_label_names or col_lower.startswith(('is_', 'has_')):
                    label_col = col
                    break

        if label_col is None:
            return {
                "success": False,
                "skill_name": "check-imbalance",
                "output": "⚠️  Could not auto-detect label column. Please specify label_col parameter.",
                "data": {},
                "error": "No label column found"
            }

        # Run profiling with label column
        stats, issues = vint.profile(df, label_col=label_col)

        # Extract imbalance issues
        imbalance_issues = [issue for issue in issues if issue.type.value == 'class_imbalance']

        # Calculate class distribution
        class_counts = df[label_col].value_counts()
        class_dist = df[label_col].value_counts(normalize=True)

        # Format output
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("CLASS IMBALANCE ANALYSIS")
        output_lines.append("=" * 80)
        output_lines.append(f"\nLabel column: '{label_col}'")
        output_lines.append(f"Dataset: {df.shape[0]} rows\n")

        if imbalance_issues:
            output_lines.append(f"⚠️  Class imbalance detected:\n")
            for issue in imbalance_issues:
                output_lines.append(f"  • {issue.description}")
        else:
            output_lines.append("✅ No significant class imbalance detected\n")

        output_lines.append("\nClass distribution:")
        output_lines.append("-" * 80)
        for class_val, count in class_counts.items():
            pct = class_dist[class_val] * 100
            bar = "█" * int(pct / 2)  # Visual bar
            output_lines.append(f"  {str(class_val):20s}: {count:,} ({pct:.1f}%) {bar}")

        output_lines.append("\n" + "=" * 80)
        output_lines.append("RECOMMENDATIONS")
        output_lines.append("=" * 80)

        min_class_pct = class_dist.min() * 100
        if min_class_pct < 10:
            output_lines.append("• Severe imbalance detected - consider:")
            output_lines.append("  - SMOTE or other oversampling techniques")
            output_lines.append("  - Class weights in model training")
            output_lines.append("  - Stratified sampling for train/test split")
        elif min_class_pct < 30:
            output_lines.append("• Moderate imbalance - consider class weights or stratified sampling")
        else:
            output_lines.append("• Classes are reasonably balanced - standard training should work")

        return {
            "success": True,
            "skill_name": "check-imbalance",
            "output": "\n".join(output_lines),
            "data": {
                "label_col": label_col,
                "class_distribution": {str(k): int(v) for k, v in class_counts.items()},
                "class_percentages": {str(k): float(v) * 100 for k, v in class_dist.items()},
                "issues": [issue.to_dict() for issue in imbalance_issues],
                "summary": {
                    "num_classes": len(class_counts),
                    "majority_class": str(class_counts.idxmax()),
                    "minority_class": str(class_counts.idxmin()),
                    "imbalance_ratio": class_counts.max() / class_counts.min()
                }
            },
            "error": None
        }

    def _execute_cardinality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute cardinality check skill"""
        # Run profiling
        stats, issues = vint.profile(df)

        # Get cardinality for all features
        cardinality_data = []
        for feat_name, feat_stats in stats.features.items():
            n_unique = df[feat_name].nunique()
            cardinality_ratio = n_unique / len(df)
            cardinality_data.append({
                'feature': feat_name,
                'n_unique': n_unique,
                'cardinality_ratio': cardinality_ratio,
                'total_count': len(df)
            })

        # Sort by cardinality (highest first)
        cardinality_data.sort(key=lambda x: x['n_unique'], reverse=True)

        # Format output
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("CARDINALITY ANALYSIS")
        output_lines.append("=" * 80)
        output_lines.append(f"\nDataset: {df.shape[0]} rows × {df.shape[1]} columns\n")

        high_card_features = [x for x in cardinality_data if x['cardinality_ratio'] > 0.9]
        if high_card_features:
            output_lines.append(f"⚠️  Found {len(high_card_features)} features with high cardinality (>90% unique):\n")
            for item in high_card_features:
                output_lines.append(f"  • {item['feature']}: {item['n_unique']:,} unique values ({item['cardinality_ratio']*100:.1f}%)")
        else:
            output_lines.append("✅ No high cardinality features detected\n")

        output_lines.append("\nCardinality by feature (highest first):")
        output_lines.append("-" * 80)
        for item in cardinality_data[:15]:  # Top 15
            status = "🔴" if item['cardinality_ratio'] > 0.9 else "⚠️" if item['cardinality_ratio'] > 0.5 else "✅"
            output_lines.append(
                f"  {status} {item['feature']:30s}: {item['n_unique']:,} unique ({item['cardinality_ratio']*100:5.1f}%)"
            )

        output_lines.append("\n" + "=" * 80)
        output_lines.append("RECOMMENDATIONS")
        output_lines.append("=" * 80)

        if high_card_features:
            output_lines.append("• High cardinality features may need special handling:")
            output_lines.append("  - Consider grouping rare categories")
            output_lines.append("  - Use target encoding or embeddings")
            output_lines.append("  - May indicate ID columns that should be excluded")
        else:
            output_lines.append("• Cardinality levels look reasonable for modeling")

        return {
            "success": True,
            "skill_name": "check-cardinality",
            "output": "\n".join(output_lines),
            "data": {
                "cardinality_data": cardinality_data,
                "summary": {
                    "high_cardinality_count": len(high_card_features),
                    "avg_cardinality_ratio": sum(x['cardinality_ratio'] for x in cardinality_data) / len(cardinality_data)
                }
            },
            "error": None
        }

    def _execute_distinctness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute distinctness check skill - placeholder"""
        return {
            "success": False,
            "skill_name": "check-distinctness",
            "output": "⚠️  Distinctness skill not yet implemented",
            "data": {},
            "error": "Not implemented"
        }

    def _execute_entropy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute entropy check skill - placeholder"""
        return {
            "success": False,
            "skill_name": "check-entropy",
            "output": "⚠️  Entropy skill not yet implemented",
            "data": {},
            "error": "Not implemented"
        }

    def _execute_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute uniqueness check skill - placeholder"""
        return {
            "success": False,
            "skill_name": "check-uniqueness",
            "output": "⚠️  Uniqueness skill not yet implemented",
            "data": {},
            "error": "Not implemented"
        }


# Global executor instance
_executor_instance = None


def get_executor() -> SkillExecutor:
    """Get or create global executor instance"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = SkillExecutor()
    return _executor_instance
