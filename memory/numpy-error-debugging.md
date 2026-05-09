# NumPy Boolean Subtract Error - Debugging

**Date**: 2026-05-08
**Issue**: Error in chatbox when checking missing values

## Error Message
```
❌ Analysis failed: Execution failed: numpy boolean subtract, the `-` operator,
is not supported, use the bitwise_xor, the `^` operator, or the logical_xor function instead.
```

## Investigation Results

**Local tests (all passed):**
- NumPy 2.0.2 + Pandas 2.3.3
- All boolean operations work fine
- DataVint detectors work correctly
- LLM-generated code patterns compatible

**Conclusion:** Environment-specific issue on Railway deployment

## Diagnostic Endpoints Added

1. `GET /api/diagnostics/numpy` - Tests NumPy boolean operations
2. `GET /api/diagnostics/env` - Shows environment info

## Next Steps

1. Deploy to Railway
2. Visit `/api/diagnostics/numpy` on production
3. Check which specific test fails
4. Apply targeted fix based on results

## Possible Fixes

1. Pin NumPy version in requirements.txt
2. Update LLM system prompt to avoid boolean subtraction
3. Add NumPy compatibility layer if needed
