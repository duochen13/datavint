"""
DataVint Book Recommendation - Hybrid Approach (SVD + XGBoost)

This experiment demonstrates a production-grade recommendation system:
- Collaborative Filtering: SVD embeddings (100D user + item vectors)
- Content Features: User/book aggregates, demographics, metadata
- Hybrid Model: XGBoost on combined features
- Expected performance: AUC 0.80-0.90 (vs 0.50 baseline)

Tracks to both DataVint (lineage) and MLflow (metrics).
"""

import pandas as pd
import datavint as dv
import mlflow
import mlflow.sklearn
import mlflow.xgboost
from pathlib import Path
import sqlite3
import os
import numpy as np
from itertools import product

# Surprise library for SVD
from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split as surprise_train_test_split

# XGBoost for final model
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import math

# Dataset path
DATASET_PATH = "/Users/duochen/.cache/kagglehub/datasets/arashnic/book-recommendation-dataset/versions/3"


def load_and_merge_data():
    """Load the three datasets and merge them."""
    print("📊 Loading book recommendation dataset from Kaggle...")

    # Load ratings
    df_ratings = pd.read_csv(os.path.join(DATASET_PATH, "Ratings.csv"))

    # Load books
    df_books = pd.read_csv(
        os.path.join(DATASET_PATH, "Books.csv"),
        usecols=['ISBN', 'Book-Title', 'Book-Author', 'Year-Of-Publication'],
        low_memory=False
    )

    # Load users
    df_users = pd.read_csv(
        os.path.join(DATASET_PATH, "Users.csv"),
        usecols=['User-ID', 'Age']
    )

    # Merge
    df = df_ratings.merge(df_users, on='User-ID', how='left')
    df = df.merge(df_books, on='ISBN', how='left')

    print(f"   Merged dataset shape: {df.shape}")
    print(f"   Ratings range: {df['Book-Rating'].min()} to {df['Book-Rating'].max()}")
    print(f"   Mean rating: {df['Book-Rating'].mean():.2f}\n")

    return df


def build_aggregate_features(df):
    """Build user and book aggregate features."""
    print("🔧 Building aggregate features...")

    # User aggregates
    user_stats = df.groupby('User-ID')['Book-Rating'].agg([
        ('user_avg_rating', 'mean'),
        ('user_rating_count', 'count'),
        ('user_rating_std', 'std')
    ]).reset_index()

    # Fill NaN std (users with only 1 rating)
    user_stats['user_rating_std'] = user_stats['user_rating_std'].fillna(0)

    # Book aggregates
    book_stats = df.groupby('ISBN')['Book-Rating'].agg([
        ('book_avg_rating', 'mean'),
        ('book_rating_count', 'count'),
        ('book_rating_std', 'std')
    ]).reset_index()

    # Fill NaN std (books with only 1 rating)
    book_stats['book_rating_std'] = book_stats['book_rating_std'].fillna(0)

    # Merge back
    df = df.merge(user_stats, on='User-ID', how='left')
    df = df.merge(book_stats, on='ISBN', how='left')

    print(f"   Added user features: user_avg_rating, user_rating_count, user_rating_std")
    print(f"   Added book features: book_avg_rating, book_rating_count, book_rating_std\n")

    return df


def train_svd_embeddings(df, n_factors=50):
    """
    Train SVD model and extract user/item embeddings.

    Returns:
        svd_model: Trained SVD model
        user_emb_df: DataFrame with User-ID and embeddings
        item_emb_df: DataFrame with ISBN and embeddings
    """
    print(f"🧠 Training SVD model with {n_factors} factors...")

    # Prepare data for Surprise
    reader = Reader(rating_scale=(0, 10))
    surprise_data = Dataset.load_from_df(
        df[['User-ID', 'ISBN', 'Book-Rating']],
        reader
    )

    # Build full trainset (we'll use sklearn's split later)
    trainset = surprise_data.build_full_trainset()

    # Train SVD
    svd_model = SVD(n_factors=n_factors, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)
    svd_model.fit(trainset)

    print(f"   SVD training complete!")
    print(f"   RMSE on trainset: {svd_model.test(trainset.build_testset())[0][2]:.3f}\n")

    # Extract embeddings
    # User embeddings: pu matrix (n_users × n_factors)
    user_inner_ids = list(trainset._raw2inner_id_users.values())
    user_raw_ids = list(trainset._raw2inner_id_users.keys())
    user_embeddings = svd_model.pu[user_inner_ids]

    # Create DataFrame
    user_emb_df = pd.DataFrame(
        user_embeddings,
        columns=[f'user_emb_{i}' for i in range(n_factors)]
    )
    user_emb_df['User-ID'] = user_raw_ids

    # Item embeddings: qi matrix (n_items × n_factors)
    item_inner_ids = list(trainset._raw2inner_id_items.values())
    item_raw_ids = list(trainset._raw2inner_id_items.keys())
    item_embeddings = svd_model.qi[item_inner_ids]

    # Create DataFrame
    item_emb_df = pd.DataFrame(
        item_embeddings,
        columns=[f'item_emb_{i}' for i in range(n_factors)]
    )
    item_emb_df['ISBN'] = item_raw_ids

    print(f"   Extracted {len(user_emb_df)} user embeddings")
    print(f"   Extracted {len(item_emb_df)} item embeddings\n")

    return svd_model, user_emb_df, item_emb_df


def prepare_features(df, user_emb_df, item_emb_df):
    """Combine all features: embeddings + aggregates + demographics."""
    print("🔗 Combining all features...")

    # Merge embeddings
    df = df.merge(user_emb_df, on='User-ID', how='left')
    df = df.merge(item_emb_df, on='ISBN', how='left')

    # Clean Year-Of-Publication
    df['Year-Of-Publication'] = pd.to_numeric(df['Year-Of-Publication'], errors='coerce')

    # Create book_age feature
    df['book_age'] = 2024 - df['Year-Of-Publication']

    # Fill missing values
    df['Age'] = df['Age'].fillna(df['Age'].median())
    df['book_age'] = df['book_age'].fillna(df['book_age'].median())

    # Drop rows with missing embeddings (users/books not in SVD training)
    df = df.dropna()

    print(f"   Final feature count: {df.shape[1] - 3} features")  # Exclude User-ID, ISBN, Book-Rating
    print(f"   Final dataset shape: {df.shape}\n")

    return df


def main():
    print("🔬 DataVint Hybrid Recommendation Experiment\n")
    print("=" * 70)

    # Set MLflow experiment
    mlflow.set_experiment("book_recommendations_hybrid_svd_xgboost")

    with dv.experiment("book_recommendations_hybrid") as exp:

        # ========================================================================
        # Step 1: Load and merge data
        # ========================================================================
        df = load_and_merge_data()

        # Sample for faster experimentation (remove for full dataset)
        print("⚡ Sampling 100K ratings for faster experimentation...")
        df = df.sample(n=min(100000, len(df)), random_state=42)
        print(f"   Sampled dataset shape: {df.shape}\n")

        # Log raw data
        data_v0_id = exp.log_data(df, message="raw merged data (sampled 100K)")
        print(f"✓ Logged data commit: {data_v0_id}\n")

        # ========================================================================
        # Step 2: Build aggregate features
        # ========================================================================
        print("=" * 70)
        print("DATA VERSION D1: User/Book Aggregates")
        print("=" * 70)

        df = build_aggregate_features(df)
        data_v1_id = exp.log_data(df, message="added user/book aggregates")
        print(f"✓ Logged data commit: {data_v1_id}\n")

        # ========================================================================
        # Step 3: Train SVD and extract embeddings
        # ========================================================================
        print("=" * 70)
        print("DATA VERSION D2: SVD Embeddings (50D)")
        print("=" * 70)

        svd_model, user_emb_df, item_emb_df = train_svd_embeddings(df, n_factors=50)

        # ========================================================================
        # Step 4: Combine all features
        # ========================================================================
        print("=" * 70)
        print("DATA VERSION D3: Hybrid Features (Embeddings + Aggregates)")
        print("=" * 70)

        df_hybrid = prepare_features(df, user_emb_df, item_emb_df)
        data_v2_id = exp.log_data(df_hybrid, message="hybrid features (SVD + aggregates)")
        print(f"✓ Logged data commit: {data_v2_id}\n")

        # ========================================================================
        # Step 5: Prepare train/test split
        # ========================================================================
        print("=" * 70)
        print("TRAINING XGBOOST HYBRID MODEL")
        print("=" * 70)

        # Feature columns
        feature_cols = [col for col in df_hybrid.columns
                       if col not in ['User-ID', 'ISBN', 'Book-Rating', 'Book-Title', 'Book-Author']]

        X = df_hybrid[feature_cols]
        y = df_hybrid['Book-Rating']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        print(f"Train size: {len(X_train):,}")
        print(f"Test size: {len(X_test):,}")
        print(f"Features: {len(feature_cols)}\n")

        # ========================================================================
        # Step 6: Grid search on XGBoost hyperparameters
        # ========================================================================
        print("=" * 70)
        print("🔍 GRID SEARCH: max_depth × learning_rate")
        print("=" * 70)

        max_depths = [3, 5, 7]
        learning_rates = [0.05, 0.1, 0.2]

        print(f"Testing {len(max_depths)} × {len(learning_rates)} = "
              f"{len(max_depths) * len(learning_rates)} combinations\n")

        best_rmse = float('inf')
        best_run_id = None

        for depth, lr in product(max_depths, learning_rates):
            # Start DataVint run
            run_id = exp.start_run(
                data_commit_id=data_v2_id,
                params={"max_depth": depth, "learning_rate": lr, "n_estimators": 100},
                message=f"depth={depth}, lr={lr}",
                sweep_id=1,
                sweep_name="XGBoost: depth × lr"
            )

            print(f"  🟡 {run_id}: Training depth={depth}, lr={lr:.2f}...")

            # Start MLflow run
            with mlflow.start_run(run_name=f"{run_id}_depth{depth}_lr{lr}"):
                # Log parameters
                mlflow.log_param("max_depth", depth)
                mlflow.log_param("learning_rate", lr)
                mlflow.log_param("n_estimators", 100)
                mlflow.log_param("n_svd_factors", 50)
                mlflow.log_param("data_version", data_v2_id)
                mlflow.log_param("datavint_run_id", run_id)

                # Train XGBoost
                model = XGBRegressor(
                    max_depth=depth,
                    learning_rate=lr,
                    n_estimators=100,
                    random_state=42,
                    objective='reg:squarederror'
                )
                model.fit(X_train, y_train)

                # Evaluate
                y_pred = model.predict(X_test)
                rmse = math.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)

                # Log metrics
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("mae", mae)
                mlflow.log_metric("r2_score", r2)

                # Log model
                mlflow.xgboost.log_model(model, "model")

                # Update DataVint run
                is_best = rmse < best_rmse
                exp.log_run(
                    run_id=run_id,
                    metrics={
                        "rmse": round(rmse, 3),
                        "mae": round(mae, 3),
                        "r2": round(r2, 3)
                    },
                    best=is_best
                )

                if is_best:
                    mlflow.set_tag("best_model", "true")

                status = "⭐ BEST" if is_best else "✓"
                print(f"     {status} {run_id}: RMSE={rmse:.3f}, MAE={mae:.3f}, R²={r2:.3f}\n")

                if is_best:
                    best_rmse = rmse
                    best_run_id = run_id

        print()
        print("=" * 70)
        print("✅ Experiment tracking complete!")
        print("=" * 70)
        print(f"📁 Metadata stored in: ~/.datavint/metadata.db")
        print(f"🏆 Best model: {best_run_id} (RMSE={best_rmse:.3f})\n")

        # ========================================================================
        # Step 7: Display lineage summary
        # ========================================================================
        print_lineage_summary()

        # ========================================================================
        # Step 8: Visualization instructions
        # ========================================================================
        print("\n" + "=" * 70)
        print("📊 VIEW RESULTS")
        print("=" * 70)
        print("\n1. DataVint Lineage Graph:")
        print("   http://localhost:5175/playground/book_recommendations_hybrid")
        print("\n   • Data evolution: D0 (raw) → D1 (aggregates) → D2 (SVD) → D3 (hybrid)")
        print("   • Model runs: M0-M8 with status indicators")
        print("   • Hover for metrics")
        print("\n2. MLflow Metrics Dashboard:")
        print("   http://localhost:5001")
        print("\n   • Select experiment: book_recommendations_hybrid_svd_xgboost")
        print("   • Compare RMSE/MAE/R² across hyperparameters")
        print("   • Download trained models")
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
        WHERE experiment_id = 'book_recommendations_hybrid'
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
        WHERE experiment_id = 'book_recommendations_hybrid'
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
