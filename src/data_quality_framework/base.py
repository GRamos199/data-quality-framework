"""
Base validator classes and interfaces
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime


class BaseValidator(ABC):
    """Abstract base class for all validators"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.last_errors = []

    @abstractmethod
    def validate(self, data: pd.DataFrame) -> bool:
        """
        Validate the data.

        Args:
            data: DataFrame to validate

        Returns:
            True if validation passes, False otherwise
        """
        pass

    def get_errors(self) -> List[str]:
        """Get the last validation errors"""
        return self.last_errors

    def clear_errors(self):
        """Clear stored errors"""
        self.last_errors = []


class ValidationResult:
    """Encapsulates validation results"""

    def __init__(
        self,
        dataset_name: str,
        layer: str,
        passed: bool,
        validators_run: List[str],
        failed_validators: List[str],
        errors: Dict[str, List[str]],
        timestamp: datetime = None,
    ):
        self.dataset_name = dataset_name
        self.layer = layer
        self.passed = passed
        self.validators_run = validators_run
        self.failed_validators = failed_validators
        self.errors = errors
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "dataset_name": self.dataset_name,
            "layer": self.layer,
            "passed": self.passed,
            "validators_run": self.validators_run,
            "failed_validators": self.failed_validators,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        status = "✓ PASSED" if self.passed else "✗ FAILED"
        return f"ValidationResult({self.dataset_name}/{self.layer}: {status})"
