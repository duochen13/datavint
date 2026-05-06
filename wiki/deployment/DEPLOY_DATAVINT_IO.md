# Deploy DataVint to datavint.io

**Quick deployment guide for getting datavint.io live in ~30 minutes**

---

## Step 1: Register datavint.io (5 minutes)

### Option A: Namecheap (Recommended)
1. Go to https://www.namecheap.com
2. Search for "datavint.io"
3. Price should be around **$35-40/year**
4. Add to cart and checkout
5. **Don't configure DNS yet** - we'll do it in Step 4

### Option B: Cloudflare Registrar (Cheaper)
1. Go to https://dash.cloudflare.com
2. Navigate to "Domain Registration"
3. Search "datavint.io"
4. Should be around **$9-12/year** (at-cost pricing)
5. Purchase
6. DNS will be auto-configured later

---

## Step 2: Deploy Backend to Railway (10 minutes)

### 2.1 Create Railway Account
1. Go to https://railway.app
2. Click "Sign up with GitHub"
3. Authorize Railway to access your GitHub

### 2.2 Deploy Backend
1. Click "**New Project**"
2. Select "**Deploy from GitHub repo**"
3. Choose your repository: `datavint`
4. Railway will auto-detect Python

### 2.3 Configure Backend Service
1. Click on the deployed service
2. Go to "**Settings**" tab
3. Set **Root Directory**: `server`
4. Set **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### 2.4 Add Environment Variables
1. Go to "**Variables**" tab
2. Add these variables:
   ```
   PORT=8000
   PYTHON_VERSION=3.9
   ```

### 2.5 Get Your Backend URL
1. Go to "**Settings**" → "**Networking**"
2. You'll see a URL like: `datavint-production-xxxx.up.railway.app`
3. **Copy this URL** - you'll use it in Step 3

### 2.6 Add Custom Domain (Do this in Step 4)
1. Click "**+ Custom Domain**"
2. Enter: `api.datavint.io`
3. Railway will show you DNS records to add
4. **Keep this page open** - you'll need the DNS info

**Your backend is now live!** 🎉
Test it: `https://your-url.up.railway.app/api/docs`

---

## Step 3: Deploy Frontend to Vercel (5 minutes)

### 3.1 Install Vercel CLI
```bash
npm install -g vercel
```

### 3.2 Build and Deploy
```bash
cd client

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

Follow the prompts:
- Set up and deploy? **Y**
- Which scope? (Choose your account)
- Link to existing project? **N**
- Project name? `datavint`
- In which directory is your code? `./`
- Override build command? **N**
- Override output directory? **N**

### 3.3 Configure Custom Domain
1. Go to https://vercel.com/dashboard
2. Click on your `datavint` project
3. Go to "**Settings**" → "**Domains**"
4. Click "**Add**"
5. Enter: `datavint.io`
6. Also add: `www.datavint.io`
7. Vercel will show you DNS records
8. **Keep this page open** - you'll need these records

**Your frontend is now live!** 🎉
Test it: `https://datavint.vercel.app`

---

## Step 4: Configure DNS (1 hour to propagate)

Now we'll point datavint.io to your deployed apps.

### If using Namecheap:

1. Log in to Namecheap
2. Go to "**Domain List**" → Click "**Manage**" for datavint.io
3. Click "**Advanced DNS**" tab
4. Add these records:

**For Frontend (datavint.io):**
```
Type: A Record
Host: @
Value: 76.76.21.21  (Vercel's IP - check your Vercel dashboard)
TTL: Automatic

Type: CNAME Record
Host: www
Value: cname.vercel-dns.com
TTL: Automatic
```

**For Backend (api.datavint.io):**
```
Type: CNAME Record
Host: api
Value: datavint-production-xxxx.up.railway.app  (from Railway)
TTL: Automatic
```

### If using Cloudflare:

1. Go to Cloudflare dashboard
2. Click on datavint.io domain
3. Go to "**DNS**" → "**Records**"
4. Add the same records as above
5. **Turn OFF orange cloud** (proxy) for api.datavint.io initially
6. Can enable later after testing

**DNS takes 10 minutes to 1 hour to propagate.**

---

## Step 5: Update Environment Variables (2 minutes)

### 5.1 Update Frontend
The frontend is already configured to use `https://api.datavint.io`

Check: `client/.env.production` should have:
```bash
VITE_API_URL=https://api.datavint.io
```

### 5.2 Rebuild Frontend with New Config
```bash
cd client
npm run build
vercel --prod
```

This redeploys with the correct API URL.

---

## Step 6: Test Everything (5 minutes)

### Test Backend API
```bash
curl https://api.datavint.io/
```

Should return:
```json
{
  "service": "DataVint API",
  "version": "0.2.0",
  "status": "healthy"
}
```

### Test API Docs
Visit: https://api.datavint.io/api/docs
Should show FastAPI Swagger UI

### Test Frontend
1. Visit: https://datavint.io
2. Should load with white Apple-style theme
3. Open browser DevTools (F12) → Console
4. Should see: `[API] GET /...` logs

### Test Full Flow
1. Go to **Data** tab
2. Upload a CSV file (try `playground/raw_data/day2.csv`)
3. Should see preview table
4. Click "**View Analysis →**"
5. Should navigate to **Visualization** tab
6. Should see summary cards with issue counts
7. Check console for any CORS errors

---

## Troubleshooting

### Frontend loads but API calls fail (CORS error)
**Check:**
```bash
# Verify CORS settings in server/api/main.py includes:
allow_origins=[
    "https://datavint.io",
    "https://www.datavint.io",
]
```

**Fix:**
```bash
git add server/api/main.py
git commit -m "fix: update CORS for datavint.io"
git push
```
Railway will auto-redeploy.

### DNS not resolving
**Check DNS propagation:**
```bash
dig datavint.io
dig api.datavint.io
```

Should show A/CNAME records pointing to Vercel/Railway.

**If still showing old/no records:**
- Wait 15-30 more minutes
- Clear browser cache: Cmd+Shift+R
- Try incognito mode

### Railway deployment fails
**Check logs:**
1. Go to Railway dashboard
2. Click your service
3. Click "**Deployments**" → Latest deployment
4. Click "**View Logs**"

**Common issues:**
- Missing dependencies → Check `server/requirements.txt`
- Wrong Python version → Add `PYTHON_VERSION=3.9` in Variables
- Wrong start command → Should be `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### Vercel deployment fails
**Check build logs:**
```bash
vercel logs
```

**Common issues:**
- Missing node_modules → Run `npm install` first
- Wrong directory → Make sure you're in `client/` folder
- Build errors → Run `npm run build` locally first to debug

---

## Cost Breakdown

- **Domain (datavint.io)**: $35-40/year (~$3/month)
- **Railway backend**: $5/month (or free tier for testing)
- **Vercel frontend**: FREE
- **SSL certificates**: FREE (auto-included)

**Total: ~$8/month** 💰

---

## Post-Deployment

### Enable Auto-Deploy
Both Railway and Vercel support auto-deploy on git push:

**Railway:**
- Already enabled by default
- Every push to `main` triggers a new deployment

**Vercel:**
- Already enabled by default
- Every push to `main` triggers a new deployment
- Can configure in Vercel dashboard → Settings → Git

### Monitor Your App
**Railway dashboard:**
- View logs: Deployments → View Logs
- Monitor resources: Metrics tab
- Set up alerts: Settings → Notifications

**Vercel dashboard:**
- View logs: Deployments → Function Logs
- Monitor performance: Analytics tab
- View errors: Real-time Logs

### Optional: Add Custom Error Pages
Create `client/public/404.html` for better error handling.

---

## Next Steps

### After deployment works:
1. ✅ Add Google Analytics
2. ✅ Set up error tracking (Sentry)
3. ✅ Add a landing page with features/pricing
4. ✅ Enable caching (Cloudflare CDN)
5. ✅ Set up monitoring/uptime checks

### Share your app:
- Twitter: "Just launched datavint.io - AI-powered data quality for ML pipelines"
- Show HN: "Show HN: DataVint - Open source data quality validation"
- Reddit: r/machinelearning, r/datascience

---

## Quick Commands Reference

```bash
# Build locally
./deploy.sh

# Deploy frontend
cd client && vercel --prod

# Check backend logs
# (Use Railway dashboard)

# Test API
curl https://api.datavint.io/

# Test frontend
open https://datavint.io

# Check DNS
dig datavint.io
dig api.datavint.io
```

---

## Support Links

- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Namecheap Support**: https://www.namecheap.com/support/
- **DataVint Issues**: https://github.com/duochen13/datavint/issues

---

**Good luck with your launch! 🚀**

Questions? Open an issue or check the full DEPLOYMENT.md guide.
