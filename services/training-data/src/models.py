"""
Data models for Training Data Service

Defines Pydantic models for training data entries and datasets.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class VerificationScores(BaseModel):
    """Verification scores from RAGAS"""
    faithfulness: float = Field(..., ge=0.0, le=1.0, description="Faithfulness score")
    relevancy: float = Field(..., ge=0.0, le=1.0, description="Relevancy score")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall verification score")
    confidence: str = Field(..., description="Confidence level (high, medium, low)")
    issues: List[str] = Field(default_factory=list, description="List of issues found")


class RewardScores(BaseModel):
    """Reward scores from reward computation"""
    score: float = Field(..., ge=0.0, le=1.0, description="Reward score")
    domain: str = Field(..., description="Domain name")
    has_ground_truth: bool = Field(..., description="Whether ground truth was found")
    reward_type: str = Field(..., description="Type of reward computation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional reward details")


class TrainingDataEntry(BaseModel):
    """Training data entry"""
    timestamp: str = Field(..., description="ISO timestamp")
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")
    contexts: List[str] = Field(default_factory=list, description="Context strings")
    verification: VerificationScores = Field(..., description="Verification scores")
    reward: RewardScores = Field(..., description="Reward scores")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TrainingDataEntryResponse(TrainingDataEntry):
    """Training data entry with ID"""
    entry_id: str = Field(..., description="Unique entry ID (line number in file)")
    file_name: str = Field(..., description="Source file name")


class DatasetStats(BaseModel):
    """Statistics about a dataset"""
    file_name: str = Field(..., description="Dataset file name")
    num_entries: int = Field(..., description="Number of entries")
    date_range: Dict[str, Optional[str]] = Field(..., description="Date range (earliest, latest)")
    avg_verification_score: float = Field(..., description="Average verification score")
    avg_reward_score: float = Field(..., description="Average reward score")
    domains: List[str] = Field(default_factory=list, description="List of domains")
    file_size_bytes: int = Field(..., description="File size in bytes")


class DatasetListResponse(BaseModel):
    """Response for listing datasets"""
    datasets: List[DatasetStats] = Field(..., description="List of datasets")
    total_datasets: int = Field(..., description="Total number of datasets")
    total_entries: int = Field(..., description="Total number of entries across all datasets")


class DPOEntry(BaseModel):
    """DPO (Direct Preference Optimization) format entry"""
    prompt: str = Field(..., description="Prompt with context and question")
    chosen: str = Field(..., description="Chosen answer (high reward)")
    rejected: str = Field(..., description="Rejected answer (low reward)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExportRequest(BaseModel):
    """Request to export dataset in specific format"""
    format: str = Field(..., description="Export format (dpo, sft, jsonl)")
    file_name: Optional[str] = Field(None, description="Source file name (if None, export all)")
    min_verification_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum verification score")
    min_reward_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum reward score")
    domains: Optional[List[str]] = Field(None, description="Filter by domains")


class ExportResponse(BaseModel):
    """Response for export request"""
    export_file: str = Field(..., description="Path to exported file")
    num_entries: int = Field(..., description="Number of entries exported")
    format: str = Field(..., description="Export format")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    data_directory: str = Field(..., description="Data directory path")
    num_datasets: int = Field(..., description="Number of datasets")
    total_entries: int = Field(..., description="Total entries")

