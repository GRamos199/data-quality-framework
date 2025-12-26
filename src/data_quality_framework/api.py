"""
FastAPI wrapper for Data Quality Framework
Provides REST API endpoints for validation operations
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import json
import logging
from datetime import datetime
from io import StringIO

from data_quality_framework.orchestrator import QualityCheckOrchestrator
from data_quality_framework.config_loader import ConfigLoader
from data_quality_framework.exceptions import ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Data Quality Framework API",
    description="REST API for data quality validation and monitoring",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ValidationRequest(BaseModel):
    """Request model for validation"""
    dataset_name: str
    layer: str
    config_path: str
    data: Dict[str, Any]
    stop_on_failure: bool = True

class ValidationResponse(BaseModel):
    """Response model for validation results"""
    passed: bool
    dataset_name: str
    layer: str
    errors: Dict[str, List[str]]
    warnings: List[str]
    timestamp: str
    execution_time_seconds: float

class ConfigRequest(BaseModel):
    """Request model for config operations"""
    config_path: str

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str

# Endpoints

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="0.1.0"
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest
    return generate_latest()

@app.post("/validate/dict", response_model=ValidationResponse)
async def validate_dict(request: ValidationRequest):
    """
    Validate data from dictionary
    
    Args:
        request: Validation request containing dataset, layer, config path, and data
    
    Returns:
        ValidationResponse with validation results
    """
    try:
        start_time = datetime.utcnow()
        
        # Load configuration
        config = ConfigLoader.load_yaml(request.config_path)
        
        # Convert dict to DataFrame
        df = pd.DataFrame([request.data])
        
        # Run validation
        orchestrator = QualityCheckOrchestrator()
        result = orchestrator.run_checks(
            data=df,
            validators=[],  # Will build from config
            dataset_name=request.dataset_name,
            layer=request.layer,
            stop_on_failure=request.stop_on_failure
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return ValidationResponse(
            passed=result.passed,
            dataset_name=request.dataset_name,
            layer=request.layer,
            errors=result.errors,
            warnings=[],
            timestamp=datetime.utcnow().isoformat(),
            execution_time_seconds=execution_time
        )
    
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/validate/json")
async def validate_json(
    file: UploadFile = File(...),
    config_path: str = "config/openweather_raw_validation.yaml",
    dataset_name: str = "dataset",
    layer: str = "raw"
):
    """
    Validate data from JSON file
    
    Args:
        file: JSON file upload
        config_path: Path to validation config
        dataset_name: Dataset name
        layer: Data layer (raw, clean, etc.)
    
    Returns:
        ValidationResponse with results
    """
    try:
        start_time = datetime.utcnow()
        
        # Read JSON file
        content = await file.read()
        data = json.loads(content)
        
        # Convert to DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError("JSON must be object or array of objects")
        
        # Load configuration
        config = ConfigLoader.load_yaml(config_path)
        
        # Run validation
        orchestrator = QualityCheckOrchestrator()
        result = orchestrator.run_checks(
            data=df,
            validators=[],
            dataset_name=dataset_name,
            layer=layer,
            stop_on_failure=True
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "passed": result.passed,
            "dataset_name": dataset_name,
            "layer": layer,
            "errors": result.errors,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time_seconds": execution_time
        }
    
    except Exception as e:
        logger.error(f"JSON validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/validate/csv")
async def validate_csv(
    file: UploadFile = File(...),
    config_path: str = "config/openweather_raw_validation.yaml",
    dataset_name: str = "dataset",
    layer: str = "raw"
):
    """
    Validate data from CSV file
    
    Args:
        file: CSV file upload
        config_path: Path to validation config
        dataset_name: Dataset name
        layer: Data layer
    
    Returns:
        Validation results
    """
    try:
        start_time = datetime.utcnow()
        
        # Read CSV file
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode()))
        
        # Load configuration
        config = ConfigLoader.load_yaml(config_path)
        
        # Run validation
        orchestrator = QualityCheckOrchestrator()
        result = orchestrator.run_checks(
            data=df,
            validators=[],
            dataset_name=dataset_name,
            layer=layer,
            stop_on_failure=True
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "passed": result.passed,
            "dataset_name": dataset_name,
            "layer": layer,
            "rows_validated": len(df),
            "errors": result.errors,
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time_seconds": execution_time
        }
    
    except Exception as e:
        logger.error(f"CSV validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/configs")
async def list_configs():
    """List available validation configurations"""
    from pathlib import Path
    
    config_dir = Path("config")
    if not config_dir.exists():
        return {"configs": []}
    
    configs = [f.stem for f in config_dir.glob("*.yaml")]
    return {"configs": configs}

@app.get("/config/{config_name}")
async def get_config(config_name: str):
    """Get configuration details"""
    try:
        config = ConfigLoader.load_yaml(f"config/{config_name}.yaml")
        return config
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Config not found: {str(e)}")

@app.post("/validate/batch")
async def validate_batch(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config_path: str = "config/openweather_raw_validation.yaml",
    dataset_name: str = "dataset",
    layer: str = "raw"
):
    """
    Validate large batch of records (background task)
    
    Args:
        file: JSON/CSV file with multiple records
        config_path: Validation config path
        dataset_name: Dataset name
        layer: Data layer
    
    Returns:
        Task ID for tracking
    """
    task_id = f"{dataset_name}_{datetime.utcnow().timestamp()}"
    
    # Add background task
    background_tasks.add_task(
        run_batch_validation,
        file_content=await file.read(),
        config_path=config_path,
        dataset_name=dataset_name,
        layer=layer,
        task_id=task_id
    )
    
    return {"task_id": task_id, "status": "queued"}

async def run_batch_validation(
    file_content: bytes,
    config_path: str,
    dataset_name: str,
    layer: str,
    task_id: str
):
    """Run batch validation in background"""
    try:
        logger.info(f"Starting batch validation: {task_id}")
        
        # Parse file
        data = json.loads(file_content)
        if isinstance(data, dict):
            data = [data]
        
        df = pd.DataFrame(data)
        
        # Load config and run validation
        config = ConfigLoader.load_yaml(config_path)
        orchestrator = QualityCheckOrchestrator()
        
        result = orchestrator.run_checks(
            data=df,
            validators=[],
            dataset_name=dataset_name,
            layer=layer,
            stop_on_failure=False
        )
        
        logger.info(f"Batch validation completed: {task_id}")
        
    except Exception as e:
        logger.error(f"Batch validation failed: {task_id}, Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
