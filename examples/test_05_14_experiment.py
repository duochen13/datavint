"""
Custom Experiment: test-05-14
Demonstrates data versioning and model tracking with a simple classification task.
"""

import pandas as pd
import numpy as np
import datavint as dv
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


def main():
    print("🚀 Starting Custom Experiment: test-05-14\n")

    # Set random seed for reproducibility
    np.random.seed(2026)

    # ========================================================================
    # Create synthetic dataset
    # ========================================================================
    print("📊 Creating synthetic customer churn dataset...")
    n_samples = 2000

    df_raw = pd.DataFrame({
        'customer_id': range(n_samples),
        'tenure_months': np.random.randint(1, 72, n_samples),
        'monthly_charges': np.random.uniform(20, 150, n_samples),
        'total_charges': np.random.uniform(100, 8000, n_samples),
        'num_products': np.random.randint(1, 5, n_samples),
        'support_tickets': np.random.poisson(2, n_samples),
        'churn': np.random.binomial(1, 0.25, n_samples)  # 25% churn rate
    })

    print(f"   Created {len(df_raw)} customer records")
    print(f"   Churn rate: {df_raw['churn'].mean():.1%}\n")

    # ========================================================================
    # Start experiment tracking
    # ========================================================================
    with dv.experiment("test-05-14") as exp:

        # === Version 1: Raw data with outliers ===
        print("=" * 70)
        print("DATA VERSION D0: Raw data with outliers")
        print("=" * 70)

        data_v0_id = exp.log_data(
            df_raw,
            message="raw customer data with outliers"
        )
        print(f"✓ Logged data commit: {data_v0_id}")
        print(f"  Shape: {df_raw.shape}")
        print(f"  Features: {list(df_raw.columns)}\n")

        # Prepare features and target
        features = ['tenure_months', 'monthly_charges', 'total_charges',
                   'num_products', 'support_tickets']
        X_v0 = df_raw[features]
        y_v0 = df_raw['churn']
        X_train, X_test, y_train, y_test = train_test_split(
            X_v0, y_v0, test_size=0.25, random_state=42
        )

        # === Sweep 1: Learning rate optimization (D0) ===
        print("🔬 Sweep 1: Learning Rate Optimization (on D0)")
        print("=" * 70)

        learning_rates = [0.01, 0.05, 0.1, 0.2]
        best_f1_v0 = 0

        for lr in learning_rates:
            # Train model
            model = GradientBoostingClassifier(
                learning_rate=lr,
                n_estimators=50,
                max_depth=3,
                random_state=42
            )
            model.fit(X_train, y_train)

            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)

            # Log run
            run_id = exp.log_run(
                data_commit_id=data_v0_id,
                metrics={
                    "accuracy": round(accuracy, 3),
                    "precision": round(precision, 3),
                    "recall": round(recall, 3),
                    "f1": round(f1, 3)
                },
                params={
                    "learning_rate": lr,
                    "n_estimators": 50,
                    "max_depth": 3
                },
                message=f"lr={lr}",
                sweep_id=1,
                sweep_name="Learning Rate (D0)",
                best=(f1 > best_f1_v0)
            )

            marker = "⭐" if f1 > best_f1_v0 else " "
            print(f"  {marker} {run_id}: lr={lr:.2f} → "
                  f"F1={f1:.3f}, Acc={accuracy:.3f}, "
                  f"Prec={precision:.3f}, Rec={recall:.3f}")

            if f1 > best_f1_v0:
                best_f1_v0 = f1
                best_lr = lr

        print(f"\n  ✅ Best learning rate: {best_lr} (F1={best_f1_v0:.3f})\n")

        # === Version 2: Cleaned data (remove outliers) ===
        print("=" * 70)
        print("DATA VERSION D1: Cleaned data (outliers removed)")
        print("=" * 70)

        # Remove outliers (simple method: remove top 5% of charges)
        charge_threshold = df_raw['monthly_charges'].quantile(0.95)
        df_clean = df_raw[df_raw['monthly_charges'] <= charge_threshold].copy()

        data_v1_id = exp.log_data(
            df_clean,
            message="cleaned data, outliers removed"
        )
        print(f"✓ Logged data commit: {data_v1_id}")
        print(f"  Shape: {len(df_raw)} → {len(df_clean)} rows "
              f"(removed {len(df_raw) - len(df_clean)} outliers)")
        print(f"  Churn rate: {df_clean['churn'].mean():.1%}\n")

        # Prepare cleaned data
        X_v1 = df_clean[features]
        y_v1 = df_clean['churn']
        X_train_v1, X_test_v1, y_train_v1, y_test_v1 = train_test_split(
            X_v1, y_v1, test_size=0.25, random_state=42
        )

        # === Sweep 2: Tree depth optimization (D1) ===
        print("🌲 Sweep 2: Tree Depth Optimization (on D1)")
        print("=" * 70)

        max_depths = [2, 3, 5, 7]
        best_f1_overall = 0
        best_run = None

        for depth in max_depths:
            # Train model with best LR from sweep 1
            model = GradientBoostingClassifier(
                learning_rate=best_lr,
                n_estimators=50,
                max_depth=depth,
                random_state=42
            )
            model.fit(X_train_v1, y_train_v1)

            # Evaluate
            y_pred = model.predict(X_test_v1)
            accuracy = accuracy_score(y_test_v1, y_pred)
            precision = precision_score(y_test_v1, y_pred, zero_division=0)
            recall = recall_score(y_test_v1, y_pred, zero_division=0)
            f1 = f1_score(y_test_v1, y_pred, zero_division=0)

            # Log run
            is_best = f1 > best_f1_overall
            run_id = exp.log_run(
                data_commit_id=data_v1_id,
                metrics={
                    "accuracy": round(accuracy, 3),
                    "precision": round(precision, 3),
                    "recall": round(recall, 3),
                    "f1": round(f1, 3)
                },
                params={
                    "learning_rate": best_lr,
                    "n_estimators": 50,
                    "max_depth": depth
                },
                message=f"max_depth={depth}",
                sweep_id=2,
                sweep_name=f"Tree Depth (D1, lr={best_lr})",
                best=is_best
            )

            marker = "⭐" if is_best else " "
            print(f"  {marker} {run_id}: depth={depth} → "
                  f"F1={f1:.3f}, Acc={accuracy:.3f}, "
                  f"Prec={precision:.3f}, Rec={recall:.3f}")

            if is_best:
                best_f1_overall = f1
                best_run = run_id
                best_depth = depth

        print(f"\n  ✅ Best configuration: depth={best_depth} (F1={best_f1_overall:.3f})\n")

        # === Version 3: Feature engineering ===
        print("=" * 70)
        print("DATA VERSION D2: Feature engineered data")
        print("=" * 70)

        # Add engineered features
        df_engineered = df_clean.copy()
        df_engineered['avg_monthly_charge'] = (
            df_engineered['total_charges'] /
            df_engineered['tenure_months'].replace(0, 1)
        )
        df_engineered['products_per_month'] = (
            df_engineered['num_products'] /
            df_engineered['tenure_months'].replace(0, 1)
        )
        df_engineered['support_intensity'] = (
            df_engineered['support_tickets'] /
            df_engineered['tenure_months'].replace(0, 1)
        )

        data_v2_id = exp.log_data(
            df_engineered,
            message="added engineered features (ratios)"
        )
        print(f"✓ Logged data commit: {data_v2_id}")
        print(f"  Added features: avg_monthly_charge, products_per_month, support_intensity")
        print(f"  Total features: {len(features)} → {len(features) + 3}\n")

        # Train final model with all features
        features_v2 = features + ['avg_monthly_charge', 'products_per_month', 'support_intensity']
        X_v2 = df_engineered[features_v2]
        y_v2 = df_engineered['churn']
        X_train_v2, X_test_v2, y_train_v2, y_test_v2 = train_test_split(
            X_v2, y_v2, test_size=0.25, random_state=42
        )

        print("🎯 Final Model: Best config + feature engineering (on D2)")
        print("=" * 70)

        model_final = GradientBoostingClassifier(
            learning_rate=best_lr,
            n_estimators=100,  # More estimators for final model
            max_depth=best_depth,
            random_state=42
        )
        model_final.fit(X_train_v2, y_train_v2)

        # Evaluate
        y_pred_final = model_final.predict(X_test_v2)
        accuracy_final = accuracy_score(y_test_v2, y_pred_final)
        precision_final = precision_score(y_test_v2, y_pred_final, zero_division=0)
        recall_final = recall_score(y_test_v2, y_pred_final, zero_division=0)
        f1_final = f1_score(y_test_v2, y_pred_final, zero_division=0)

        # Log final run
        final_run_id = exp.log_run(
            data_commit_id=data_v2_id,
            metrics={
                "accuracy": round(accuracy_final, 3),
                "precision": round(precision_final, 3),
                "recall": round(recall_final, 3),
                "f1": round(f1_final, 3)
            },
            params={
                "learning_rate": best_lr,
                "n_estimators": 100,
                "max_depth": best_depth,
                "feature_engineering": True
            },
            message="production model with all optimizations",
            best=(f1_final > best_f1_overall)
        )

        print(f"  🏆 {final_run_id}: "
              f"F1={f1_final:.3f}, Acc={accuracy_final:.3f}, "
              f"Prec={precision_final:.3f}, Rec={recall_final:.3f}")

        if f1_final > best_f1_overall:
            print(f"\n  ✨ New best model! F1 improved: {best_f1_overall:.3f} → {f1_final:.3f}")
            best_run = final_run_id
        else:
            print(f"\n  ℹ️  Final model F1: {f1_final:.3f} (previous best: {best_f1_overall:.3f})")

    print("\n" + "=" * 70)
    print("✅ Experiment Complete: test-05-14")
    print("=" * 70)
    print(f"📁 Database: ~/.datavint/metadata.db")
    print(f"📊 Data versions: 3 (D0, D1, D2)")
    print(f"🤖 Model runs: 9 total")
    print(f"🏆 Best model: {best_run}")
    print("\n🌐 View lineage visualization:")
    print("   http://localhost:5175/experiments/test-05-14")
    print()


if __name__ == "__main__":
    main()
