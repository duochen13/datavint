"""
Dataset Description Generator - LLM-powered dataset summarization

Generates human-readable "About this dataset" descriptions using Claude API.
"""

from anthropic import Anthropic
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DESCRIPTION_PROMPT = """You are a data analyst writing a concise dataset description for a data quality platform.

Given the dataset statistics and issues detected, write a 2-3 sentence description that:
1. Summarizes what the dataset contains (infer from column names)
2. Highlights key statistics (rows, columns, data types)
3. Mentions notable data quality issues if any

Be conversational but precise. Write like you're explaining to a colleague.

Dataset Statistics:
- Rows: {n_rows}
- Columns: {n_cols}
- Column names: {columns}
- Data types: {dtypes}
- Issues detected: {issue_count} ({high_severity} high severity, {medium_severity} medium severity)

Write ONLY the description (no markdown, no headings). Maximum 3 sentences.
"""


async def generate_dataset_description(
    stats: Dict[str, Any],
    issues: list,
    columns: list
) -> Optional[str]:
    """
    Generate human-readable dataset description using Claude API.

    Args:
        stats: Dataset statistics from vint.profile()
        issues: List of issues detected
        columns: Column names

    Returns:
        Generated description string, or None if generation fails

    Example output:
        "This dataset contains customer transaction data with 451,017 records across 23 features,
        including demographics, transaction amounts, and fraud indicators. The dataset has notable
        quality issues with 3 columns showing over 30% missing values and a severe class imbalance
        (98.2% negative class)."
    """
    try:
        # Count severity levels
        high_severity = len([i for i in issues if i.get('severity') == 'HIGH'])
        medium_severity = len([i for i in issues if i.get('severity') == 'MEDIUM'])

        # Prepare column sample (first 10)
        column_sample = ', '.join(columns[:10])
        if len(columns) > 10:
            column_sample += ', ...'

        # Infer data types summary
        dtypes_summary = "mixed" if len(set(c.get('type', 'unknown') for c in stats.get('features', {}).values())) > 1 else "numeric"

        # Build prompt
        prompt = DESCRIPTION_PROMPT.format(
            n_rows=stats.get('n_rows', 0),
            n_cols=stats.get('n_cols', 0),
            columns=column_sample,
            dtypes=dtypes_summary,
            issue_count=len(issues),
            high_severity=high_severity,
            medium_severity=medium_severity
        )

        # Call Claude API (Haiku for cost efficiency)
        message = client.messages.create(
            model="claude-haiku-4-0",  # Haiku for fast + cheap descriptions
            max_tokens=150,
            temperature=0.3,  # Slightly creative but consistent
            messages=[{"role": "user", "content": prompt}],
            timeout=10.0
        )

        description = message.content[0].text.strip()
        logger.info(f"Generated dataset description ({len(description)} chars)")
        return description

    except Exception as e:
        logger.error(f"Description generation failed: {e}")
        return None  # Fallback to auto-generated description in frontend
