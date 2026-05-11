# Useful Commands & Tips

## Session Management

- Save progress: `/context-save [optional-title]`
- Restore session: `/context-restore`
- List saved contexts: `/context-save list`
- List all branches: `/context-save list --all`

## Gstack Skills

- QA testing: `/qa`
- Investigation: `/investigate`
- Code review: `/review`
- Ship changes: `/ship`

## Learnings

- Record learning: `/learn` skill
- Learnings auto-load at session start

## Tested Public Problematic Datasets

### Titanic (Kaggle) ✅ TESTED
- **Size**: 891 passengers (59KB)
- **Quality Issues**: Missing Age (19%), duplicates (10%)
- **DataVint Results**: 
  - Detected 10.1% duplicates
  - AUC improved 0.842 → 0.845 (+0.4%)
  - Precision improved +2.8%
  - Removed 72 duplicate rows

### Amazon Electronics ✅ TESTED  
- **Size**: 1.4GB (100K reviews tested)
- **Finding**: Too clean in sample, has data leakage (rating → label)
- **Recommendation**: Use for scale testing, not quality detection

### Recommended Next Tests
1. UCI Dirty Datasets (various sizes)
2. OpenML tagged quality issues
3. MovieLens Anomalous (injected issues)

## Experiment Tracking Commands (2026-05-11)

### Run Demo
```bash
python3 examples/experiment_tracking_demo.py
```
Output: 7 model runs (M0-M6) across 2 sweeps with mock data stored in SQLite.

### Query Metadata Store
```bash
# View all data commits
sqlite3 ~/.datavint/metadata.db "SELECT id, message, row_count FROM data_commits;"

# View all model runs
sqlite3 ~/.datavint/metadata.db "SELECT id, data_commit_id, message, metrics FROM model_runs;"

# Query specific experiment
sqlite3 ~/.datavint/metadata.db "SELECT * FROM model_runs WHERE experiment_id = 'learning_rate_sweep_demo';"

# Find best model (lowest NE)
sqlite3 ~/.datavint/metadata.db "SELECT id, metrics FROM model_runs WHERE best = 1;"
```

### Test API Endpoints
```bash
# List all experiments
curl http://localhost:8000/api/experiments | python3 -m json.tool

# Get experiment lineage (mock data)
curl http://localhost:8000/api/experiments/test_learning_rate_experiment/lineage | python3 -m json.tool

# Pretty print with head
curl -s http://localhost:8000/api/experiments/test_learning_rate_experiment/lineage | python3 -m json.tool | head -50
```

### View Dashboard
```
Frontend: http://localhost:5173/playground
Backend API: http://localhost:8000/api/docs
```

### Development Workflow
```bash
# Terminal 1: Start backend server
cd server
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start frontend dev server
cd client
npm run dev

# Terminal 3: Run tests
pytest tests/api/test_experiment_tracking.py -v
```

### SDK Usage in Notebooks
```python
import datavint as dv
import pandas as pd

# Create experiment
with dv.experiment("my_experiment") as exp:
    # Log data version
    df = pd.read_csv("data.csv")
    data_id = exp.log_data(df, message="cleaned data v1")

    # Train model
    # ... your training code ...

    # Log run
    exp.log_run(
        metrics={"NE": 0.685, "CTR": 0.0058},
        params={"lr": 0.005, "sample_rate": 0.6},
        message="best hyperparameters",
        best=True
    )
```

### Useful SQL Queries
```sql
-- Count runs per experiment
SELECT experiment_id, COUNT(*) as num_runs
FROM model_runs
GROUP BY experiment_id;

-- Find sweep winners
SELECT id, message, metrics, sweep_name
FROM model_runs
WHERE sweep_id IS NOT NULL
ORDER BY sweep_id, metrics;

-- Data commit usage
SELECT dc.id, dc.message, COUNT(mr.id) as num_runs
FROM data_commits dc
LEFT JOIN model_runs mr ON dc.id = mr.data_commit_id
GROUP BY dc.id;
```
