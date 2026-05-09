"""
Diagnostic Routes - Help debug NumPy compatibility and environment issues
"""
from fastapi import APIRouter
import pandas as pd
import numpy as np
import sys

router = APIRouter()


@router.get("/api/diagnostics/numpy")
async def numpy_diagnostics():
    """
    Test NumPy boolean operations to detect compatibility issues.

    This endpoint helps debug the NumPy 2.0 boolean subtract error that
    some users are experiencing.
    """
    diagnostics = {
        "environment": {
            "python_version": sys.version,
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
        },
        "tests": []
    }

    # Test 1: Boolean pandas Series subtraction
    try:
        df = pd.DataFrame({'a': [1, None, 3]})
        null_mask = df['a'].isnull()
        result = 1 - null_mask
        diagnostics["tests"].append({
            "name": "Boolean pandas Series subtraction (1 - Series)",
            "status": "✅ PASS",
            "result": result.tolist()
        })
    except Exception as e:
        diagnostics["tests"].append({
            "name": "Boolean pandas Series subtraction",
            "status": "❌ FAIL",
            "error": str(e)
        })

    # Test 2: Boolean DataFrame subtraction
    try:
        df = pd.DataFrame({'a': [1, None, 3], 'b': [10, 20, None]})
        null_mask = df.isnull()
        result = 1 - null_mask
        diagnostics["tests"].append({
            "name": "Boolean DataFrame subtraction (1 - DataFrame)",
            "status": "✅ PASS",
            "result": "Shape: " + str(result.shape)
        })
    except Exception as e:
        diagnostics["tests"].append({
            "name": "Boolean DataFrame subtraction",
            "status": "❌ FAIL",
            "error": str(e)
        })

    # Test 3: NumPy boolean array subtraction
    try:
        bool_array = np.array([True, False, True])
        result = 1 - bool_array
        diagnostics["tests"].append({
            "name": "NumPy boolean array subtraction (1 - np.array)",
            "status": "✅ PASS",
            "result": result.tolist()
        })
    except Exception as e:
        diagnostics["tests"].append({
            "name": "NumPy boolean array subtraction",
            "status": "❌ FAIL",
            "error": str(e)
        })

    # Test 4: Completeness calculation (from detectors)
    try:
        df = pd.DataFrame({'a': [1, None, 3, 4, 5]})
        completeness = 1 - (df.isnull().sum() / len(df))
        diagnostics["tests"].append({
            "name": "Completeness calculation (1 - null_rate)",
            "status": "✅ PASS",
            "result": completeness.to_dict()
        })
    except Exception as e:
        diagnostics["tests"].append({
            "name": "Completeness calculation",
            "status": "❌ FAIL",
            "error": str(e)
        })

    # Test 5: DataVint profile() call
    try:
        import datavint as vint
        df = pd.DataFrame({
            'feature1': [1, 2, None, 4, 5],
            'feature2': [10, None, None, 40, 50],
        })
        stats, issues = vint.profile(df)
        diagnostics["tests"].append({
            "name": "datavint.profile() execution",
            "status": "✅ PASS",
            "result": f"{len(issues)} issues found"
        })
    except Exception as e:
        diagnostics["tests"].append({
            "name": "datavint.profile() execution",
            "status": "❌ FAIL",
            "error": str(e)
        })

    # Count pass/fail
    passed = sum(1 for t in diagnostics["tests"] if t["status"] == "✅ PASS")
    failed = sum(1 for t in diagnostics["tests"] if t["status"] == "❌ FAIL")

    diagnostics["summary"] = {
        "total": len(diagnostics["tests"]),
        "passed": passed,
        "failed": failed,
        "status": "✅ ALL TESTS PASSED" if failed == 0 else f"❌ {failed} TESTS FAILED"
    }

    return diagnostics


@router.get("/api/diagnostics/env")
async def environment_info():
    """
    Return complete environment information for debugging.
    """
    import platform
    import datavint as vint

    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
        },
        "packages": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "datavint": vint.__version__ if hasattr(vint, '__version__') else "unknown",
        },
        "python_path": sys.path,
        "executable": sys.executable
    }
