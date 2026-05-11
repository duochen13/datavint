"""
DataVint Experiment Tracking Demo

This example demonstrates how to use the experiment() context manager
to track data versions and model runs in an ML training pipeline.
"""

import pandas as pd
import numpy as np
import datavint as dv

# Simulate a recommendation system hyperparameter sweep
def main():
    print("🔬 DataVint Experiment Tracking Demo\n")

    # Create mock training data
    np.random.seed(42)
    df_v0 = pd.DataFrame({
        'user_id': range(1000),
        'item_id': np.random.randint(0, 100, 1000),
        'engagement': np.random.rand(1000),
        'clicked': np.random.binomial(1, 0.3, 1000)
    })

    # Improved data (after deduplication)
    df_v1 = df_v0.drop_duplicates(subset=['user_id', 'item_id'])
    print(f"Data v0: {len(df_v0)} rows")
    print(f"Data v1: {len(df_v1)} rows (after dedup)\n")

    # Start experiment tracking
    with dv.experiment("learning_rate_sweep_demo") as exp:
        # === Sweep 1: Try different learning rates on D0 ===
        print("📊 Sweep 1: Learning Rate Optimization (D0)")
        data_v0_id = exp.log_data(df_v0, message="original data with duplicates")
        print(f"  Logged data version: {data_v0_id}")

        learning_rates = [0.001, 0.005, 0.01, 0.02]
        best_ne = 0
        best_lr = None

        for lr in learning_rates:
            # Simulate training (mock NE metric)
            ne = 0.75 + np.random.rand() * 0.1
            ctr = 0.003 + np.random.rand() * 0.002

            run_id = exp.log_run(
                data_commit_id=data_v0_id,
                metrics={"NE": round(ne, 3), "CTR": round(ctr, 4)},
                params={"lr": lr},
                message=f"lr={lr}",
                sweep_id=1,
                sweep_name="Learning Rate (from D0)"
            )
            print(f"  {run_id}: lr={lr}, NE={ne:.3f}, CTR={ctr:.4f}")

            if ne > best_ne:
                best_ne = ne
                best_lr = lr

        print(f"  ✅ Best: lr={best_lr} (NE={best_ne:.3f})\n")

        # === Sweep 2: Try sample rates with best LR on D1 ===
        print("📊 Sweep 2: Sample Rate Optimization (D1)")
        data_v1_id = exp.log_data(df_v1, message="deduped data")
        print(f"  Logged data version: {data_v1_id}")

        sample_rates = [0.4, 0.6, 0.8]
        best_overall_ne = 0
        best_run_id = None

        for sr in sample_rates:
            # Simulate training with improved data
            ne = 0.85 + np.random.rand() * 0.05  # Higher NE with better data
            ctr = 0.005 + np.random.rand() * 0.002

            run_id = exp.log_run(
                data_commit_id=data_v1_id,
                metrics={"NE": round(ne, 3), "CTR": round(ctr, 4)},
                params={"lr": best_lr, "sample_rate": sr},
                message=f"sample_rate={sr}",
                sweep_id=2,
                sweep_name=f"Sample Rate (from D1, lr={best_lr})",
                best=(ne > 0.88)  # Mark as best if NE > 0.88
            )
            print(f"  {run_id}: sample_rate={sr}, NE={ne:.3f}, CTR={ctr:.4f}")

            if ne > best_overall_ne:
                best_overall_ne = ne
                best_run_id = run_id

        print(f"  ✅ Best overall: {best_run_id} (NE={best_overall_ne:.3f})\n")

    print("✅ Experiment tracking complete!")
    print(f"📁 Metadata stored in: ~/.datavint/metadata.db")
    print("\n💡 Next steps:")
    print("  1. View lineage in dashboard: http://localhost:5173/experiments/learning_rate_sweep_demo")
    print("  2. Query metadata with SQL:")
    print("     sqlite3 ~/.datavint/metadata.db 'SELECT * FROM model_runs;'")
    print("  3. Integrate with server API to visualize lineage graph")


if __name__ == "__main__":
    main()
