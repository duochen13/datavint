# Railway Deployment Configuration

This directory contains Railway-specific deployment configuration files.

## Files

- `Procfile` - Railway start command
- `railway.json` - Railway service configuration (optional)
- `requirements.txt` - Server-specific dependencies (references root package via `-e ..`)

## Railway Settings

**Build Configuration:**
- **Root Directory**: `/` (empty or root - Railway builds from repo root)
- **Install Command**: `pip install -r requirements.txt`
- **Build Command**: (leave default/empty)

**Deploy Configuration:**
- **Start Command**: `cd server && uvicorn api.main:app --host 0.0.0.0 --port $PORT`
  - Defined in `/server/Procfile`
  - Changes to server directory first
  - Starts FastAPI application

## How It Works

1. Railway builds from repo root (has access to everything)
2. Installs dependencies from root `requirements.txt`:
   - `-e .` installs the datavint package from root via `pyproject.toml`
   - FastAPI and server dependencies
3. Starts server using `Procfile` command (changes to /server first)
4. FastAPI app at `/server/api` can import datavint package

## Package Structure

```
/ (root - Railway build context)
├── pyproject.toml       # datavint package definition
├── requirements.txt     # All dependencies (includes -e .)
├── datavint/           # Package source code
└── server/             # FastAPI application
    ├── Procfile        # Start command
    ├── railway.json    # Railway config
    ├── requirements.txt # Points to root package (-e ..)
    └── api/            # FastAPI routes
```

Railway installs datavint as an editable package from root, making it available to the server code.
