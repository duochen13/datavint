# Experiment Lineage Tracking & Bipartite Graph Visualization

## ✅ Complete Implementation

This document describes the complete end-to-end flow for tracking ML experiment lineage and visualizing it in a bipartite graph.

---

## 🏗️ Architecture

```
┌─────────────────────┐
│  Python Script      │  (examples/experiment_lineage_demo.py)
│  or Notebook        │  Uses: datavint.experiment() API
└──────────┬──────────┘
           │
           │ Writes to
           ▼
┌─────────────────────┐
│  SQLite Database    │  (~/.datavint/metadata.db)
│                     │  Tables: data_commits, model_runs
└──────────┬──────────┘
           │
           │ Reads from
           ▼
┌─────────────────────┐
│  FastAPI Server     │  (server/api/routes/experiments.py)
│                     │  GET /api/experiments/{id}/lineage
└──────────┬──────────┘
           │
           │ Serves JSON
           ▼
┌─────────────────────┐
│  Vue Frontend       │  (client/src/components/LineageGraph.vue)
│                     │  Renders bipartite graph
└─────────────────────┘
```

---

## 📁 Files Created/Modified

### 1. Demo Script
**File**: `examples/experiment_lineage_demo.py`
- Demonstrates data versioning and model tracking
- Creates 2 data versions (original + deduplicated)
- Runs 2 hyperparameter sweeps (6 total model runs)
- Shows lineage connections

### 2. API Endpoint
**File**: `server/api/routes/experiments.py`
- `GET /api/experiments/list` - List all SDK experiments
- `GET /api/experiments/{experiment_id}/lineage` - Get lineage data
- `GET /api/experiments/stats` - Aggregate statistics
- Reads from `~/.datavint/metadata.db`

### 3. Server Registration
**File**: `server/api/main.py`
- Added import for `experiments` router
- Registered endpoint at `/api/experiments/*`

### 4. Test Script
**File**: `test_api_endpoint.py`
- Validates database structure
- Tests endpoint logic
- Verifies lineage connections

---

## 🚀 Quick Start

### Step 1: Run the Demo

```bash
# Clear old data (optional)
rm -f ~/.datavint/metadata.db

# Run the demo
python3 examples/experiment_lineage_demo.py
```

**Output:**
```
🔬 DataVint Experiment Tracking & Lineage Demo

DATA VERSION D0: Original data with duplicates
✓ Logged data commit: D0
  Rows: 1000, Columns: 5

🌲 Sweep 1: Testing different max_depth values on D0
  M0: depth= 3 → accuracy=0.740, precision=0.667
  M1: depth= 5 → accuracy=0.740, precision=0.600
  M2: depth=10 → accuracy=0.695, precision=0.300

DATA VERSION D1: Deduplicated data
✓ Logged data commit: D1
  Rows: 1000 → 954 (removed 46 duplicates)

🌲 Sweep 2: Testing different n_estimators on D1
  M3: n_trees= 20 → accuracy=0.660, precision=0.429 ⭐ BEST
  M4: n_trees= 50 → accuracy=0.660, precision=0.429
  M5: n_trees=100 → accuracy=0.665, precision=0.500 ⭐ BEST
```

### Step 2: Start the Server

```bash
cd server
python3 main.py
```

Server runs at: http://localhost:8080

### Step 3: Start the Frontend

```bash
cd client
npm run dev
```

Frontend runs at: http://localhost:5173

### Step 4: View Lineage

Open in browser:
```
http://localhost:5173/experiments/rec_model_sweep
```

---

## 📊 What You'll See

### Bipartite Graph Layout

```
┌─────────────────┐                    ┌─────────────────┐
│  Data Commits   │                    │   Model Runs    │
├─────────────────┤                    ├─────────────────┤
│                 │                    │                 │
│  D0             │──────┬─────────────│ Sweep 1         │
│  original data  │      │             │  M0 (depth=3)   │
│  1000 rows      │      ├─────────────│  M1 (depth=5)   │
│                 │      └─────────────│  M2 (depth=10)  │
│                 │                    │                 │
│  D1             │──────┬─────────────│ Sweep 2         │
│  deduped data   │      │             │  M3 (n=20) ⭐   │
│  954 rows       │      ├─────────────│  M4 (n=50)      │
│                 │      └─────────────│  M5 (n=100) ⭐  │
└─────────────────┘                    └─────────────────┘
```

### Interactive Features

- **Hover**: Highlight connected nodes
- **Grouped Sweeps**: Model runs organized by hyperparameter sweep
- **Best Models**: Marked with ⭐
- **Metrics Display**: Accuracy, precision with quality indicators
- **Connections**: Bezier curves showing data → model lineage

---

## 🔍 Database Schema

### Table: `data_commits`
```sql
CREATE TABLE data_commits (
    id TEXT PRIMARY KEY,              -- D0, D1, D2, ...
    experiment_id TEXT NOT NULL,      -- "rec_model_sweep"
    hash TEXT NOT NULL,               -- SHA256 content hash (first 7 chars)
    message TEXT,                     -- "deduped interactions"
    row_count INTEGER,                -- 954
    column_count INTEGER,             -- 5
    timestamp TEXT NOT NULL,          -- ISO 8601
    metadata TEXT                     -- JSON blob
);
```

### Table: `model_runs`
```sql
CREATE TABLE model_runs (
    id TEXT PRIMARY KEY,              -- M0, M1, M2, ...
    experiment_id TEXT NOT NULL,      -- "rec_model_sweep"
    data_commit_id TEXT NOT NULL,     -- "D0" (foreign key)
    message TEXT,                     -- "max_depth=3"
    metrics TEXT,                     -- JSON: {"accuracy": 0.74, ...}
    params TEXT,                      -- JSON: {"max_depth": 3, ...}
    timestamp TEXT NOT NULL,          -- ISO 8601
    best INTEGER DEFAULT 0,           -- 1 if best model
    sweep_id INTEGER,                 -- 1, 2, 3, ...
    sweep_name TEXT,                  -- "Tree Depth (from D0)"
    FOREIGN KEY (data_commit_id) REFERENCES data_commits(id)
);
```

---

## 🧪 Testing

### Test the Database

```bash
# View data commits
sqlite3 ~/.datavint/metadata.db \
  "SELECT id, message, row_count FROM data_commits WHERE experiment_id='rec_model_sweep';"

# View model runs
sqlite3 ~/.datavint/metadata.db \
  "SELECT id, data_commit_id, message FROM model_runs WHERE experiment_id='rec_model_sweep';"
```

### Test the API

```bash
# Test endpoint logic
python3 test_api_endpoint.py

# Test live endpoint (server must be running)
curl http://localhost:8080/api/experiments/rec_model_sweep/lineage | jq
```

### Verify Frontend

1. Open: http://localhost:5173/experiments/rec_model_sweep
2. Check that you see 2 data commits (D0, D1)
3. Check that you see 6 model runs grouped into 2 sweeps
4. Hover over a node to verify connections highlight
5. Verify best models (M3, M5) are marked with stars

---

## 📝 API Response Format

### GET /api/experiments/{experiment_id}/lineage

```json
{
  "experimentId": "rec_model_sweep",
  "dataCommits": [
    {
      "id": "D0",
      "message": "original data with duplicates",
      "hash": "0b8025b",
      "rowCount": 1000,
      "columnCount": 5,
      "timestamp": "2026-05-14T..."
    },
    {
      "id": "D1",
      "message": "deduped interactions",
      "hash": "40eb8c7",
      "rowCount": 954,
      "columnCount": 5,
      "timestamp": "2026-05-14T..."
    }
  ],
  "modelRuns": [
    {
      "id": "M0",
      "dataCommitId": "D0",
      "message": "max_depth=3",
      "metrics": {
        "accuracy": {"value": 0.74, "quality": "ok"},
        "precision": {"value": 0.667, "quality": "ok"}
      },
      "timestamp": "2026-05-14T...",
      "sweep": {
        "id": 1,
        "name": "Tree Depth (from D0)"
      }
    },
    ...
  ],
  "connections": {
    "D0": ["M0", "M1", "M2"],
    "D1": ["M3", "M4", "M5"]
  }
}
```

---

## 🔄 Typical Workflow

### 1. Track Experiments (Python)

```python
import datavint as dv
import pandas as pd

with dv.experiment("my_experiment") as exp:
    # Log data version
    df = pd.read_csv("data.csv")
    data_id = exp.log_data(df, message="cleaned dataset")

    # Train models
    for lr in [0.001, 0.01, 0.1]:
        model.train(lr=lr)
        metrics = {"accuracy": model.evaluate()}

        exp.log_run(
            metrics=metrics,
            params={"lr": lr},
            sweep_id=1,
            sweep_name="Learning Rate Sweep"
        )
```

### 2. View in Dashboard

1. Navigate to: `http://localhost:5173/experiments/my_experiment`
2. See your data versions and model runs visualized
3. Hover to explore lineage relationships

### 3. Query Metadata

```python
import sqlite3
from pathlib import Path

db = Path.home() / ".datavint" / "metadata.db"
conn = sqlite3.connect(str(db))

# Get best model
cursor = conn.execute("""
    SELECT id, metrics, params
    FROM model_runs
    WHERE experiment_id = 'my_experiment' AND best = 1
""")
print(cursor.fetchone())
```

---

## 🎯 Next Steps

### Potential Enhancements

1. **Auto-refresh**: Frontend auto-polls for new experiments
2. **Diff view**: Compare metrics between runs
3. **Export**: Download lineage as JSON/CSV
4. **Search**: Filter by metrics, params, or time range
5. **Multi-experiment**: Compare lineage across experiments
6. **Notebook integration**: Jupyter widget for inline visualization

### Integration Points

- **MLflow**: Import/export MLflow experiments
- **DVC**: Link to DVC-tracked datasets
- **W&B**: Sync with Weights & Biases
- **Git**: Track code versions alongside data versions

---

## ✅ Verification Checklist

- [x] Demo script runs successfully
- [x] Database contains correct data (2 commits, 6 runs)
- [x] API endpoint reads from metadata.db
- [x] API returns correct JSON format
- [x] Frontend can display bipartite graph
- [x] Connections correctly link data → models
- [x] Sweeps are grouped correctly
- [x] Best models are marked with stars

---

## 🐛 Troubleshooting

### Database already exists error

```bash
# Clear the database
rm ~/.datavint/metadata.db

# Re-run the demo
python3 examples/experiment_lineage_demo.py
```

### Server not starting

```bash
# Check if port 8080 is in use
lsof -i :8080

# Kill existing process or use different port
cd server
uvicorn api.main:app --port 8081 --reload
```

### Frontend not loading

```bash
# Reinstall dependencies
cd client
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

## 📚 Documentation References

- **Experiment API**: `datavint/experiment.py`
- **Server Endpoint**: `server/api/routes/experiments.py`
- **Frontend Component**: `client/src/components/LineageGraph.vue`
- **Demo Script**: `examples/experiment_lineage_demo.py`
