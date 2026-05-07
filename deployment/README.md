# DataVint Deployment Files

This directory contains all deployment-related configuration and documentation for DataVint.

## Files

### Documentation

- **DEPLOY_DATAVINT_IO.md** - Complete step-by-step guide for deploying to datavint.io (~30 minutes)
  - Domain registration (Namecheap/Cloudflare)
  - Railway backend deployment
  - Vercel frontend deployment
  - DNS configuration
  - Testing and troubleshooting

- **DEPLOYMENT.md** - General deployment guide with multiple platform options
  - Platform comparisons (Railway, Render, Heroku, etc.)
  - Alternative deployment strategies
  - Cost analysis

### Configuration Files

Railway configuration has been moved to `/server/` for better organization:
- **Procfile** → `/server/Procfile`
- **railway.json** → `/server/railway.json`
- See `/server/RAILWAY.md` for Railway deployment details

### Scripts

- **vercel/build.sh** - Vercel build script (moved from root for organization)
  - Builds Vue.js dashboard (client/)
  - Copies landing page (docs/)
  - Creates combined deployment structure

- **deploy.sh** - Quick deployment verification script
  - Builds frontend locally
  - Verifies backend dependencies
  - Checks project structure

## Quick Start

1. **For datavint.io deployment**, follow: `DEPLOY_DATAVINT_IO.md`
2. **For general deployment options**, see: `DEPLOYMENT.md`
3. **To verify build locally**, run: `./deploy.sh`

## Production Configuration

### Frontend Configuration
File: `../client/.env.production`
```bash
VITE_API_URL=https://api.datavint.io
```

### Backend Configuration
File: `../server/api/main.py`
```python
allow_origins=[
    "https://datavint.io",
    "https://www.datavint.io",
    "https://api.datavint.io",
]
```

### Railway Configuration
File: `railway.json`
- Build configuration for Railway platform
- Environment variables for production

## Cost Estimate

- **Domain**: $35-40/year (~$3/month)
- **Railway Backend**: $5/month (free tier available)
- **Vercel Frontend**: FREE
- **Total**: ~$8/month

## Support

For deployment issues, check:
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- DataVint Issues: https://github.com/duochen13/datavint/issues
