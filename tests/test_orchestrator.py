"""
Tests for the orchestrator
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_quality_framework.orchestrator import QualityCheckOrchestrator
from data_quality_framework.validators import NullCheckValidator
from data_quality_framework.exceptions import ValidationError


class TestQualityCheckOrchestrator:
    """Test QualityCheckOrchestrator"""
    
    def test_all_validators_pass(self):
        """Test orchestrator returns success when all validators pass"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        })
        
        validators = [
            NullCheckValidator("test", ["id", "name"]),
        ]
        
        orchestrator = QualityCheckOrchestrator()
        result = orchestrator.run_checks(
            data,
            validators,
            dataset_name="test",
            layer="raw",
            stop_on_failure=False,
        )
        
        assert result.passed is True
        assert len(result.failed_validators) == 0
    
    def test_validator_failure_no_stop(self):
        """Test orchestrator continues when validator fails and stop_on_failure=False"""
        data = pd.DataFrame({
            "id": [1, None, 3],
        })
        
        validators = [
            NullCheckValidator("test", ["id"]),
        ]
        
        orchestrator = QualityCheckOrchestrator()
        result = orchestrator.run_checks(
            data,
            validators,
            dataset_name="test",
            layer="raw",
            stop_on_failure=False,
        )
        
        assert result.passed is False
        assert "test" in result.failed_validators
    
    def test_validator_failure_with_stop(self):
        """Test orchestrator raises error when validator fails and stop_on_failure=True"""
        data = pd.DataFrame({
            "id": [1, None, 3],
        })
        
        validators = [
            NullCheckValidator("test", ["id"]),
        ]
        
        orchestrator = QualityCheckOrchestrator()
        
        with pytest.raises(ValidationError):
            orchestrator.run_checks(
                data,
                validators,
                dataset_name="test",
                layer="raw",
                stop_on_failure=True,
            )
    
    def test_validation_history_tracking(self):
        """Test orchestrator tracks validation history"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
        })
        
        validators = [
            NullCheckValidator("test", ["id"]),
        ]
        
        orchestrator = QualityCheckOrchestrator()
        
        # Run multiple validations
        orchestrator.run_checks(data, validators, "dataset1", "raw", stop_on_failure=False)
        orchestrator.run_checks(data, validators, "dataset2", "raw", stop_on_failure=False)
        
        history = orchestrator.get_validation_history()
        assert len(history) == 2
    
    def test_generate_report(self):
        """Test orchestrator generates validation report"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
        })
        
        validators = [
            NullCheckValidator("test", ["id"]),
        ]
        
        orchestrator = QualityCheckOrchestrator()
        orchestrator.run_checks(data, validators, "test", "raw", stop_on_failure=False)
        
        report = orchestrator.generate_report()
        
        assert report["total_validations"] == 1
        assert report["passed"] == 1
        assert report["failed"] == 0
        assert "100.00%" in report["success_rate"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
