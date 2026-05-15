"""
DataVint Book Recommendation Experiment with Logistic Regression

This script demonstrates experiment tracking on a real Kaggle dataset:
- Book Recommendation Dataset from Kaggle
- Data versioning: raw → filtered → feature engineered
- Logistic Regression with hyperparameter grid search (C × penalty)
- Dual tracking: DataVint (lineage) + MLflow (metrics)
- Lineage visualization in bipartite graph
"""

import pandas as pd
import datavint as dv
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, roc_auc_score
from pathlib import Path
import sqlite3
import os
from itertools import product

# Dataset path from kagglehub download
DATASET_PATH = "/Users/duochen/.cache/kagglehub/datasets/arashnic/book-recommendation-dataset/versions/3"


def main():
    print("🔬 DataVint Book Recommendation Experiment\n")

    # ========================================================================
    # Step 1: Load and Merge Dataset
    # ========================================================================
    print("📊 Loading book recommendation dataset from Kaggle...")

    # Load ratings (full dataset)
    df_ratings = pd.read_csv(
        os.path.join(DATASET_PATH, "Ratings.csv")
    )

    # Load books
    df_books = pd.read_csv(
        os.path.join(DATASET_PATH, "Books.csv"),
        usecols=['ISBN', 'Year-Of-Publication', 'Book-Author']
    )

    # Load users
    df_users = pd.read_csv(
        os.path.join(DATASET_PATH, "Users.csv"),
        usecols=['User-ID', 'Age']
    )

    # Merge datasets
    df = df_ratings.merge(df_users, on='User-ID', how='left')
    df = df.merge(df_books, on='ISBN', how='left')

    print(f"   Merged dataset shape: {df.shape}")
    print(f"   Ratings range: {df['Book-Rating'].min()} to {df['Book-Rating'].max()}")
    print(f"   Mean rating: {df['Book-Rating'].mean():.2f}\n")

    # ========================================================================
    # Step 2: Track Data Versions and Model Runs (DataVint + MLflow)
    # ========================================================================

    # Set MLflow experiment
    mlflow.set_experiment("book_recommendations_logistic_regression")

    with dv.experiment("book_recommendations") as exp:

        # === Data Version 1: Raw merged data ===
        print("=" * 70)
        print("DATA VERSION D0: Raw merged data with missing values")
        print("=" * 70)
        data_v0_id = exp.log_data(df, message="raw merged data")
        print(f"✓ Logged data commit: {data_v0_id}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        print(f"  Missing Age: {df['Age'].isna().sum()} rows")
        print(f"  Missing Year: {df['Year-Of-Publication'].isna().sum()} rows\n")

        # Prepare features (drop rows with missing values for simplicity)
        df_clean = df.dropna(subset=['Age', 'Year-Of-Publication'])

        # Convert Year to numeric (handle invalid values)
        df_clean['Year-Of-Publication'] = pd.to_numeric(
            df_clean['Year-Of-Publication'],
            errors='coerce'
        )
        df_clean = df_clean.dropna(subset=['Year-Of-Publication'])

        # Create binary target: high rating (>= 7)
        df_clean['high_rating'] = (df_clean['Book-Rating'] >= 7).astype(int)

        print(f"  Clean data shape: {df_clean.shape}")
        print(f"  High rating rate: {df_clean['high_rating'].mean():.2%}\n")

        # === Data Version 1: Feature engineered ===
        print("=" * 70)
        print("DATA VERSION D1: Feature engineering")
        print("=" * 70)

        df_engineered = df_clean.copy()

        # Add book age feature
        current_year = 2024
        df_engineered['book_age'] = current_year - df_engineered['Year-Of-Publication']

        # Add age group feature (binned)
        df_engineered['age_group'] = pd.cut(
            df_engineered['Age'],
            bins=[0, 18, 30, 50, 100],
            labels=[0, 1, 2, 3]
        ).cat.codes.astype(float)  # Use float to handle potential NaN

        data_v1_id = exp.log_data(df_engineered, message="added book_age and age_group")
        print(f"✓ Logged data commit: {data_v1_id}")
        print(f"  Rows: {len(df_engineered)}, Columns: {len(df_engineered.columns)}")
        print(f"  New features: book_age, age_group\n")

        # === Grid Search: C (regularization) × penalty type ===
        print("=" * 70)
        print("🔍 GRID SEARCH: C (regularization) × penalty type")
        print("=" * 70)

        features_v1 = ['Age', 'Year-Of-Publication', 'book_age', 'age_group']
        X_v1 = df_engineered[features_v1]
        y_v1 = df_engineered['high_rating']
        X_train_v1, X_test_v1, y_train_v1, y_test_v1 = train_test_split(
            X_v1, y_v1, test_size=0.2, random_state=42
        )

        # Grid search parameters
        C_values = [0.01, 0.1, 1.0]  # Regularization strength (smaller = stronger)
        penalties = ['l1', 'l2', None]  # Regularization type

        print(f"Testing {len(C_values)} × {len(penalties)} = "
              f"{len(C_values) * len(penalties)} combinations\n")

        best_auc = 0
        best_run_id = None

        # Grid search: all combinations
        for C, penalty in product(C_values, penalties):
            # Select appropriate solver for penalty type
            if penalty == 'l1':
                solver = 'saga'  # saga supports l1
            elif penalty is None:
                solver = 'lbfgs'  # lbfgs supports None
            else:  # l2
                solver = 'lbfgs'  # lbfgs is fast for l2

            # Format penalty for display
            penalty_str = 'none' if penalty is None else penalty

            # Start DataVint run (shows as 'running' with pulsing yellow indicator)
            run_id = exp.start_run(
                data_commit_id=data_v1_id,
                params={"C": C, "penalty": penalty_str, "solver": solver},
                message=f"C={C}, penalty={penalty_str}",
                sweep_id=1,
                sweep_name="Grid Search: C × penalty"
            )

            print(f"  🟡 {run_id}: Training C={C:7.2f}, penalty={penalty_str:5s}, solver={solver:8s}...")

            # Start MLflow run
            with mlflow.start_run(run_name=f"{run_id}_C{C}_penalty{penalty_str}"):
                # Log parameters to MLflow
                mlflow.log_param("C", C)
                mlflow.log_param("penalty", penalty_str)
                mlflow.log_param("solver", solver)
                mlflow.log_param("max_iter", 1000)
                mlflow.log_param("random_state", 42)
                mlflow.log_param("data_version", data_v1_id)
                mlflow.log_param("datavint_run_id", run_id)

                # Train model
                model = LogisticRegression(
                    C=C,
                    penalty=penalty,
                    solver=solver,
                    max_iter=1000,
                    random_state=42
                )
                model.fit(X_train_v1, y_train_v1)

                # Evaluate
                y_pred = model.predict(X_test_v1)
                y_prob = model.predict_proba(X_test_v1)[:, 1]
                accuracy = accuracy_score(y_test_v1, y_pred)
                precision = precision_score(y_test_v1, y_pred, zero_division=0)
                auc = roc_auc_score(y_test_v1, y_prob)

                # Log metrics to MLflow
                mlflow.log_metric("accuracy", accuracy)
                mlflow.log_metric("precision", precision)
                mlflow.log_metric("auc", auc)

                # Log model to MLflow
                mlflow.sklearn.log_model(model, "model")

                # Log feature coefficients for interpretability
                for i, feature in enumerate(features_v1):
                    mlflow.log_param(f"coef_{feature}", round(model.coef_[0][i], 4))

                # Update DataVint run with results (changes to green 'completed')
                is_best = auc > best_auc
                exp.log_run(
                    run_id=run_id,
                    metrics={
                        "accuracy": round(accuracy, 3),
                        "precision": round(precision, 3),
                        "auc": round(auc, 3)
                    },
                    best=is_best
                )

                # Log best model tag to MLflow
                if is_best:
                    mlflow.set_tag("best_model", "true")

                status = "⭐ BEST" if is_best else "✓"
                print(f"     {status} {run_id}: accuracy={accuracy:.3f}, auc={auc:.3f}\n")

                if is_best:
                    best_auc = auc
                    best_run_id = run_id

    print()
    print("=" * 70)
    print("✅ Experiment tracking complete!")
    print("=" * 70)
    print(f"📁 Metadata stored in: ~/.datavint/metadata.db")
    print(f"🏆 Best model: {best_run_id} (AUC={best_auc:.3f})\n")

    # ========================================================================
    # Step 3: Display Lineage Summary
    # ========================================================================
    print_lineage_summary()

    # ========================================================================
    # Step 4: Instructions for Visualization
    # ========================================================================
    print("\n" + "=" * 70)
    print("📊 VIEW LINEAGE IN BIPARTITE GRAPH")
    print("=" * 70)
    print("\n1. Start the server (if not running):")
    print("   cd server && python main.py")
    print("\n2. Start the frontend (if not running):")
    print("   cd client && npm run dev")
    print("\n3. Open in browser:")
    print("   http://localhost:5175/playground/book_recommendations")
    print("\n   You'll see:")
    print("   • Top: Data commits (D0, D1)")
    print("   • Bottom: Model runs (M0-M5) grouped by sweep")
    print("   • Lines: Connections showing data → model lineage")
    print("   • Hover: Metrics appear on hover")
    print()


def print_lineage_summary():
    """Print a summary of the tracked lineage from the database."""
    db_path = Path.home() / ".datavint" / "metadata.db"

    if not db_path.exists():
        print("⚠️  Database not found")
        return

    conn = sqlite3.connect(str(db_path))

    print("\n📊 LINEAGE SUMMARY (from database)")
    print("=" * 70)

    # Data commits
    print("\nData Commits:")
    commits_df = pd.read_sql_query("""
        SELECT id, message, row_count, column_count, hash
        FROM data_commits
        WHERE experiment_id = 'book_recommendations'
        ORDER BY timestamp
    """, conn)

    for _, row in commits_df.iterrows():
        print(f"  {row['id']}: {row['message']}")
        print(f"      {row['row_count']} rows × {row['column_count']} cols, "
              f"hash={row['hash'][:7]}")

    # Model runs
    print("\nModel Runs:")
    runs_df = pd.read_sql_query("""
        SELECT id, data_commit_id, message, metrics, sweep_id, sweep_name, best, status
        FROM model_runs
        WHERE experiment_id = 'book_recommendations'
        ORDER BY timestamp
    """, conn)

    current_sweep = None
    for _, row in runs_df.iterrows():
        # Print sweep header
        if row['sweep_id'] != current_sweep:
            current_sweep = row['sweep_id']
            print(f"\n  Sweep {row['sweep_id']}: {row['sweep_name']}")

        # Parse metrics
        import json
        metrics = json.loads(row['metrics']) if row['metrics'] else {}
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items()) if metrics else "no metrics"

        # Status indicator
        status_icons = {
            'init': '⚪',
            'running': '🟡',
            'completed': '🟢',
            'failed': '🔴'
        }
        status_icon = status_icons.get(row['status'], '⚪')

        best_marker = "⭐" if row['best'] else " "
        print(f"    {status_icon} {best_marker} {row['id']} (from {row['data_commit_id']}): "
              f"{row['message']} → {metrics_str}")

    conn.close()


if __name__ == "__main__":
    main()
