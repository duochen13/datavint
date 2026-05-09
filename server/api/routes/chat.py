"""
Chat API Routes - CSV upload and LLM-driven analysis

Provides endpoint for chat-driven custom data analysis:
- CSV file upload
- LLM code generation
- Code validation and execution
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import tempfile
import os
import pandas as pd
import logging

# Import datavint library
import datavint as vint

# Import shared utilities
from ..utils.rate_limit import rate_limiter
from ..utils.code_validator import validate_generated_code
from ..services.llm_client import generate_datavint_code

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class AnalysisResponse(BaseModel):
    """Response model for CSV analysis"""
    success: bool
    generated_code: str
    output: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/api/chat/analyze-csv", response_model=AnalysisResponse)
async def analyze_csv(
    file: UploadFile = File(...),
    prompt: str = Form("profile this dataset"),
    http_request: Request = None
):
    """
    Upload CSV + natural language prompt → LLM-generated code → Execution results

    MVP endpoint that combines upload, code generation, and execution in one call.

    Flow:
    1. Validate file (size, type, format)
    2. Check rate limit
    3. Save to temp file on disk
    4. Parse CSV to DataFrame
    5. Call Claude API with prompt + DataFrame metadata
    6. Validate generated code (AST + import whitelist)
    7. Execute code with DataFrame
    8. Return results + generated code
    9. Cleanup temp file

    Args:
        file: CSV file (max 10MB)
        prompt: Natural language description of desired analysis
        http_request: FastAPI Request for client IP (rate limiting)

    Returns:
        AnalysisResponse with generated code and profiling results

    Raises:
        HTTPException 400: Invalid file or CSV parsing error
        HTTPException 413: File too large
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Code generation or execution error
    """
    # Get client IP for rate limiting
    client_ip = http_request.client.host if http_request and http_request.client else "unknown"

    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        retry_after = rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported. Please upload a .csv file."
        )

    # Read file content and check size
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"File read error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(file_content) == 0:
        raise HTTPException(
            status_code=400,
            detail="File is empty. Please upload a valid CSV file with data."
        )

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({len(file_content) / (1024*1024):.1f}MB) exceeds {MAX_FILE_SIZE / (1024*1024)}MB limit."
        )

    # Save to temporary file
    temp_file = None
    temp_file_path = None

    try:
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False)
        temp_file.write(file_content)
        temp_file_path = temp_file.name
        temp_file.close()

        logger.info(f"CSV uploaded: {file.filename} ({len(file_content) / 1024:.1f} KB) → {temp_file_path}")

        # Parse CSV to DataFrame
        try:
            df = pd.read_csv(temp_file_path)
        except pd.errors.ParserError as e:
            logger.error(f"CSV parse error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid CSV format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"CSV read error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read CSV: {str(e)}"
            )

        logger.info(f"CSV parsed: {df.shape[0]} rows × {df.shape[1]} columns")

        # Prepare DataFrame metadata for LLM
        dataframe_info = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
        }

        # Generate code via Claude API
        try:
            generated_code = await generate_datavint_code(
                prompt=prompt,
                dataframe_info=dataframe_info
            )
            logger.info(f"Code generated ({len(generated_code)} chars)")
        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return AnalysisResponse(
                success=False,
                generated_code="",
                output="",
                error=f"Failed to generate code: {str(e)}"
            )

        # Validate generated code for security
        is_valid, validation_error = validate_generated_code(generated_code)
        if not is_valid:
            logger.warning(f"Code validation failed: {validation_error}")
            return AnalysisResponse(
                success=False,
                generated_code=generated_code,
                output="",
                error=f"Generated code failed security validation: {validation_error}"
            )

        logger.info("Code validation passed")

        # Execute code in restricted scope
        try:
            # Create restricted execution scope
            # Only df, vint, pd, np are available
            import numpy as np
            local_scope = {
                'df': df,
                'vint': vint,
                'pd': pd,
                'np': np
            }

            # Execute generated code
            exec(generated_code, {}, local_scope)

            # Extract results
            # Code should assign to 'result' variable
            if 'result' in local_scope:
                result_data = local_scope['result']
            # Fallback: check for stats/issues from vint.profile()
            elif 'stats' in local_scope and 'issues' in local_scope:
                stats = local_scope['stats']
                issues = local_scope['issues']

                # Convert Issue objects to dictionaries for JSON serialization
                serialized_issues = []
                if isinstance(issues, list):
                    for issue in issues:
                        if hasattr(issue, 'to_dict'):
                            serialized_issues.append(issue.to_dict())
                        else:
                            serialized_issues.append(issue)

                # Convert DatasetStatistics to dict if available
                serialized_stats = stats.to_dict() if hasattr(stats, 'to_dict') else stats

                result_data = {
                    'stats': serialized_stats,
                    'issues': serialized_issues
                }
            else:
                # No explicit result variable found
                result_data = {
                    'message': 'Analysis completed (no explicit result returned)'
                }

            logger.info("Code execution successful")

            # Format success response
            output_message = (
                f"✅ Analysis complete\n"
                f"Dataset: {file.filename}\n"
                f"Shape: {df.shape[0]} rows × {df.shape[1]} columns"
            )

            # Add issue count if available
            if isinstance(result_data, dict) and 'issues' in result_data:
                issues = result_data['issues']
                if isinstance(issues, list):
                    issue_count = len(issues)
                    output_message += f"\nData quality issues found: {issue_count}"

                    # Add severity breakdown
                    if issue_count > 0:
                        high_count = sum(1 for i in issues if isinstance(i, dict) and i.get('severity') == 'HIGH')
                        if high_count > 0:
                            output_message += f"\n⚠ {high_count} HIGH severity issue(s) detected"

            return AnalysisResponse(
                success=True,
                generated_code=generated_code,
                output=output_message,
                data=result_data
            )

        except Exception as e:
            logger.error(f"Code execution error: {e}", exc_info=True)
            return AnalysisResponse(
                success=False,
                generated_code=generated_code,
                output="",
                error=f"Execution failed: {str(e)}"
            )

    finally:
        # Cleanup: Delete temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Temp file deleted: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to delete temp file {temp_file_path}: {e}")


@router.get("/api/chat/health")
async def chat_health():
    """
    Health check endpoint for chat analysis service.

    Returns:
        dict: Service status and configuration
    """
    import sys

    # Check if Anthropic API key is configured
    anthropic_configured = bool(os.environ.get("ANTHROPIC_API_KEY"))

    return {
        "service": "chat-analysis",
        "status": "healthy",
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "rate_limit": "10 requests per 60 seconds per IP",
        "anthropic_configured": anthropic_configured,
        "python_version": sys.version
    }
