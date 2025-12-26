"""
Quality check orchestrator for running validation pipelines
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .base import BaseValidator, ValidationResult
from .exceptions import ValidationError


class QualityCheckOrchestrator:
    """Orchestrates running quality checks on data"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize orchestrator.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or self._setup_logger()
        self.validation_history = []

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger("data_quality_framework")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def run_checks(
        self,
        data: pd.DataFrame,
        validators: List[BaseValidator],
        dataset_name: str,
        layer: str,
        stop_on_failure: bool = True,
    ) -> ValidationResult:
        """
        Run a set of validators on data.

        Args:
            data: DataFrame to validate
            validators: List of validators to run
            dataset_name: Name of the dataset
            layer: Layer name (raw, clean, etc.)
            stop_on_failure: If True, raise error on first failure

        Returns:
            ValidationResult object

        Raises:
            ValidationError: If stop_on_failure is True and validation fails
        """
        self.logger.info(
            f"Starting quality checks for {dataset_name} ({layer} layer)"
        )

        validators_run = []
        failed_validators = []
        errors = {}
        all_passed = True

        for validator in validators:
            try:
                self.logger.debug(f"Running validator: {validator.name}")
                passed = validator.validate(data)

                validators_run.append(validator.name)

                if not passed:
                    all_passed = False
                    failed_validators.append(validator.name)
                    errors[validator.name] = validator.get_errors()

                    self.logger.warning(
                        f"✗ Validator '{validator.name}' failed: "
                        f"{'; '.join(validator.get_errors())}"
                    )

                    if stop_on_failure:
                        raise ValidationError(
                            f"Validation failed in {validator.name}",
                            {validator.name: validator.get_errors()},
                        )
                else:
                    self.logger.info(f"✓ Validator '{validator.name}' passed")

            except Exception as e:
                self.logger.error(f"Error running validator {validator.name}: {e}")
                raise

        # Create result
        result = ValidationResult(
            dataset_name=dataset_name,
            layer=layer,
            passed=all_passed,
            validators_run=validators_run,
            failed_validators=failed_validators,
            errors=errors,
        )

        # Log result
        if all_passed:
            self.logger.info(
                f"✓ All quality checks passed for {dataset_name} ({layer})"
            )
        else:
            self.logger.error(
                f"✗ Quality checks failed for {dataset_name} ({layer}): "
                f"{failed_validators}"
            )

        self.validation_history.append(result)
        return result

    def get_validation_history(self) -> List[ValidationResult]:
        """Get all validation results from this session"""
        return self.validation_history

    def generate_report(self) -> Dict[str, Any]:
        """Generate summary report of all validations"""
        if not self.validation_history:
            return {"total_validations": 0, "passed": 0, "failed": 0}

        total = len(self.validation_history)
        passed = sum(1 for r in self.validation_history if r.passed)
        failed = total - passed

        return {
            "total_validations": total,
            "passed": passed,
            "failed": failed,
            "success_rate": f"{passed / total * 100:.2f}%",
            "results": [r.to_dict() for r in self.validation_history],
        }
