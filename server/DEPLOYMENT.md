# Server Deployment Structure

## Railway Deployment Context

Railway builds from the `/server` directory (rootDirectory setting = `/server`).

To keep the root directory clean while allowing Railway to access all dependencies, deployment-related files are self-contained in `/server`:

```
/server/
├── pyproject.toml        # Package definition for datavint
├── requirements.txt      # Python dependencies (includes -e .)
├── datavint/            # Copy of datavint package source (deployment artifact)
├── api/                 # FastAPI application
└── DEPLOYMENT.md        # This file
```

## Important Notes

1. **Source of Truth**: `/datavint` (root level) is the source of truth for the datavint package
2. **Deployment Copy**: `/server/datavint` is a copy for Railway deployment
3. **Sync Required**: When making changes to `/datavint`, manually copy to `/server/datavint`:
   ```bash
   cp -r datavint/* server/datavint/
   ```

## Railway Configuration

- **Root Directory**: `/server`
- **Install Command**: `pip install -r requirements.txt`
- **Start Command**: Uses `Procfile` → `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

The `-e .` in `requirements.txt` installs the datavint package from `/server` in editable mode.
