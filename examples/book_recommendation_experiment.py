"""
DataVint Book Recommendation Experiment with XGBoost

This script demonstrates experiment tracking on a real Kaggle dataset:
- Book Recommendation Dataset from Kaggle
- Data versioning: raw → filtered → feature engineered
- XGBoost model training with hyperparameter sweeps
- Lineage visualization in bipartite graph
"""

import pandas as pd
import numpy as np
import datavint as dv
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, roc_auc_score
from pathlib import Path
import sqlite3
import os

# Dataset path from kagglehub download
DATASET_PATH = "/Users/duochen/.cache/kagglehub/datasets/arashnic/book-recommendation-dataset/versions/3"


def main():
    print("🔬 DataVint Book Recommendation Experiment\n")

    # ========================================================================
    # Step 1: Load and Merge Dataset
    # ========================================================================
    print("📊 Loading book recommendation dataset from Kaggle...")

    # Load ratings (sample to speed up demo)
    df_ratings = pd.read_csv(
        os.path.join(DATASET_PATH, "Ratings.csv"),
        nrows=50000  # Sample for faster processing
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
    # Step 2: Track Data Versions and Model Runs
    # ========================================================================
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

        # === Sweep 1: Different max_depth on raw data ===
        print("🌲 Sweep 1: Testing different max_depth values on D0\n")

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

        # Features: user age, book publication year
        features = ['Age', 'Year-Of-Publication']
        X = df_clean[features]
        y = df_clean['high_rating']

        print(f"  Clean data shape: {X.shape}")
        print(f"  High rating rate: {y.mean():.2%}\n")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        for depth in [3, 5, 10]:
            # Train model
            model = XGBClassifier(
                max_depth=depth,
                n_estimators=20,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            y_prob = model.predict_proba(X_test)[:, 1]
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            auc = roc_auc_score(y_test, y_prob)

            # Log run
            run_id = exp.log_run(
                data_commit_id=data_v0_id,
                metrics={
                    "accuracy": round(accuracy, 3),
                    "precision": round(precision, 3),
                    "auc": round(auc, 3)
                },
                params={"max_depth": depth, "n_estimators": 20, "learning_rate": 0.1},
                message=f"max_depth={depth}",
                sweep_id=1,
                sweep_name="Max Depth (from D0)"
            )
            print(f"  {run_id}: depth={depth:2d} → "
                  f"accuracy={accuracy:.3f}, auc={auc:.3f}")

        print()

        # === Data Version 2: Feature engineered ===
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

        # === Sweep 2: Different learning rates on D1 ===
        print("🌲 Sweep 2: Testing different learning rates on D1\n")

        features_v1 = ['Age', 'Year-Of-Publication', 'book_age', 'age_group']
        X_v1 = df_engineered[features_v1]
        y_v1 = df_engineered['high_rating']
        X_train_v1, X_test_v1, y_train_v1, y_test_v1 = train_test_split(
            X_v1, y_v1, test_size=0.2, random_state=42
        )

        best_auc = 0
        best_run_id = None

        for lr in [0.01, 0.1, 0.3]:
            # Train model
            model = XGBClassifier(
                max_depth=5,
                n_estimators=50,
                learning_rate=lr,
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train_v1, y_train_v1)

            # Evaluate
            y_pred = model.predict(X_test_v1)
            y_prob = model.predict_proba(X_test_v1)[:, 1]
            accuracy = accuracy_score(y_test_v1, y_pred)
            precision = precision_score(y_test_v1, y_pred, zero_division=0)
            auc = roc_auc_score(y_test_v1, y_prob)

            # Log run
            is_best = auc > best_auc
            run_id = exp.log_run(
                data_commit_id=data_v1_id,
                metrics={
                    "accuracy": round(accuracy, 3),
                    "precision": round(precision, 3),
                    "auc": round(auc, 3)
                },
                params={"max_depth": 5, "n_estimators": 50, "learning_rate": lr},
                message=f"learning_rate={lr}",
                sweep_id=2,
                sweep_name="Learning Rate (from D1, depth=5)",
                best=is_best
            )

            status = "⭐ BEST" if is_best else ""
            print(f"  {run_id}: lr={lr:0.2f} → "
                  f"accuracy={accuracy:.3f}, auc={auc:.3f} {status}")

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
        SELECT id, data_commit_id, message, metrics, sweep_id, sweep_name, best
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
        metrics = json.loads(row['metrics'])
        metrics_str = ", ".join(f"{k}={v}" for k, v in metrics.items())

        best_marker = "⭐" if row['best'] else " "
        print(f"    {best_marker} {row['id']} (from {row['data_commit_id']}): "
              f"{row['message']} → {metrics_str}")

    conn.close()


if __name__ == "__main__":
    main()
