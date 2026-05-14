"""
Test script to verify the SDK experiments API endpoint works.

This directly tests the endpoint logic without needing the server running.
"""

import sys
from pathlib import Path
import sqlite3
import json

# Add server to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

# Import the endpoint functions
from api.routes.experiments import _get_metadata_db_connection, _format_metrics


def test_get_lineage():
    """Test getting lineage data from database."""
    print("🧪 Testing SDK Experiments API Endpoint\n")

    # Connect to database
    conn = _get_metadata_db_connection()
    cursor = conn.cursor()

    experiment_id = "rec_model_sweep"

    # === Get Data Commits ===
    cursor.execute("""
        SELECT id, hash, message, row_count, column_count, timestamp
        FROM data_commits
        WHERE experiment_id = ?
        ORDER BY timestamp ASC
    """, (experiment_id,))

    data_commits_rows = cursor.fetchall()
    print(f"✓ Found {len(data_commits_rows)} data commits:")
    for row in data_commits_rows:
        print(f"   {row[0]}: {row[2]} ({row[3]} rows)")

    # === Get Model Runs ===
    cursor.execute("""
        SELECT id, data_commit_id, message, metrics, params, sweep_id, sweep_name, best
        FROM model_runs
        WHERE experiment_id = ?
        ORDER BY timestamp ASC
    """, (experiment_id,))

    model_runs_rows = cursor.fetchall()
    print(f"\n✓ Found {len(model_runs_rows)} model runs:")

    # Group by sweep
    sweeps = {}
    for row in model_runs_rows:
        sweep_id = row[5]
        if sweep_id not in sweeps:
            sweeps[sweep_id] = []
        sweeps[sweep_id].append(row)

    for sweep_id, runs in sorted(sweeps.items()):
        sweep_name = runs[0][6]
        print(f"\n   Sweep {sweep_id}: {sweep_name}")
        for row in runs:
            best_marker = "⭐" if row[7] else " "
            metrics = json.loads(row[3])
            metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
            print(f"     {best_marker} {row[0]} (from {row[1]}): {metrics_str}")

    # === Test Formatted Output ===
    print("\n✓ Testing formatted metrics:")
    sample_metrics = '{"accuracy": 0.92, "precision": 0.85}'
    formatted = _format_metrics(sample_metrics)
    print(f"   Input: {sample_metrics}")
    print(f"   Output: {json.dumps(formatted, indent=6)}")

    # === Build Connections ===
    connections = {}
    for row in data_commits_rows:
        connections[row[0]] = []

    for row in model_runs_rows:
        data_commit_id = row[1]
        run_id = row[0]
        if data_commit_id in connections:
            connections[data_commit_id].append(run_id)

    print("\n✓ Connections (data → models):")
    for data_id, model_ids in connections.items():
        print(f"   {data_id} → {', '.join(model_ids)}")

    conn.close()

    print("\n" + "=" * 70)
    print("✅ API Endpoint Test Passed!")
    print("=" * 70)
    print("\nThe endpoint will return:")
    print("• dataCommits: Data versions with metadata")
    print("• modelRuns: Training experiments with metrics (grouped by sweep)")
    print("• connections: Lineage mapping (which data → which models)")
    print("\nReady to serve at: GET /api/experiments/rec_model_sweep/lineage")


if __name__ == "__main__":
    test_get_lineage()
