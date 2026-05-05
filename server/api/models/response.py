"""
Pydantic response models
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecuteCodeResponse(BaseModel):
    """Response model for code execution"""
    success: bool
    execution_time: float
    output: Dict[str, Any]
    error: Optional[str] = None


class ValidateCodeResponse(BaseModel):
    """Response model for code validation"""
    valid: bool
    errors: List[str] = Field(default_factory=list)


class DataPreviewResponse(BaseModel):
    """Response model for data preview"""
    dataset_id: str
    total_rows: int
    columns: List[str]
    rows: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    """Response model for statistics"""
    dataset_id: str
    statistics: Dict[str, Any]


class IssueItem(BaseModel):
    """Individual issue model"""
    type: str
    feature: Optional[str]
    severity: str
    metric_value: float
    threshold: float
    description: str
    impact: Optional[Dict[str, str]] = None


class IssuesResponse(BaseModel):
    """Response model for issues"""
    dataset_id: str
    issues: List[IssueItem]
    summary: Dict[str, int]


class ManifestResponse(BaseModel):
    """Response model for manifest generation"""
    manifest: Dict[str, Any]
    improvements: Dict[str, Any]
