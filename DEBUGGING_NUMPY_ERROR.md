# Debugging NumPy Boolean Subtract Error

## Problem

You're seeing this error when using the chatbox to check missing values:

```
❌ Analysis failed: Execution failed: numpy boolean subtract, the `-` operator,
is not supported, use the bitwise_xor, the `^` operator, or the logical_xor function instead.
```

## Root Cause

This error is specific to **NumPy 2.0+** when using the `-` operator on boolean arrays. However, all local tests pass, suggesting this is an environment-specific issue on Railway.

## Diagnostic Steps

### 1. Check Your Production Environment

Visit these endpoints in your deployed Railway app:

**Environment Info:**
```
https://your-app.railway.app/api/diagnostics/env
```

**NumPy Compatibility Tests:**
```
https://your-app.railway.app/api/diagnostics/numpy
```

### 2. Analyze the Results

The `/api/diagnostics/numpy` endpoint runs 5 tests:

1. ✅ Boolean pandas Series subtraction
2. ✅ Boolean DataFrame subtraction
3. ✅ NumPy boolean array subtraction
4. ✅ Completeness calculation
5. ✅ DataVint profile() execution

If any test fails, the error message will tell you exactly what's failing.

### 3. Compare Versions

Check if Railway is using a different NumPy version than expected:

**Local (working):**
- NumPy: 2.0.2
- Pandas: 2.3.3

**Railway (check via `/api/diagnostics/env`):**
- NumPy: ?
- Pandas: ?

## Possible Fixes

### Fix 1: Pin NumPy Version

If Railway is using a different NumPy version, pin it in `requirements.txt`:

```txt
numpy==2.0.2
```

### Fix 2: Update Generated Code

If the LLM is generating code with boolean subtraction, update the system prompt in `server/api/services/llm_client.py` to avoid boolean operations:

Replace:
```python
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
```

With:
```python
missing_pct = (df.isnull().mean() * 100).round(2)
```

### Fix 3: Check for Hidden Boolean Operations

Search for any code using `-` on boolean masks:

```bash
grep -r "1 - df\\.isnull" .
grep -r "~" datavint/
```

## Testing Locally

Run this command to test all NumPy operations:

```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from server.api.routes.diagnostics import numpy_diagnostics
import asyncio
result = asyncio.run(numpy_diagnostics())
print(result)
"
```

## Next Steps

1. Deploy this diagnostic code to Railway
2. Visit the diagnostic endpoints
3. Share the results here
4. I'll provide a targeted fix based on what fails
