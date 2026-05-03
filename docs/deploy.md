# Deploy HeptaAI Website

## Option 1: GitHub Pages (Free, Easy, Recommended)

### Steps:
1. **Commit and push website to GitHub**:
   ```bash
   cd /Users/duochen/Desktop/career/heptaAI
   git add website/
   git commit -m "Add HeptaAI landing page website"
   git push origin main
   ```

2. **Enable GitHub Pages**:
   - Go to https://github.com/duochen13/hepta-ai/settings/pages
   - Under "Source", select "Deploy from a branch"
   - Choose branch: `main`
   - Choose folder: `/website`
   - Click "Save"

3. **Your site will be live at**:
   ```
   https://duochen13.github.io/hepta-ai/
   ```

   Or with custom domain:
   ```
   https://heptaai.com
   ```

**Time to deploy**: ~2 minutes

---

## Option 2: Netlify (Easiest, Drag & Drop)

### Steps:
1. Go to https://app.netlify.com/drop
2. Drag the entire `/website` folder to the browser
3. Your site will be instantly live at a URL like:
   ```
   https://[random-name].netlify.app
   ```

4. **Optional**: Change to custom domain:
   - Click "Domain settings"
   - Add custom domain: `heptaai.com`

**Time to deploy**: ~30 seconds

---

## Option 3: Vercel (Professional, Fast)

### Steps:
1. **Login to Vercel**:
   ```bash
   vercel login
   ```

2. **Deploy**:
   ```bash
   cd /Users/duochen/Desktop/career/heptaAI/website
   vercel --prod
   ```

3. Your site will be live at:
   ```
   https://[project-name].vercel.app
   ```

**Time to deploy**: ~1 minute

---

## Option 4: Surge.sh (Simple, Command Line)

### Steps:
1. **Create account (one-time)**:
   ```bash
   surge login
   ```
   Enter your email and choose a password.

2. **Deploy**:
   ```bash
   cd /Users/duochen/Desktop/career/heptaAI/website
   surge . heptaai.surge.sh
   ```

3. Your site will be live at:
   ```
   https://heptaai.surge.sh
   ```

**Time to deploy**: ~30 seconds

---

## Quick Deploy Script

I've created a script to deploy to GitHub Pages automatically:

```bash
#!/bin/bash
cd /Users/duochen/Desktop/career/heptaAI
git add website/
git commit -m "Deploy HeptaAI landing page"
git push origin main
echo "✅ Pushed to GitHub!"
echo "📝 Now enable GitHub Pages at: https://github.com/duochen13/hepta-ai/settings/pages"
echo "🌐 Your site will be live at: https://duochen13.github.io/hepta-ai/"
```

---

## Recommended: GitHub Pages

**Why GitHub Pages?**
- ✅ Free forever
- ✅ Custom domain support (heptaai.com)
- ✅ HTTPS by default
- ✅ Integrated with your existing repo
- ✅ Easy to update (just push to git)

**After enabling GitHub Pages**, your website will be accessible at:
```
https://duochen13.github.io/hepta-ai/
```

To use a custom domain like `heptaai.com`:
1. Add a CNAME file with your domain
2. Configure DNS with your domain registrar
3. Enable custom domain in GitHub Pages settings
