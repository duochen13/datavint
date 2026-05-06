# Git Hooks Guide

## Pre-Commit Hook

A pre-commit hook is installed at `.git/hooks/pre-commit` that automatically checks for redundant or problematic files before allowing commits.

### What It Checks

#### 🚫 **Blocked (Commit will fail)**
- **Large files** (>100MB) - Too large for git, use Git LFS instead
- **Build outputs** - `dist/`, `client/dist/`, `node_modules/`, `__pycache__/`
- **Python bytecode** - `*.pyc`, `*.pyo`, `*.pyd`
- **Temporary files** - `*.tmp`, `*.temp`, `*~`, `*.swp`
- **OS files** - `.DS_Store`, `Thumbs.db`, `desktop.ini`

#### ⚠️ **Warnings (Requires confirmation)**
- **Medium files** (10-100MB) - Consider using Git LFS
- **Data files** - `*.csv`, `*.parquet`, `*.xlsx`
- **Environment files** - `.env`, `.env.local`, `.env.production`
- **Log files** - `*.log`, `logs/`
- **Duplicate documentation** - Same markdown filename appearing multiple times

### How to Use

**Normal commit** - The hook runs automatically:
```bash
git add .
git commit -m "your message"
# Hook will check files automatically
```

**If warnings appear:**
1. Review the warned files
2. Decide if they should be committed
3. Type `y` to proceed or `n` to cancel

**Bypass the hook** (not recommended):
```bash
git commit --no-verify -m "your message"
```

### Example Output

```bash
🔍 Checking for redundant files...

📏 Checking file sizes...
⚠️  WARNING: data/train.csv is 45MB (consider using Git LFS)

🚫 Checking for blocked patterns...
❌ BLOCKED: Build outputs or dependencies detected
   - node_modules/package/index.js
   - dist/bundle.js

📄 Checking for potential duplicate documentation...

❌ COMMIT BLOCKED: Fix the issues above before committing

To bypass this check (not recommended):
  git commit --no-verify
```

### Customization

Edit `.git/hooks/pre-commit` to:
- Change file size thresholds (currently 10MB warning, 100MB block)
- Add/remove blocked patterns
- Change warnings to hard blocks
- Add custom checks

### Best Practices

1. **Keep data out of git** - Use `.gitignore` for `*.csv`, `*.parquet` files
2. **Use Git LFS for large files** - Install with `git lfs install`
3. **Review .env files** - Never commit real API keys or secrets
4. **Clean before commit** - Run `npm run clean` or equivalent
5. **Check .gitignore** - Make sure build outputs are ignored

### Disabling the Hook

If you need to disable it temporarily:
```bash
mv .git/hooks/pre-commit .git/hooks/pre-commit.disabled
```

Re-enable:
```bash
mv .git/hooks/pre-commit.disabled .git/hooks/pre-commit
```

### Sharing With Team

To share this hook with your team, you can:

1. **Store in repo** (requires manual installation):
   ```bash
   mkdir -p scripts/git-hooks
   cp .git/hooks/pre-commit scripts/git-hooks/
   ```

   Team members install with:
   ```bash
   cp scripts/git-hooks/pre-commit .git/hooks/
   chmod +x .git/hooks/pre-commit
   ```

2. **Use Husky** (automatic installation):
   ```bash
   npm install --save-dev husky
   npx husky install
   npx husky add .husky/pre-commit "bash scripts/git-hooks/pre-commit"
   ```

### Related Files

- **`.gitignore`** - Prevents files from being tracked at all
- **`.vercelignore`** - Prevents files from being deployed to Vercel
- **`wiki/guides/SEVERITY_GUIDE.md`** - Data quality severity levels
