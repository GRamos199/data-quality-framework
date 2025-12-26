"""
Database models for validation history and audit trail
Using SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from typing import Optional

Base = declarative_base()

class ValidationRun(Base):
    """Model for storing validation run history"""
    __tablename__ = "validation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String, index=True)
    layer = Column(String, index=True)
    passed = Column(Boolean, default=False)
    execution_time_seconds = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    config_path = Column(String)
    errors = Column(JSON)
    warnings = Column(JSON)
    row_count = Column(Integer)
    
    def __repr__(self):
        return f"<ValidationRun(id={self.id}, dataset={self.dataset_name}, passed={self.passed})>"

class ValidationConfig(Base):
    """Model for storing validation configurations"""
    __tablename__ = "validation_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    dataset = Column(String)
    layer = Column(String)
    config_content = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ValidationConfig(id={self.id}, name={self.name})>"

class ValidationMetric(Base):
    """Model for storing validation metrics"""
    __tablename__ = "validation_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String, index=True)
    metric_value = Column(Float)
    dataset_name = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ValidationMetric(id={self.id}, name={self.metric_name})>"

class Database:
    """Database connection manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            database_url: PostgreSQL connection string.
                         If None, uses DATABASE_URL environment variable
        """
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://dqf_user:dqf_password@localhost:5432/dqf_dev"
            )
        
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all tables from the database"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    def add_validation_run(
        self,
        dataset_name: str,
        layer: str,
        passed: bool,
        execution_time: float,
        config_path: str,
        errors: dict,
        warnings: list = None,
        row_count: int = 0
    ) -> ValidationRun:
        """
        Add a validation run to the database
        
        Args:
            dataset_name: Name of the dataset
            layer: Data layer (raw, clean, etc.)
            passed: Whether validation passed
            execution_time: Time taken for validation
            config_path: Path to configuration file
            errors: Dictionary of validation errors
            warnings: List of warnings
            row_count: Number of rows validated
        
        Returns:
            ValidationRun record
        """
        session = self.get_session()
        try:
            run = ValidationRun(
                dataset_name=dataset_name,
                layer=layer,
                passed=passed,
                execution_time_seconds=execution_time,
                config_path=config_path,
                errors=errors,
                warnings=warnings or [],
                row_count=row_count
            )
            session.add(run)
            session.commit()
            return run
        finally:
            session.close()
    
    def get_validation_history(
        self,
        dataset_name: str,
        limit: int = 100
    ) -> list:
        """
        Get validation history for a dataset
        
        Args:
            dataset_name: Name of the dataset
            limit: Maximum number of records to return
        
        Returns:
            List of ValidationRun records
        """
        session = self.get_session()
        try:
            runs = session.query(ValidationRun).filter(
                ValidationRun.dataset_name == dataset_name
            ).order_by(
                ValidationRun.timestamp.desc()
            ).limit(limit).all()
            return runs
        finally:
            session.close()
    
    def get_validation_stats(self, dataset_name: str) -> dict:
        """
        Get validation statistics for a dataset
        
        Args:
            dataset_name: Name of the dataset
        
        Returns:
            Dictionary with statistics
        """
        session = self.get_session()
        try:
            runs = session.query(ValidationRun).filter(
                ValidationRun.dataset_name == dataset_name
            ).all()
            
            if not runs:
                return {
                    "total_runs": 0,
                    "passed": 0,
                    "failed": 0,
                    "pass_rate": 0.0,
                    "avg_execution_time": 0.0
                }
            
            total = len(runs)
            passed = sum(1 for r in runs if r.passed)
            failed = total - passed
            avg_time = sum(r.execution_time_seconds for r in runs) / total
            
            return {
                "total_runs": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": (passed / total) * 100,
                "avg_execution_time": avg_time
            }
        finally:
            session.close()
    
    def save_config(
        self,
        name: str,
        dataset: str,
        layer: str,
        config_content: dict
    ) -> ValidationConfig:
        """
        Save a validation configuration
        
        Args:
            name: Configuration name
            dataset: Dataset name
            layer: Data layer
            config_content: Configuration dictionary
        
        Returns:
            ValidationConfig record
        """
        session = self.get_session()
        try:
            # Try to update existing
            config = session.query(ValidationConfig).filter(
                ValidationConfig.name == name
            ).first()
            
            if config:
                config.dataset = dataset
                config.layer = layer
                config.config_content = config_content
                config.updated_at = datetime.utcnow()
            else:
                config = ValidationConfig(
                    name=name,
                    dataset=dataset,
                    layer=layer,
                    config_content=config_content
                )
                session.add(config)
            
            session.commit()
            return config
        finally:
            session.close()
    
    def get_config(self, name: str) -> Optional[ValidationConfig]:
        """
        Get a validation configuration
        
        Args:
            name: Configuration name
        
        Returns:
            ValidationConfig or None
        """
        session = self.get_session()
        try:
            return session.query(ValidationConfig).filter(
                ValidationConfig.name == name
            ).first()
        finally:
            session.close()
    
    def add_metric(
        self,
        metric_name: str,
        metric_value: float,
        dataset_name: str
    ) -> ValidationMetric:
        """
        Add a validation metric
        
        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            dataset_name: Dataset name
        
        Returns:
            ValidationMetric record
        """
        session = self.get_session()
        try:
            metric = ValidationMetric(
                metric_name=metric_name,
                metric_value=metric_value,
                dataset_name=dataset_name
            )
            session.add(metric)
            session.commit()
            return metric
        finally:
            session.close()

# Initialize database instance
db = Database()
