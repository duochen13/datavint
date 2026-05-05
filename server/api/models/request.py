"""
Pydantic request models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ExecuteCodeRequest(BaseModel):
    """Request model for code execution"""
    code: str = Field(..., description="Python code to execute")
    dataset: Optional[str] = Field(None, description="Dataset ID to use")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution options")


class ValidateCodeRequest(BaseModel):
    """Request model for code validation"""
    code: str = Field(..., description="Python code to validate")


class UploadDataRequest(BaseModel):
    """Request model for data upload (multipart form will override this)"""
    label_col: Optional[str] = Field(None, description="Label column name")
