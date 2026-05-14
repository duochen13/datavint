"""
DataVint CLI - ML Execution Waste Control Layer

Command-line interface for preventing duplicate ML experiments before GPU allocation.

Commands:
    datavint check <dataset>    Check for duplicate experiments
    datavint history            Show experiment history
    datavint config             Configure DataVint settings

Week 1 Implementation (Exact Duplicate Detection):
- Dataset fingerprinting via sampling
- Local SQLite storage
- Duplicate detection (exact matches only)
"""

import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
import pandas as pd


# Database path
DEFAULT_DB_PATH = Path.home() / ".datavint" / "experiments.db"


def _ensure_db_exists(db_path: Path):
    """Create database and tables if they don't exist."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Experiment fingerprints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT NOT NULL UNIQUE,
            dataset_path TEXT NOT NULL,
            dataset_size_mb REAL,
            row_count INTEGER,
            column_count INTEGER,
            columns TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            run_count INTEGER DEFAULT 1
        )
    """)

    # Experiment runs table (for tracking individual runs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint_id INTEGER NOT NULL,
            dataset_path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT,
            notes TEXT,
            FOREIGN KEY (fingerprint_id) REFERENCES experiment_fingerprints(id)
        )
    """)

    # Create indexes
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_fingerprints_fingerprint
        ON experiment_fingerprints(fingerprint)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_runs_fingerprint_id
        ON experiment_runs(fingerprint_id)
    """)

    conn.commit()
    conn.close()


def _compute_dataset_fingerprint(df: pd.DataFrame, sampling_rate: float = 0.001) -> str:
    """
    Compute fingerprint for a dataset using sampling.

    For Week 1: Sample 0.1% of dataset (0.001) for fast fingerprinting.
    Target: <30 seconds for 500GB dataset (500MB sample).

    Args:
        df: Dataset to fingerprint
        sampling_rate: Fraction of rows to sample (default: 0.001 = 0.1%)

    Returns:
        SHA256 hash (first 16 characters)
    """
    # Sample dataset for large datasets
    if len(df) > 1000:
        sample_size = max(1000, int(len(df) * sampling_rate))
        df_sample = df.sample(n=min(sample_size, len(df)), random_state=42)
    else:
        df_sample = df

    # Sort columns for deterministic ordering
    df_sorted = df_sample[sorted(df_sample.columns)]

    # Convert to JSON and hash
    json_str = df_sorted.to_json(orient='split', date_format='iso')
    hash_obj = hashlib.sha256(json_str.encode('utf-8'))

    # Return first 16 chars (longer than git's 7 for fewer collisions)
    return hash_obj.hexdigest()[:16]


def _load_dataset(path: str) -> pd.DataFrame:
    """
    Load dataset from file path.

    Supports: CSV, Parquet, JSON
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise click.ClickException(f"Dataset not found: {path}")

    # Determine file type and load
    suffix = path_obj.suffix.lower()

    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix == '.parquet':
        return pd.read_parquet(path)
    elif suffix == '.json':
        return pd.read_json(path)
    else:
        raise click.ClickException(
            f"Unsupported file type: {suffix}. "
            f"Supported formats: .csv, .parquet, .json"
        )


def _check_duplicate(
    fingerprint: str,
    dataset_path: str,
    df: pd.DataFrame,
    db_path: Path
) -> Optional[dict]:
    """
    Check if experiment fingerprint already exists in database.

    Args:
        fingerprint: Dataset fingerprint hash
        dataset_path: Path to dataset file
        df: Loaded dataset
        db_path: Path to SQLite database

    Returns:
        Dictionary with duplicate info if found, None otherwise
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check for exact match
    cursor.execute("""
        SELECT
            id,
            dataset_path,
            row_count,
            column_count,
            first_seen,
            last_seen,
            run_count
        FROM experiment_fingerprints
        WHERE fingerprint = ?
    """, (fingerprint,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'id': result[0],
            'dataset_path': result[1],
            'row_count': result[2],
            'column_count': result[3],
            'first_seen': result[4],
            'last_seen': result[5],
            'run_count': result[6]
        }

    return None


def _store_fingerprint(
    fingerprint: str,
    dataset_path: str,
    df: pd.DataFrame,
    db_path: Path
):
    """
    Store experiment fingerprint in database.

    If fingerprint already exists, update last_seen and increment run_count.
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    now = datetime.now().isoformat()

    # Check if fingerprint already exists
    cursor.execute(
        "SELECT id, run_count FROM experiment_fingerprints WHERE fingerprint = ?",
        (fingerprint,)
    )
    existing = cursor.fetchone()

    if existing:
        # Update existing fingerprint
        fingerprint_id, run_count = existing
        cursor.execute("""
            UPDATE experiment_fingerprints
            SET last_seen = ?, run_count = ?, dataset_path = ?
            WHERE id = ?
        """, (now, run_count + 1, dataset_path, fingerprint_id))
    else:
        # Insert new fingerprint
        dataset_size_mb = Path(dataset_path).stat().st_size / (1024 * 1024)

        cursor.execute("""
            INSERT INTO experiment_fingerprints
            (fingerprint, dataset_path, dataset_size_mb, row_count, column_count,
             columns, first_seen, last_seen, run_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fingerprint,
            dataset_path,
            dataset_size_mb,
            len(df),
            len(df.columns),
            json.dumps(list(df.columns)),
            now,
            now,
            1
        ))
        fingerprint_id = cursor.lastrowid

    # Record experiment run
    cursor.execute("""
        INSERT INTO experiment_runs
        (fingerprint_id, dataset_path, timestamp, status)
        VALUES (?, ?, ?, ?)
    """, (fingerprint_id, dataset_path, now, 'checked'))

    conn.commit()
    conn.close()


@click.group()
@click.version_option(version='0.2.0')
def main():
    """
    DataVint - ML Execution Waste Control Layer

    Prevent duplicate ML experiments before GPU allocation.
    """
    pass


@main.command()
@click.argument('dataset_path', type=click.Path(exists=True))
@click.option(
    '--db-path',
    type=click.Path(),
    default=str(DEFAULT_DB_PATH),
    help='Path to SQLite database (default: ~/.datavint/experiments.db)'
)
@click.option(
    '--sampling-rate',
    type=float,
    default=0.001,
    help='Fraction of dataset to sample for fingerprinting (default: 0.001 = 0.1%)'
)
def check(dataset_path: str, db_path: str, sampling_rate: float):
    """
    Check for duplicate experiments before launching.

    Computes dataset fingerprint and checks if this exact experiment
    has been run before. Warns if duplicate is found.

    Example:
        $ datavint check data/train.csv
        $ datavint check data/features.parquet

    Exit codes:
        0 - No duplicate found (safe to proceed)
        1 - Duplicate found (warning issued)
        2 - Error occurred
    """
    try:
        db_path_obj = Path(db_path)
        _ensure_db_exists(db_path_obj)

        click.echo(f"🔍 Checking experiment: {dataset_path}")
        click.echo(f"   Loading dataset...")

        # Load dataset
        df = _load_dataset(dataset_path)
        click.echo(f"   Dataset: {len(df):,} rows × {len(df.columns)} columns")

        # Compute fingerprint
        click.echo(f"   Computing fingerprint (sampling {sampling_rate * 100}% of data)...")
        fingerprint = _compute_dataset_fingerprint(df, sampling_rate)
        click.echo(f"   Fingerprint: {fingerprint}")

        # Check for duplicates
        click.echo(f"   Checking for duplicates...")
        duplicate = _check_duplicate(fingerprint, dataset_path, df, db_path_obj)

        if duplicate:
            # Duplicate found!
            click.secho("\n⚠️  DUPLICATE EXPERIMENT DETECTED", fg='yellow', bold=True)
            click.echo(f"\nThis exact experiment has been run {duplicate['run_count']} time(s) before:\n")
            click.echo(f"  First run:    {duplicate['first_seen']}")
            click.echo(f"  Last run:     {duplicate['last_seen']}")
            click.echo(f"  Dataset path: {duplicate['dataset_path']}")
            click.echo(f"  Dataset size: {duplicate['row_count']:,} rows × {duplicate['column_count']} columns")
            click.echo(f"\n💡 Consider skipping this run to save GPU costs.")

            # Store this check
            _store_fingerprint(fingerprint, dataset_path, df, db_path_obj)

            # Exit with code 1 (warning)
            raise SystemExit(1)
        else:
            # No duplicate found
            click.secho("\n✅ NO DUPLICATE FOUND", fg='green', bold=True)
            click.echo(f"\nThis is a new experiment configuration.")
            click.echo(f"Safe to proceed with training.\n")

            # Store fingerprint for future checks
            _store_fingerprint(fingerprint, dataset_path, df, db_path_obj)

            # Exit with code 0 (success)
            raise SystemExit(0)

    except click.ClickException:
        raise
    except Exception as e:
        click.secho(f"\n❌ ERROR: {str(e)}", fg='red', bold=True)
        raise SystemExit(2)


@main.command()
@click.option(
    '--db-path',
    type=click.Path(),
    default=str(DEFAULT_DB_PATH),
    help='Path to SQLite database (default: ~/.datavint/experiments.db)'
)
@click.option(
    '--limit',
    type=int,
    default=10,
    help='Maximum number of experiments to show (default: 10)'
)
def history(db_path: str, limit: int):
    """
    Show experiment history.

    Displays recent experiments with their fingerprints and run counts.

    Example:
        $ datavint history
        $ datavint history --limit 20
    """
    try:
        db_path_obj = Path(db_path)

        if not db_path_obj.exists():
            click.echo("No experiment history found.")
            click.echo(f"Run 'datavint check <dataset>' to start tracking experiments.")
            return

        conn = sqlite3.connect(str(db_path_obj))
        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM experiment_fingerprints")
        total_count = cursor.fetchone()[0]

        if total_count == 0:
            click.echo("No experiment history found.")
            click.echo(f"Run 'datavint check <dataset>' to start tracking experiments.")
            conn.close()
            return

        # Get recent experiments
        cursor.execute("""
            SELECT
                fingerprint,
                dataset_path,
                row_count,
                column_count,
                first_seen,
                last_seen,
                run_count
            FROM experiment_fingerprints
            ORDER BY last_seen DESC
            LIMIT ?
        """, (limit,))

        experiments = cursor.fetchall()
        conn.close()

        # Display results
        click.secho(f"\n📊 Experiment History (showing {len(experiments)} of {total_count})\n", bold=True)

        for i, exp in enumerate(experiments, 1):
            fingerprint, dataset_path, row_count, col_count, first_seen, last_seen, run_count = exp

            click.echo(f"{i}. Fingerprint: {fingerprint}")
            click.echo(f"   Dataset:     {dataset_path}")
            click.echo(f"   Size:        {row_count:,} rows × {col_count} columns")
            click.echo(f"   Runs:        {run_count} time(s)")
            click.echo(f"   First seen:  {first_seen}")
            click.echo(f"   Last seen:   {last_seen}")
            click.echo()

    except Exception as e:
        click.secho(f"\n❌ ERROR: {str(e)}", fg='red', bold=True)
        raise SystemExit(2)


@main.command()
@click.option(
    '--gpu-price',
    type=float,
    help='GPU price per hour (e.g., 4.76 for 4x A100)'
)
@click.option(
    '--show',
    is_flag=True,
    help='Show current configuration'
)
def config(gpu_price: Optional[float], show: bool):
    """
    Configure DataVint settings.

    Example:
        $ datavint config --gpu-price 4.76
        $ datavint config --show

    Note: Cost estimation is a Week 5-6 feature. This command is a placeholder.
    """
    config_path = Path.home() / ".datavint" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if show:
        if config_path.exists():
            with open(config_path) as f:
                cfg = json.load(f)
            click.echo("\nCurrent configuration:")
            for key, value in cfg.items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo("\nNo configuration found. Use --gpu-price to set values.")
        return

    # Load existing config or create new
    cfg = {}
    if config_path.exists():
        with open(config_path) as f:
            cfg = json.load(f)

    # Update config
    if gpu_price is not None:
        cfg['gpu_price_per_hour'] = gpu_price
        click.echo(f"✅ GPU price set to ${gpu_price:.2f}/hour")

    # Save config
    with open(config_path, 'w') as f:
        json.dump(cfg, f, indent=2)

    click.echo(f"Configuration saved to {config_path}")


if __name__ == '__main__':
    main()
