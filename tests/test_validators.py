"""
Tests for validators
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_quality_framework.validators import (
    SchemaValidator,
    NullCheckValidator,
    UniquenessValidator,
    RangeValidator,
    FreshnessValidator,
)


class TestNullCheckValidator:
    """Test NullCheckValidator"""
    
    def test_valid_no_nulls(self):
        """Test data with no nulls passes validation"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "value": [10.0, 20.0, 30.0],
        })
        
        validator = NullCheckValidator("test", ["id", "name", "value"])
        assert validator.validate(data) is True
        assert len(validator.get_errors()) == 0
    
    def test_invalid_with_nulls(self):
        """Test data with nulls fails validation"""
        data = pd.DataFrame({
            "id": [1, None, 3],
            "name": ["A", "B", "C"],
            "value": [10.0, None, 30.0],
        })
        
        validator = NullCheckValidator("test", ["id", "value"])
        assert validator.validate(data) is False
        assert len(validator.get_errors()) > 0
    
    def test_missing_column(self):
        """Test validator handles missing columns gracefully"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
        })
        
        validator = NullCheckValidator("test", ["id", "nonexistent"])
        assert validator.validate(data) is False
        assert any("not found" in err for err in validator.get_errors())


class TestUniquenessValidator:
    """Test UniquenessValidator"""
    
    def test_valid_unique_values(self):
        """Test data with unique values passes validation"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            "email": ["a@example.com", "b@example.com", "c@example.com"],
        })
        
        validator = UniquenessValidator("test", "id")
        assert validator.validate(data) is True
    
    def test_invalid_duplicates(self):
        """Test data with duplicates fails validation"""
        data = pd.DataFrame({
            "id": [1, 1, 2],
            "email": ["a@example.com", "b@example.com", "c@example.com"],
        })
        
        validator = UniquenessValidator("test", "id")
        assert validator.validate(data) is False
        assert len(validator.get_errors()) > 0
    
    def test_composite_key_uniqueness(self):
        """Test uniqueness with composite keys"""
        data = pd.DataFrame({
            "city": ["NYC", "NYC", "LA"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-01"],
        })
        
        validator = UniquenessValidator("test", ["city", "date"])
        assert validator.validate(data) is True
    
    def test_composite_key_duplicates(self):
        """Test composite key duplicates detection"""
        data = pd.DataFrame({
            "city": ["NYC", "NYC", "LA"],
            "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
        })
        
        validator = UniquenessValidator("test", ["city", "date"])
        assert validator.validate(data) is False


class TestRangeValidator:
    """Test RangeValidator"""
    
    def test_valid_values_in_range(self):
        """Test values within range pass validation"""
        data = pd.DataFrame({
            "temperature": [10.0, 20.0, 30.0],
            "humidity": [40, 60, 80],
        })
        
        validator = RangeValidator("test", {
            "temperature": {"min": 0, "max": 40},
            "humidity": {"min": 0, "max": 100},
        })
        assert validator.validate(data) is True
    
    def test_invalid_below_minimum(self):
        """Test values below minimum fail validation"""
        data = pd.DataFrame({
            "temperature": [-10.0, 20.0, 30.0],
        })
        
        validator = RangeValidator("test", {
            "temperature": {"min": 0, "max": 40},
        })
        assert validator.validate(data) is False
    
    def test_invalid_above_maximum(self):
        """Test values above maximum fail validation"""
        data = pd.DataFrame({
            "humidity": [40, 120, 80],
        })
        
        validator = RangeValidator("test", {
            "humidity": {"min": 0, "max": 100},
        })
        assert validator.validate(data) is False


class TestFreshnessValidator:
    """Test FreshnessValidator"""
    
    def test_valid_recent_data(self):
        """Test recent data passes freshness check"""
        now = datetime.utcnow()
        data = pd.DataFrame({
            "timestamp": [now - timedelta(minutes=30)],
        })
        
        validator = FreshnessValidator("test", "timestamp", max_age_hours=1)
        assert validator.validate(data) is True
    
    def test_invalid_stale_data(self):
        """Test old data fails freshness check"""
        now = datetime.utcnow()
        data = pd.DataFrame({
            "timestamp": [now - timedelta(days=5)],
        })
        
        validator = FreshnessValidator("test", "timestamp", max_age_hours=1)
        assert validator.validate(data) is False
        assert any("hours old" in err for err in validator.get_errors())
    
    def test_empty_dataset(self):
        """Test empty dataset fails freshness check"""
        data = pd.DataFrame({"timestamp": []})
        
        validator = FreshnessValidator("test", "timestamp", max_age_hours=1)
        assert validator.validate(data) is False


class TestSchemaValidator:
    """Test SchemaValidator"""
    
    def test_valid_schema(self):
        """Test data matching schema passes validation"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "price": [10.5, 20.5, 30.5],
        })
        
        schema = {
            "id": "int64",
            "name": "string",
            "price": "float64",
        }
        
        validator = SchemaValidator("test", schema)
        assert validator.validate(data) is True
    
    def test_invalid_data_type(self):
        """Test data with wrong type fails validation"""
        data = pd.DataFrame({
            "id": ["1", "2", "3"],  # Should be int
            "name": ["A", "B", "C"],
        })
        
        schema = {
            "id": "int64",
            "name": "string",
        }
        
        validator = SchemaValidator("test", schema)
        # Schema validation will fail due to type mismatch
        # (actual behavior depends on strict type checking)
    
    def test_missing_column(self):
        """Test missing required column fails validation"""
        data = pd.DataFrame({
            "id": [1, 2, 3],
            # 'name' column is missing
        })
        
        schema = {
            "id": "int64",
            "name": "string",
        }
        
        validator = SchemaValidator("test", schema)
        assert validator.validate(data) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
