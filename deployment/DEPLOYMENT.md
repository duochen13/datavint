# DataVint Deployment Guide

## Quick Start: Deploy to Railway (Recommended)

### Prerequisites
- GitHub account
- Credit card for domain registration ($12-15)
- Railway account (free to start)

---

## Step 1: Register Domain

### Option A: Namecheap (Recommended)
1. Go to https://www.namecheap.com
2. Search for domain:
   - **datavint.com** (~$12/year) ⭐ Best for SaaS product
   - **datavint.io** (~$40/year) - Developer-focused
   - **datavint.ai** (~$80/year) - AI branding
3. Complete purchase
4. **Don't configure DNS yet** - we'll do it after deployment

### Option B: Cloudflare Registrar
1. Go to https://dash.cloudflare.com
2. Navigate to "Domain Registration"
3. Search and purchase at cost (no markup)
4. DNS will be automatically configured

---

## Step 2: Deploy Backend (FastAPI)

### Railway Deployment

1. **Sign up for Railway**
   - Go to https://railway.app
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `hepta-ai` repository

3. **Configure Backend Service**
   - Railway will auto-detect Python
   - Set these environment variables:
     ```
     PORT=8000
     PYTHON_VERSION=3.9
     ```

4. **Get Backend URL**
   - Railway will give you a URL like: `https://datavint-production.up.railway.app`
   - **Copy this URL** - you'll need it for frontend

---

## Step 3: Build Frontend for Production

The frontend needs to know your backend URL. Update the API configuration:

1. Create production environment file:
   ```bash
   cd client
   cat > .env.production << 'EOF'
VITE_API_URL=https://your-backend-url.up.railway.app
EOF
   ```

2. Build frontend:
   ```bash
   npm run build
   ```

3. This creates `client/dist/` folder with production-ready files

---

## Step 4: Deploy Frontend

### Option A: Vercel (Free, Recommended)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy**
   ```bash
   cd client
   vercel --prod
   ```

3. **Configure Custom Domain** (in Vercel dashboard)
   - Go to Project Settings → Domains
   - Add `datavint.com` or `www.datavint.com`
   - Vercel will provide DNS records

### Option B: Netlify (Free)

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Deploy**
   ```bash
   cd client
   netlify deploy --prod --dir=dist
   ```

3. **Configure Custom Domain** (in Netlify dashboard)

### Option C: Railway (All-in-One)

1. Add a second service to your Railway project
2. Configure build command:
   ```
   cd client && npm install && npm run build
   ```
3. Configure start command:
   ```
   cd client && npx serve -s dist -p $PORT
   ```

---

## Step 5: Configure DNS

### If using Namecheap:

1. Log in to Namecheap
2. Go to "Domain List" → Manage
3. Find "Advanced DNS" tab
4. Add these records:

**For Vercel/Netlify Frontend:**
```
Type: A Record
Host: @
Value: <IP from hosting provider>

Type: CNAME Record
Host: www
Value: <domain from hosting provider>
```

**For Railway Backend:**
```
Type: CNAME Record
Host: api
Value: <your-backend>.up.railway.app
```

### If using Cloudflare:
- DNS is automatically configured
- Just add CNAME records pointing to your services

---

## Step 6: Update CORS Configuration

Update your backend CORS to allow your production domain:

```python
# server/api/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",          # Local development
        "https://datavint.com",            # Production
        "https://www.datavint.com",        # Production with www
        "https://api.datavint.com"         # API subdomain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push to trigger redeployment.

---

## Step 7: Test Production Deployment

1. **Test Frontend**
   - Visit `https://datavint.com`
   - Should load with white Apple-style theme
   - Check browser console for errors

2. **Test Backend**
   - Visit `https://api.datavint.com/docs` (or your Railway URL + /docs)
   - Should show FastAPI documentation

3. **Test Full Flow**
   - Upload a CSV file
   - Check data preview loads
   - Navigate to Visualization tab
   - Verify profiling results appear

---

## Cost Breakdown

### Minimal Setup (~$17/month):
- Domain: $12/year (~ $1/month)
- Railway backend: $5/month
- Vercel/Netlify frontend: Free
- **Total: ~$6/month**

### Professional Setup (~$25/month):
- Domain: $12/year
- Railway backend: $10/month (more resources)
- Cloudflare CDN: Free
- SSL: Free (auto-included)
- **Total: ~$11/month**

---

## Troubleshooting

### Frontend can't connect to backend
- Check `VITE_API_URL` in `.env.production`
- Verify CORS settings in `server/api/main.py`
- Check browser console for specific errors

### Backend crashes on Railway
- Check logs in Railway dashboard
- Ensure `requirements.txt` includes all dependencies
- Verify Python version matches (3.9)

### Domain not resolving
- DNS changes take 1-48 hours to propagate
- Use `dig datavint.com` to check DNS records
- Try clearing browser cache

### SSL certificate errors
- Wait 10-15 minutes after DNS configuration
- Hosting providers auto-provision SSL
- Check hosting provider's SSL dashboard

---

## Quick Deploy Script

Want to automate? Here's a one-command deploy:

```bash
#!/bin/bash
# deploy.sh

echo "🚀 Deploying DataVint..."

# Build frontend
cd client
npm install
npm run build

# Deploy with your chosen platform
vercel --prod  # or: netlify deploy --prod --dir=dist

echo "✅ Deployment complete!"
echo "🌐 Visit your site at https://datavint.com"
```

---

## Next Steps After Deployment

1. **Set up monitoring** - Railway/Vercel have built-in monitoring
2. **Add analytics** - Google Analytics or Plausible
3. **Enable error tracking** - Sentry for production errors
4. **Set up backups** - Railway auto-backs up databases
5. **Configure CI/CD** - Auto-deploy on git push

---

## Alternative: Docker Deployment

If you prefer Docker:

```dockerfile
# Dockerfile (root directory)
FROM python:3.9-slim as backend
WORKDIR /app
COPY server/ ./server/
RUN pip install -r server/requirements.txt
CMD ["uvicorn", "server.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:18 as frontend
WORKDIR /app
COPY client/ ./
RUN npm install && npm run build
CMD ["npx", "serve", "-s", "dist", "-p", "5173"]
```

Deploy to:
- **Railway**: Push Dockerfile, auto-detects
- **Fly.io**: `flyctl launch`
- **DigitalOcean App Platform**: Connect GitHub repo
- **AWS ECS/Fargate**: More complex but scalable

---

## Support

Questions? Check:
- Railway docs: https://docs.railway.app
- Vercel docs: https://vercel.com/docs
- Cloudflare docs: https://developers.cloudflare.com
