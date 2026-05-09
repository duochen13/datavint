"""
Playground tab API routes
"""

import time
import sys
from io import StringIO
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..models.request import ExecuteCodeRequest, ValidateCodeRequest
from ..models.response import ExecuteCodeResponse, ValidateCodeResponse

router = APIRouter()


@router.post("/execute", response_model=ExecuteCodeResponse)
async def execute_code(request: ExecuteCodeRequest):
    """
    Execute DataVint code and return results

    This endpoint runs the provided Python code in a controlled environment
    and captures the output, statistics, and any detected issues.
    """
    start_time = time.time()

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    # Local namespace for execution
    local_namespace: Dict[str, Any] = {}

    try:
        # Import datavint into the execution namespace
        import datavint as dv
        local_namespace['dv'] = dv

        # Execute user code
        exec(request.code, local_namespace)

        # Get captured output
        stdout_output = captured_output.getvalue()

        # Extract statistics and issues if they exist
        statistics = None
        issues = None

        if 'train_stats' in local_namespace:
            stats_obj = local_namespace['train_stats']
            statistics = {
                'n_rows': stats_obj.n_rows,
                'n_cols': stats_obj.n_cols,
                'label_rate': stats_obj.label_rate,
                'duplicate_rate': stats_obj.duplicate_rate,
            }

        if 'issues' in local_namespace:
            issues_list = local_namespace['issues']
            issues = [
                {
                    'type': issue.type.value,
                    'feature': issue.feature,
                    'severity': issue.severity.value,
                    'description': issue.description,
                    'metric_value': issue.metric_value
                }
                for issue in issues_list
            ]

        execution_time = time.time() - start_time

        return ExecuteCodeResponse(
            success=True,
            execution_time=round(execution_time, 3),
            output={
                'stdout': stdout_output,
                'statistics': statistics,
                'issues': issues
            },
            error=None
        )

    except Exception as e:
        execution_time = time.time() - start_time
        return ExecuteCodeResponse(
            success=False,
            execution_time=round(execution_time, 3),
            output={'stdout': captured_output.getvalue()},
            error=str(e)
        )

    finally:
        sys.stdout = old_stdout


@router.post("/validate", response_model=ValidateCodeResponse)
async def validate_code(request: ValidateCodeRequest):
    """
    Validate Python code syntax without executing

    Checks for syntax errors and basic issues before execution.
    """
    errors = []

    try:
        # Try to compile the code
        compile(request.code, '<string>', 'exec')
        return ValidateCodeResponse(valid=True, errors=[])

    except SyntaxError as e:
        errors.append(f"Syntax error on line {e.lineno}: {e.msg}")
        return ValidateCodeResponse(valid=False, errors=errors)

    except Exception as e:
        errors.append(str(e))
        return ValidateCodeResponse(valid=False, errors=errors)
