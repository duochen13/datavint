# Quick Start: Experiment Lineage Tracking

## 🎯 3-Step Demo

### 1️⃣ Run the Demo (1 command)

```bash
python3 examples/experiment_lineage_demo.py
```

This creates:
- 2 data versions (D0, D1)
- 6 model runs (M0-M5)
- Lineage connections in `~/.datavint/metadata.db`

### 2️⃣ Start Services (2 commands)

```bash
# Terminal 1: Start server
cd server && python3 main.py

# Terminal 2: Start frontend
cd client && npm run dev
```

### 3️⃣ View Graph (1 URL)

```
http://localhost:5173/experiments/rec_model_sweep
```

---

## 🎨 What You'll See

```
Data Commits              Model Runs
━━━━━━━━━━━              ━━━━━━━━━━
D0 ─────┬──────────────► Sweep 1 (Tree Depth)
         │                 M0 (depth=3)
         ├──────────────►  M1 (depth=5)
         └──────────────►  M2 (depth=10)

D1 ─────┬──────────────► Sweep 2 (Num Trees)
         │                 M3 (n=20) ⭐
         ├──────────────►  M4 (n=50)
         └──────────────►  M5 (n=100) ⭐
```

**Interactive Features:**
- Hover over nodes to highlight connections
- Best models marked with ⭐
- Metrics shown with quality indicators
- Grouped by hyperparameter sweep

---

## 🔧 Custom Experiment

```python
import datavint as dv
import pandas as pd

with dv.experiment("my_experiment") as exp:
    # Log data
    df = pd.read_csv("data.csv")
    data_id = exp.log_data(df, message="v1 dataset")

    # Log model run
    exp.log_run(
        metrics={"accuracy": 0.92},
        params={"lr": 0.01},
        message="baseline model"
    )
```

View at: `http://localhost:5173/experiments/my_experiment`

---

## 📦 Files Summary

| File | Purpose |
|------|---------|
| `examples/experiment_lineage_demo.py` | Demo script |
| `server/api/routes/experiments.py` | API endpoint |
| `client/src/components/LineageGraph.vue` | Visualization |
| `~/.datavint/metadata.db` | SQLite storage |

---

## ✅ Verify Setup

```bash
# Check database
sqlite3 ~/.datavint/metadata.db "SELECT * FROM data_commits;"

# Test API
curl http://localhost:8080/api/experiments/rec_model_sweep/lineage | jq

# Test frontend
open http://localhost:5173/experiments/rec_model_sweep
```

---

## 📚 Full Documentation

See `EXPERIMENT_LINEAGE_SETUP.md` for:
- Architecture diagram
- Database schema
- API reference
- Troubleshooting
- Advanced usage
