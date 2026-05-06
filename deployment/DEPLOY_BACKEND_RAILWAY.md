# Deploy Backend API to Railway

**Quick guide to fix the 500 error on datavint.io/playground**

## 🔴 The Problem

Your frontend at `datavint.io/playground` is trying to call `https://api.datavint.io` but this backend doesn't exist yet!

```
✅ Localhost:  localhost:5173 → localhost:8000 (works)
❌ Production: datavint.io/playground → api.datavint.io (doesn't exist)
```

## ⏱️ Time Required: 15 minutes

---

## Step 1: Create Railway Account (2 min)

1. Go to: **https://railway.app**
2. Click **"Start a New Project"** or **"Sign up with GitHub"**
3. Authorize Railway to access your GitHub repos
4. You'll get **$5 free credit** (enough for testing)

---

## Step 2: Deploy Backend from GitHub (5 min)

### 2.1 Create New Project

1. In Railway dashboard, click **"+ New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose repository: **`duochen13/datavint`**
4. Railway will auto-detect Python ✅

### 2.2 Configure Service Settings

1. Click on the deployed service card
2. Go to **"Settings"** tab
3. Scroll to **"Service Settings"**
4. Configure:
   ```
   Root Directory: server
   Start Command: uvicorn api.main:app --host 0.0.0.0 --port $PORT
   ```

### 2.3 Add Environment Variables

1. Go to **"Variables"** tab
2. Click **"+ New Variable"**
3. Add these:
   ```
   PORT=8000
   PYTHON_VERSION=3.9
   ```

### 2.4 Wait for Deployment

Railway will:
1. Install dependencies from `server/requirements.txt`
2. Start the FastAPI server
3. Assign a public URL

**Status:** Watch the logs tab - should show "Uvicorn running on..."

---

## Step 3: Get Your Backend URL (1 min)

1. Go to **"Settings"** → **"Networking"**
2. Under **"Public Networking"**, you'll see:
   ```
   https://datavint-production-xxxx.up.railway.app
   ```
3. **Copy this URL**
4. Test it by visiting:
   ```
   https://your-url.up.railway.app/docs
   ```
   You should see the FastAPI Swagger documentation ✅

---

## Step 4: Add Custom Domain (5 min)

### 4.1 Add Domain in Railway

1. In Railway service settings, go to **"Networking"**
2. Click **"+ Custom Domain"**
3. Enter: `api.datavint.io`
4. Railway will show DNS records like:
   ```
   Type: CNAME
   Name: api
   Value: xxxx.railway.app
   ```
5. **Keep this page open**

### 4.2 Add DNS Record in Namecheap

1. Go to: **https://ap.www.namecheap.com/domains/domaincontrolpanel**
2. Find **datavint.io**, click **"Manage"**
3. Go to **"Advanced DNS"** tab
4. Click **"Add New Record"**:
   ```
   Type: CNAME Record
   Host: api
   Value: [paste Railway value from step 4.1]
   TTL: Automatic
   ```
5. Click **"Save All Changes"**

### 4.3 Wait for DNS Propagation

**Time:** 5-20 minutes

Check status:
```bash
dig api.datavint.io +short
# Should show Railway's CNAME
```

Or visit: https://dnschecker.org/#CNAME/api.datavint.io

---

## Step 5: Update Frontend Environment (Already Done ✅)

Your `client/.env.production` already has:
```
VITE_API_URL=https://api.datavint.io
```

So once DNS propagates, **it will just work!** 🎉

---

## Step 6: Rebuild and Redeploy Frontend (2 min)

Since you updated the backend URL, rebuild the frontend:

```bash
# Rebuild the site
npm run build

# Or trigger Vercel redeploy
git commit --allow-empty -m "chore: trigger rebuild for backend connection"
git push
```

Vercel will auto-deploy in ~1 minute.

---

## ✅ Testing

Once DNS propagates and Vercel redeploys:

### Test Backend API
```bash
curl https://api.datavint.io/docs
# Should return HTML (FastAPI docs)
```

### Test Frontend → Backend Connection
1. Go to: **https://www.datavint.io/playground**
2. Upload a CSV file
3. Should work! ✅

### Check CORS
The backend already has CORS configured for:
```python
allow_origins=[
    "https://datavint.io",
    "https://www.datavint.io",
    "https://api.datavint.io",
]
```

---

## 💰 Railway Pricing

**Free tier:**
- $5 credit (lasts ~1 month for small projects)
- No credit card required

**Paid tier ($5/month):**
- After free credit runs out
- Includes:
  - 500 hours execution time
  - 5GB storage
  - Custom domains

**Estimated cost for DataVint:** $5-8/month

---

## 🔍 Troubleshooting

### "Module not found" error
**Fix:** Check `server/requirements.txt` includes all dependencies:
```bash
cd server
pip freeze > requirements.txt
git add requirements.txt
git commit -m "chore: update requirements.txt"
git push
```

### "Port binding error"
**Fix:** Make sure start command uses `$PORT`:
```
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### "CORS error" in browser
**Fix:** Check `server/api/main.py` CORS settings include your domain:
```python
allow_origins=[
    "https://datavint.io",
    "https://www.datavint.io",
]
```

### Railway URL works but custom domain doesn't
**Fix:**
1. Check DNS propagation: `dig api.datavint.io`
2. Wait 10-20 minutes
3. Clear browser cache (Cmd+Shift+R)

### 500 error persists after deployment
**Fix:**
1. Check Railway logs for errors
2. Test Railway URL directly first
3. Make sure frontend rebuilt after backend deployed

---

## 📊 Verification Checklist

- [ ] Railway project created
- [ ] Backend deployed and running
- [ ] Railway URL works (visit /docs)
- [ ] Custom domain added in Railway
- [ ] DNS CNAME record added in Namecheap
- [ ] DNS propagated (dig api.datavint.io)
- [ ] Frontend rebuilt and deployed
- [ ] Upload CSV works on datavint.io/playground

---

## 🆘 Quick Help

**Railway not deploying?**
```bash
# Check logs in Railway dashboard → Deployments → View Logs
```

**DNS not propagating?**
```bash
# Check status
dig api.datavint.io +short

# Check globally
# Visit: https://dnschecker.org/#CNAME/api.datavint.io
```

**Still getting 500 errors?**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Upload CSV and see which request fails
4. Share the error message

---

## 📝 Summary

After completing these steps:
- ✅ Backend API live at: `https://api.datavint.io`
- ✅ Frontend can upload CSVs and get results
- ✅ Full stack working end-to-end

**Total time:** 15-30 minutes (depending on DNS propagation)
