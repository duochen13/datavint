"""
DataVint API - Experiment Lineage Routes

Provides endpoints for retrieving experiment versioning data:
- Data commits (dataset versions)
- Model runs (training experiments)
- Lineage connections (data → model relationships)
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Dict, List, Optional
from datetime import datetime

router = APIRouter()


# TODO: Replace with actual database queries when metadata store is implemented
def get_experiment_lineage_mock(experiment_id: str) -> Dict:
    """
    Mock data for experiment lineage visualization.

    In production, this will query:
    - SQLite metadata store for data_commits and model_runs tables
    - MLflow database for experiment metadata
    - Content-based hashes for DataFrame versioning

    Args:
        experiment_id: Unique identifier for the experiment

    Returns:
        Dict containing dataCommits, modelRuns, and connections
    """
    # Mock data matching the frontend structure
    data = {
        "experimentId": experiment_id,
        "dataCommits": [
            {
                "id": "D1",
                "message": "fix user feature coverage",
                "hash": "a3f9d2c",
                "rowCount": 1200000,
                "timestamp": datetime.now().isoformat(),
            },
            {
                "id": "D0",
                "message": "dedup interactions",
                "hash": "7b2e8f1",
                "rowCount": 1500000,
                "timestamp": datetime.now().isoformat(),
            },
        ],
        "modelRuns": [
            {
                "id": "M2.2",
                "dataCommitId": "D1",
                "message": "sample_rate=0.6",
                "metrics": {
                    "NE": {"value": 0.867, "quality": "good"},
                    "CTR": {"value": 0.0058, "quality": "good"},
                    "lr": {"value": 0.005, "quality": "neutral"},
                    "coverage": {"value": "94%", "quality": "good"},
                },
                "timestamp": datetime.now().isoformat(),
                "best": True,
                "sweep": {"id": 2, "name": "Sample Rate (from D1, lr=0.005)"},
            },
            {
                "id": "M2.1",
                "dataCommitId": "D1",
                "message": "sample_rate=0.4",
                "metrics": {
                    "NE": {"value": 0.841, "quality": "ok"},
                    "CTR": {"value": 0.0051, "quality": "ok"},
                    "lr": {"value": 0.005, "quality": "neutral"},
                    "coverage": {"value": "89%", "quality": "ok"},
                },
                "timestamp": datetime.now().isoformat(),
                "sweep": {"id": 2, "name": "Sample Rate (from D1, lr=0.005)"},
            },
            {
                "id": "M2",
                "dataCommitId": "D0",
                "message": "lr=0.005 ← selected for Sweep 2",
                "metrics": {
                    "NE": {"value": 0.856, "quality": "good"},
                    "CTR": {"value": 0.0053, "quality": "good"},
                },
                "timestamp": datetime.now().isoformat(),
                "sweepWinner": True,
                "sweep": {"id": 1, "name": "Learning Rate (from D0)"},
            },
            {
                "id": "M3",
                "dataCommitId": "D0",
                "message": "lr=0.010",
                "metrics": {
                    "NE": {"value": 0.823, "quality": "ok"},
                    "CTR": {"value": 0.0047, "quality": "neutral"},
                },
                "timestamp": datetime.now().isoformat(),
                "sweep": {"id": 1, "name": "Learning Rate (from D0)"},
            },
            {
                "id": "M1",
                "dataCommitId": "D0",
                "message": "lr=0.020",
                "metrics": {
                    "NE": {"value": 0.801, "quality": "bad"},
                    "CTR": {"value": 0.0042, "quality": "neutral"},
                },
                "timestamp": datetime.now().isoformat(),
                "sweep": {"id": 1, "name": "Learning Rate (from D0)"},
            },
            {
                "id": "M0",
                "dataCommitId": "D0",
                "message": "lr=0.030",
                "metrics": {
                    "NE": {"value": 0.788, "quality": "bad"},
                    "CTR": {"value": 0.0039, "quality": "neutral"},
                },
                "timestamp": datetime.now().isoformat(),
                "sweep": {"id": 1, "name": "Learning Rate (from D0)"},
            },
        ],
        "connections": {
            "D1": ["M2.2", "M2.1"],
            "D0": ["M3", "M2", "M1", "M0"],
        },
    }

    return data


@router.get("/experiments/{experiment_id}/lineage")
async def get_experiment_lineage(
    experiment_id: str = Path(..., description="Unique experiment identifier")
):
    """
    Get experiment lineage data including data commits, model runs, and connections.

    This endpoint returns the complete lineage graph for an experiment:
    - Data commits: versions of the training dataset
    - Model runs: training experiments with metrics
    - Connections: which data version was used for which model runs

    Args:
        experiment_id: The unique identifier for the experiment

    Returns:
        JSON object with dataCommits, modelRuns, and connections

    Raises:
        HTTPException: 404 if experiment not found
    """
    # TODO: Query actual database when implemented
    # For now, return mock data for any experiment_id
    try:
        data = get_experiment_lineage_mock(experiment_id)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch experiment lineage: {str(e)}"
        )


@router.get("/experiments")
async def list_experiments():
    """
    List all available experiments.

    TODO: Implement when metadata store is ready.

    Returns:
        List of experiment summaries
    """
    # Mock response for now
    return {
        "experiments": [
            {
                "id": "test_learning_rate_experiment",
                "name": "Learning Rate Optimization",
                "description": "Sweep learning rates and sample rates",
                "createdAt": datetime.now().isoformat(),
                "dataCommits": 2,
                "modelRuns": 6,
            }
        ]
    }
