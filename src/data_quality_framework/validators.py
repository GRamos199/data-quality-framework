"""
Data validators for quality checks
"""

import pandas as pd
import pandera as pa
from typing import List, Dict, Any, Union, Callable
from datetime import datetime, timedelta
from .base import BaseValidator, ValidationResult
from .exceptions import ValidationError, RuleDefinitionError


class SchemaValidator(BaseValidator):
    """Validates DataFrame schema using Pandera"""

    def __init__(self, name: str, schema_dict: Dict[str, Any]):
        """
        Initialize schema validator.

        Args:
            name: Validator name
            schema_dict: Schema definition (column_name -> dtype or dict with constraints)
        """
        super().__init__(name, "Schema validation")
        self.schema_dict = schema_dict
        self.schema = self._build_schema(schema_dict)

    def _build_schema(self, schema_dict: Dict[str, Any]) -> pa.DataFrameSchema:
        """Build Pandera schema from dictionary definition"""
        columns = {}

        for col_name, col_spec in schema_dict.items():
            if isinstance(col_spec, str):
                # Simple type specification
                dtype = self._parse_dtype(col_spec)
                columns[col_name] = pa.Column(dtype)
            elif isinstance(col_spec, dict):
                # Complex specification with constraints
                columns[col_name] = self._build_column(col_name, col_spec)
            else:
                raise RuleDefinitionError(
                    f"Invalid schema specification for column {col_name}"
                )

        return pa.DataFrameSchema(columns, coerce=True)

    def _build_column(self, col_name: str, col_spec: Dict[str, Any]) -> pa.Column:
        """Build a Pandera Column with constraints"""
        dtype = self._parse_dtype(col_spec.get("type", "object"))
        nullable = col_spec.get("nullable", True)
        unique = col_spec.get("unique", False)

        checks = []
        if "min" in col_spec:
            checks.append(pa.Check.greater_than_or_equal_to(col_spec["min"]))
        if "max" in col_spec:
            checks.append(pa.Check.less_than_or_equal_to(col_spec["max"]))

        return pa.Column(
            dtype,
            checks=checks,
            nullable=nullable,
            unique=unique,
        )

    def _parse_dtype(self, dtype_str: str):
        """Parse string type specification to Pandas dtype"""
        dtype_map = {
            "int": "int64",
            "int64": "int64",
            "int32": "int32",
            "float": "float64",
            "float64": "float64",
            "float32": "float32",
            "str": "object",
            "string": "string",
            "object": "object",
            "bool": "bool",
            "datetime": "datetime64[ns]",
            "timestamp": "datetime64[ns]",
        }
        return dtype_map.get(dtype_str.lower(), dtype_str)

    def validate(self, data: pd.DataFrame) -> bool:
        """Validate DataFrame against schema"""
        self.clear_errors()
        try:
            self.schema.validate(data)
            return True
        except pa.errors.SchemaError as e:
            self.last_errors = [str(e)]
            return False


class NullCheckValidator(BaseValidator):
    """Validates that mandatory fields don't have null values"""

    def __init__(self, name: str, mandatory_columns: List[str]):
        """
        Initialize null check validator.

        Args:
            name: Validator name
            mandatory_columns: List of columns that cannot be null
        """
        super().__init__(name, "Null value checks")
        self.mandatory_columns = mandatory_columns

    def validate(self, data: pd.DataFrame) -> bool:
        """Check for null values in mandatory columns"""
        self.clear_errors()
        errors = []

        for col in self.mandatory_columns:
            if col not in data.columns:
                errors.append(f"Column '{col}' not found in dataset")
                continue

            null_count = data[col].isna().sum()
            if null_count > 0:
                errors.append(
                    f"Column '{col}' has {null_count} null values "
                    f"({null_count / len(data) * 100:.2f}%)"
                )

        self.last_errors = errors
        return len(errors) == 0


class UniquenessValidator(BaseValidator):
    """Validates uniqueness constraints"""

    def __init__(self, name: str, key_columns: Union[str, List[str]]):
        """
        Initialize uniqueness validator.

        Args:
            name: Validator name
            key_columns: Column or list of columns that should be unique
        """
        super().__init__(name, "Uniqueness checks")
        self.key_columns = (
            [key_columns] if isinstance(key_columns, str) else key_columns
        )

    def validate(self, data: pd.DataFrame) -> bool:
        """Check uniqueness of key columns"""
        self.clear_errors()
        errors = []

        # Check if columns exist
        missing_cols = [col for col in self.key_columns if col not in data.columns]
        if missing_cols:
            errors.append(f"Columns not found: {missing_cols}")
            self.last_errors = errors
            return False

        # Check duplicates
        duplicates = data[self.key_columns].duplicated().sum()
        if duplicates > 0:
            errors.append(
                f"Found {duplicates} duplicate rows on columns {self.key_columns}"
            )

        self.last_errors = errors
        return len(errors) == 0


class RangeValidator(BaseValidator):
    """Validates that values are within expected ranges"""

    def __init__(
        self,
        name: str,
        column_ranges: Dict[str, Dict[str, Union[int, float]]],
    ):
        """
        Initialize range validator.

        Args:
            name: Validator name
            column_ranges: Dictionary mapping column names to min/max ranges
                          e.g., {"temperature": {"min": -40, "max": 60}}
        """
        super().__init__(name, "Range validation")
        self.column_ranges = column_ranges

    def validate(self, data: pd.DataFrame) -> bool:
        """Check that values are within specified ranges"""
        self.clear_errors()
        errors = []

        for col, range_spec in self.column_ranges.items():
            if col not in data.columns:
                errors.append(f"Column '{col}' not found in dataset")
                continue

            min_val = range_spec.get("min")
            max_val = range_spec.get("max")

            if min_val is not None:
                out_of_range = (data[col] < min_val).sum()
                if out_of_range > 0:
                    errors.append(
                        f"Column '{col}': {out_of_range} values below minimum "
                        f"({min_val})"
                    )

            if max_val is not None:
                out_of_range = (data[col] > max_val).sum()
                if out_of_range > 0:
                    errors.append(
                        f"Column '{col}': {out_of_range} values above maximum "
                        f"({max_val})"
                    )

        self.last_errors = errors
        return len(errors) == 0


class FreshnessValidator(BaseValidator):
    """Validates that data is recent (API-ingested data freshness)"""

    def __init__(
        self, name: str, timestamp_column: str, max_age_hours: int
    ):
        """
        Initialize freshness validator.

        Args:
            name: Validator name
            timestamp_column: Column containing timestamps
            max_age_hours: Maximum allowed age in hours
        """
        super().__init__(name, "Data freshness checks")
        self.timestamp_column = timestamp_column
        self.max_age_hours = max_age_hours

    def validate(self, data: pd.DataFrame) -> bool:
        """Check that data is not too old"""
        self.clear_errors()
        errors = []

        if self.timestamp_column not in data.columns:
            errors.append(f"Timestamp column '{self.timestamp_column}' not found")
            self.last_errors = errors
            return False

        if len(data) == 0:
            errors.append("Dataset is empty")
            self.last_errors = errors
            return False

        # Convert to datetime if needed
        try:
            timestamps = pd.to_datetime(data[self.timestamp_column])
        except Exception as e:
            errors.append(f"Cannot parse timestamps: {e}")
            self.last_errors = errors
            return False

        now = datetime.utcnow()
        max_age = timedelta(hours=self.max_age_hours)

        # Check oldest record
        oldest_time = timestamps.min()
        age = now - oldest_time.to_pydatetime()

        if age > max_age:
            errors.append(
                f"Oldest record is {age.total_seconds() / 3600:.2f} hours old "
                f"(max allowed: {self.max_age_hours}h)"
            )

        self.last_errors = errors
        return len(errors) == 0


class CustomValidator(BaseValidator):
    """Allows custom validation logic via callable"""

    def __init__(self, name: str, validation_func: Callable):
        """
        Initialize custom validator.

        Args:
            name: Validator name
            validation_func: Function that takes DataFrame and returns (bool, List[str])
                           where bool is success and list is errors
        """
        super().__init__(name, "Custom validation")
        self.validation_func = validation_func

    def validate(self, data: pd.DataFrame) -> bool:
        """Run custom validation function"""
        self.clear_errors()
        try:
            result = self.validation_func(data)
            if isinstance(result, bool):
                return result
            elif isinstance(result, tuple):
                success, errors = result
                self.last_errors = errors if isinstance(errors, list) else [str(errors)]
                return success
            else:
                raise ValueError(
                    f"Validation function must return bool or (bool, list), "
                    f"got {type(result)}"
                )
        except Exception as e:
            self.last_errors = [f"Custom validator error: {e}"]
            return False


class CompositeValidator(BaseValidator):
    """Combines multiple validators"""

    def __init__(self, name: str, validators: List[BaseValidator]):
        """
        Initialize composite validator.

        Args:
            name: Validator name
            validators: List of validators to run
        """
        super().__init__(name, "Composite validation")
        self.validators = validators

    def validate(self, data: pd.DataFrame) -> bool:
        """Run all validators"""
        self.clear_errors()
        all_passed = True

        for validator in self.validators:
            if not validator.validate(data):
                all_passed = False
                self.last_errors.extend(
                    [f"[{validator.name}] {err}" for err in validator.get_errors()]
                )

        return all_passed

    def add_validator(self, validator: BaseValidator):
        """Add a validator to the composite"""
        self.validators.append(validator)
