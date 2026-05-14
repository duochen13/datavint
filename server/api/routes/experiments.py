"""
DataVint API - SDK Experiments Integration

Provides endpoints for retrieving SDK experiment tracking data:
- Data commits (dataset versions tracked via datavint.experiment)
- Model runs (training experiments with metrics and params)
- Lineage connections (which data was used for which models)

This reads from ~/.datavint/metadata.db (the SDK database).
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Dict, List, Optional
from pathlib import Path as PathLib
import sqlite3
import json

router = APIRouter()

# Default SDK database path
DEFAULT_METADATA_DB = PathLib.home() / ".datavint" / "metadata.db"


def _get_metadata_db_connection(db_path: Optional[PathLib] = None):
    """Get connection to SDK metadata database."""
    path = db_path or DEFAULT_METADATA_DB
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"SDK database not found at {path}. Run an experiment with datavint.experiment() first."
        )
    return sqlite3.connect(str(path))


def _format_metrics(metrics_json: Optional[str]) -> Dict:
    """
    Format metrics from JSON string to frontend format.

    SDK format: {"accuracy": 0.92, "precision": 0.85}
    Frontend format: {"accuracy": {"value": 0.92, "quality": "good"}, ...}
    """
    if not metrics_json:
        return {}

    try:
        metrics = json.loads(metrics_json)
        formatted = {}

        for key, value in metrics.items():
            # Determine quality based on metric name and value
            quality = "neutral"
            if isinstance(value, (int, float)):
                # For accuracy-like metrics (higher is better)
                if key.lower() in ['accuracy', 'precision', 'recall', 'f1', 'auc']:
                    if value >= 0.90:
                        quality = "good"
                    elif value >= 0.70:
                        quality = "ok"
                    else:
                        quality = "bad"
                # For loss-like metrics (lower is better)
                elif key.lower() in ['loss', 'error', 'mse', 'rmse']:
                    if value <= 0.1:
                        quality = "good"
                    elif value <= 0.3:
                        quality = "ok"
                    else:
                        quality = "bad"

            formatted[key] = {
                "value": value if isinstance(value, (int, float)) else str(value),
                "quality": quality
            }

        return formatted
    except (json.JSONDecodeError, Exception):
        return {}


@router.get("/experiments/list")
async def list_sdk_experiments(limit: int = 50):
    """
    List all experiments tracked via SDK.

    Returns experiment summaries with counts of data commits and model runs.

    Args:
        limit: Maximum number of experiments to return (default 50)

    Returns:
        List of experiments with metadata
    """
    conn = _get_metadata_db_connection()
    cursor = conn.cursor()

    # Get all unique experiments
    cursor.execute("""
        SELECT experiment_id, MAX(timestamp) as latest
        FROM data_commits
        GROUP BY experiment_id
        ORDER BY latest DESC
        LIMIT ?
    """, (limit,))

    experiment_ids = [row[0] for row in cursor.fetchall()]

    experiments = []
    for exp_id in experiment_ids:
        # Count data commits
        cursor.execute(
            "SELECT COUNT(*) FROM data_commits WHERE experiment_id = ?",
            (exp_id,)
        )
        data_commit_count = cursor.fetchone()[0]

        # Count model runs
        cursor.execute(
            "SELECT COUNT(*) FROM model_runs WHERE experiment_id = ?",
            (exp_id,)
        )
        model_run_count = cursor.fetchone()[0]

        # Get latest timestamp
        cursor.execute("""
            SELECT MAX(timestamp)
            FROM model_runs
            WHERE experiment_id = ?
        """, (exp_id,))
        latest_timestamp = cursor.fetchone()[0]

        experiments.append({
            "id": exp_id,
            "name": exp_id.replace("_", " ").title(),
            "dataCommits": data_commit_count,
            "modelRuns": model_run_count,
            "lastUpdated": latest_timestamp
        })

    conn.close()

    return {
        "experiments": experiments,
        "total": len(experiments)
    }


@router.get("/experiments/{experiment_id}/lineage")
async def get_sdk_experiment_lineage(
    experiment_id: str = Path(..., description="Experiment ID from datavint.experiment()")
):
    """
    Get experiment lineage data from SDK database in bipartite graph format.

    Transforms SDK data into the format expected by the frontend LineageGraph component:
    - dataCommits: Dataset versions (content-based hashing)
    - modelRuns: Training experiments with metrics and params
    - connections: Maps data commits to their model runs

    This allows visualizing:
    - Data versioning (D0, D1, D2, ...)
    - Model runs on each data version
    - Hyperparameter sweeps grouped by sweep_id
    - Best models marked with best=True

    Args:
        experiment_id: The experiment ID (e.g., "rec_model_sweep")

    Returns:
        Dict with dataCommits, modelRuns, connections for bipartite graph
    """
    conn = _get_metadata_db_connection()
    cursor = conn.cursor()

    # Get all data commits for this experiment
    cursor.execute("""
        SELECT id, hash, message, row_count, column_count, timestamp, metadata
        FROM data_commits
        WHERE experiment_id = ?
        ORDER BY timestamp ASC
    """, (experiment_id,))

    data_commits_rows = cursor.fetchall()

    if not data_commits_rows:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Experiment '{experiment_id}' not found in SDK database"
        )

    # Get all model runs for this experiment
    cursor.execute("""
        SELECT id, data_commit_id, message, metrics, params, timestamp, best, sweep_id, sweep_name
        FROM model_runs
        WHERE experiment_id = ?
        ORDER BY timestamp ASC
    """, (experiment_id,))

    model_runs_rows = cursor.fetchall()

    conn.close()

    # Transform to frontend format
    data_commits = []
    model_runs = []
    connections = {}

    # Build data commits
    for row in data_commits_rows:
        commit_id = row[0]
        data_commits.append({
            "id": commit_id,
            "message": row[2] or "Data version",
            "hash": row[1][:7],  # Short hash (first 7 chars)
            "rowCount": row[3],
            "columnCount": row[4],
            "timestamp": row[5],
        })
        connections[commit_id] = []

    # Build model runs
    for row in model_runs_rows:
        run_id = row[0]
        data_commit_id = row[1]

        # Parse params for display
        params_json = row[4]
        params_str = ""
        if params_json:
            try:
                params = json.loads(params_json)
                params_str = ", ".join(f"{k}={v}" for k, v in list(params.items())[:2])
            except:
                pass

        # Build model run object
        model_run = {
            "id": run_id,
            "dataCommitId": data_commit_id,
            "message": row[2] or params_str,
            "metrics": _format_metrics(row[3]),
            "timestamp": row[5],
        }

        # Add best flag
        if row[6]:  # best column
            model_run["best"] = True

        # Add sweep info
        if row[7] is not None:  # sweep_id
            model_run["sweep"] = {
                "id": row[7],
                "name": row[8] or f"Sweep {row[7]}"
            }

        model_runs.append(model_run)

        # Add to connections
        if data_commit_id in connections:
            connections[data_commit_id].append(run_id)

    return {
        "experimentId": experiment_id,
        "dataCommits": data_commits,
        "modelRuns": model_runs,
        "connections": connections
    }


@router.get("/experiments/stats")
async def get_sdk_experiments_stats():
    """
    Get aggregate statistics about SDK-tracked experiments.

    Returns:
        Dict with counts, metrics, etc.
    """
    conn = _get_metadata_db_connection()
    cursor = conn.cursor()

    # Count total experiments
    cursor.execute("SELECT COUNT(DISTINCT experiment_id) FROM data_commits")
    total_experiments = cursor.fetchone()[0]

    # Count total data commits
    cursor.execute("SELECT COUNT(*) FROM data_commits")
    total_data_commits = cursor.fetchone()[0]

    # Count total model runs
    cursor.execute("SELECT COUNT(*) FROM model_runs")
    total_model_runs = cursor.fetchone()[0]

    # Count best models
    cursor.execute("SELECT COUNT(*) FROM model_runs WHERE best = 1")
    total_best_models = cursor.fetchone()[0]

    conn.close()

    return {
        "totalExperiments": total_experiments,
        "totalDataCommits": total_data_commits,
        "totalModelRuns": total_model_runs,
        "totalBestModels": total_best_models
    }
