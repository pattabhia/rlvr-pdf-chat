"""
Training Data Service - FastAPI REST API

Provides endpoints for:
- Listing datasets
- Getting dataset statistics
- Querying training data entries
- Exporting to different formats (DPO, SFT, JSONL)
"""

import os
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from src.models import (
    DatasetListResponse,
    DatasetStats,
    TrainingDataEntryResponse,
    ExportRequest,
    ExportResponse,
    HealthResponse
)
from src.dataset_manager import DatasetManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Training Data Service",
    description="Manage and export training datasets for RLVR fine-tuning",
    version="1.0.0"
)

# Initialize dataset manager
dataset_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global dataset_manager
    
    logger.info("Starting Training Data Service...")
    
    # Load configuration from environment
    data_dir = os.getenv("DATA_DIR", "/app/data/training_data")
    
    # Initialize dataset manager
    dataset_manager = DatasetManager(data_dir=data_dir)
    
    logger.info("Training Data Service started successfully")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Training Data Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check with service status."""
    stats = dataset_manager.get_all_stats()
    
    return HealthResponse(
        status="healthy",
        data_directory=str(dataset_manager.data_dir),
        num_datasets=stats["total_datasets"],
        total_entries=stats["total_entries"]
    )


@app.get("/datasets", response_model=DatasetListResponse)
async def list_datasets():
    """
    List all training datasets with statistics.
    
    Returns:
        List of datasets with statistics
    """
    try:
        stats = dataset_manager.get_all_stats()
        return DatasetListResponse(**stats)
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/datasets/{file_name}/stats", response_model=DatasetStats)
async def get_dataset_stats(file_name: str):
    """
    Get statistics for a specific dataset.
    
    Args:
        file_name: Dataset file name
        
    Returns:
        Dataset statistics
    """
    try:
        stats = dataset_manager.get_dataset_stats(file_name)
        return stats
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get dataset stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entries", response_model=List[TrainingDataEntryResponse])
async def get_entries(
    file_name: Optional[str] = Query(None, description="Filter by file name"),
    min_verification_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum verification score"),
    min_reward_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum reward score"),
    domains: Optional[List[str]] = Query(None, description="Filter by domains"),
    limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of entries"),
    offset: int = Query(0, ge=0, description="Number of entries to skip")
):
    """
    Get training data entries with optional filtering.
    
    Args:
        file_name: Filter by specific file
        min_verification_score: Minimum verification score
        min_reward_score: Minimum reward score
        domains: Filter by domains
        limit: Maximum number of entries
        offset: Number of entries to skip
        
    Returns:
        List of training data entries
    """
    try:
        entries = dataset_manager.get_entries(
            file_name=file_name,
            min_verification_score=min_verification_score,
            min_reward_score=min_reward_score,
            domains=domains,
            limit=limit,
            offset=offset
        )
        return entries
    except Exception as e:
        logger.error(f"Failed to get entries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export", response_model=ExportResponse)
async def export_dataset(request: ExportRequest):
    """
    Export dataset to specified format.
    
    Supported formats:
    - dpo: Direct Preference Optimization (chosen/rejected pairs)
    - sft: Supervised Fine-Tuning (prompt/completion pairs)
    - jsonl: Filtered JSONL (standard format)
    
    Args:
        request: Export configuration
        
    Returns:
        Export response with file path
    """
    try:
        # Validate format
        if request.format not in ["dpo", "sft", "jsonl"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {request.format}. Must be one of: dpo, sft, jsonl"
            )
        
        # Export based on format
        if request.format == "dpo":
            export_file = dataset_manager.export_to_dpo(request)
        elif request.format == "sft":
            export_file = dataset_manager.export_to_sft(request)
        else:  # jsonl
            export_file = dataset_manager.export_to_jsonl(request)
        
        # Count entries in exported file
        num_entries = 0
        with open(export_file, "r", encoding="utf-8") as f:
            num_entries = sum(1 for _ in f)
        
        # Build filters applied
        filters_applied = {}
        if request.min_verification_score:
            filters_applied["min_verification_score"] = request.min_verification_score
        if request.min_reward_score:
            filters_applied["min_reward_score"] = request.min_reward_score
        if request.domains:
            filters_applied["domains"] = request.domains
        if request.file_name:
            filters_applied["file_name"] = request.file_name
        
        return ExportResponse(
            export_file=export_file,
            num_entries=num_entries,
            format=request.format,
            filters_applied=filters_applied
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

