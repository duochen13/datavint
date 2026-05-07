# Root Directory Structure

This document explains the root-level configuration files and their purposes.

## Root Configuration Files

### Python Package (DataVint SDK)
- **`pyproject.toml`** - Python package definition
  - Defines datavint as an installable package
  - Used by: pip, local development, Railway deployment
  - Must stay at root (Python packaging standard)

- **`requirements.txt`** - Python dependencies for all components
  - Installs datavint package via `-e .`
  - Includes FastAPI server dependencies
  - Used by: Railway deployment, local development
  - Must stay at root (pip convention)

### Frontend Deployment (Vercel)
- **`package.json`** - Node.js package metadata
  - Defines build script for Vercel
  - Points to: `deployment/vercel/build.sh`
  - Must stay at root (Vercel requirement)

- **`vercel.json`** - Vercel deployment configuration
  - Defines build command, output directory, headers
  - Must stay at root (Vercel convention)

- **`.vercelignore`** - Files to exclude from Vercel deployment
  - Git-style ignore patterns
  - Must stay at root (Vercel convention)

### Project Documentation
- **`README.md`** - Main project documentation
- **`CLAUDE.md`** - AI assistant instructions and project structure

### Environment & Git
- **`.env.local`** - Local environment variables
- **`.gitignore`** - Files to exclude from git

## Deployment Configurations (Organized in Subdirectories)

### Backend (Railway) → `/server/`
- `server/Procfile` - Railway start command
- `server/railway.json` - Railway service config
- `server/RAILWAY.md` - Railway deployment guide
- `server/requirements.txt` - Points to root package via `-e ..`

### Frontend (Vercel) → `/deployment/vercel/`
- `deployment/vercel/build.sh` - Vercel build script

## Why This Structure?

**Root files** = Required by tools (pip, Vercel, npm)
**Subdirectory files** = Platform-specific configs (organized by platform)

This keeps root clean while maintaining standard tool conventions.

## Quick Reference

| File | Purpose | Can Move? |
|------|---------|-----------|
| `pyproject.toml` | Python package def | ❌ No (pip standard) |
| `requirements.txt` | Python dependencies | ❌ No (pip standard) |
| `package.json` | Node.js metadata | ❌ No (Vercel needs it) |
| `vercel.json` | Vercel config | ❌ No (Vercel convention) |
| `.vercelignore` | Vercel ignore | ❌ No (Vercel convention) |
| `README.md` | Documentation | ✅ Could, but standard at root |
| `CLAUDE.md` | AI instructions | ✅ Could, but useful at root |
