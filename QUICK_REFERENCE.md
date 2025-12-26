# 🎯 Quick Reference Card

## Data Quality Framework - One-Page Cheat Sheet

### Installation
```bash
pip install -e ".[dev]"
```

### Basic Usage
```python
from data_quality_framework import NullCheckValidator, RangeValidator
from data_quality_framework.orchestrator import QualityCheckOrchestrator

# Create validators
validators = [
    NullCheckValidator("nulls", ["col1", "col2"]),
    RangeValidator("ranges", {"col1": {"min": 0, "max": 100}}),
]

# Run checks
orchestrator = QualityCheckOrchestrator()
result = orchestrator.run_checks(
    data=df,
    validators=validators,
    dataset_name="my_data",
    layer="raw",
    stop_on_failure=True,
)

# Check result
if result.passed:
    print("✓ Validation passed")
else:
    print("✗ Validation failed:", result.errors)
```

---

## Validator Types

| Validator | Purpose | Example |
|-----------|---------|---------|
| `SchemaValidator` | Column types | `SchemaValidator("schema", {"id": "int64", "name": "string"})` |
| `NullCheckValidator` | No nulls | `NullCheckValidator("nulls", ["id", "email"])` |
| `UniquenessValidator` | Unique keys | `UniquenessValidator("unique", ["id", "date"])` |
| `RangeValidator` | Value bounds | `RangeValidator("range", {"temp": {"min": -60, "max": 65}})` |
| `FreshnessValidator` | Data age | `FreshnessValidator("fresh", "timestamp", max_age_hours=1)` |
| `CompositeValidator` | Multiple | `CompositeValidator("all", [v1, v2, v3])` |

---

## Configuration File (YAML)

```yaml
dataset: "openweather"
layer: "raw"

rules:
  - type: "freshness"
    timestamp_column: "dt"
    max_age_hours: 1

  - type: "null_check"
    columns: ["city", "temperature"]

  - type: "range"
    columns:
      temperature:
        min: -60
        max: 65
      humidity:
        min: 0
        max: 100

on_failure: "log_and_stop"
```

---

## Airflow Integration Pattern

```python
def quality_check_task(ti):
    # Get data from previous task
    data = pd.read_json(ti.xcom_pull(task_ids='previous'))
    
    # Define validators
    validators = [...]
    
    # Run checks
    orchestrator = QualityCheckOrchestrator()
    try:
        result = orchestrator.run_checks(
            data, validators, 
            dataset_name="openweather",
            layer="raw",
            stop_on_failure=True,
        )
        return data
    except ValidationError as e:
        raise AirflowException(f"Quality check failed: {e}")
```

---

## Common Commands

```bash
# Install & test
make install
make install-dev
make test
make test-cov

# Run examples
make examples
make example-validators
make example-etl

# Code quality
make lint
make format

# Cleanup
make clean
make clean-test
```

---

## Error Handling

```python
from data_quality_framework.exceptions import ValidationError

try:
    result = orchestrator.run_checks(data, validators, ...)
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Details: {e.validation_errors}")
```

---

## Result Object

```python
result.passed              # bool - Did validation pass?
result.validators_run      # list - Validators executed
result.failed_validators   # list - Validators that failed
result.errors              # dict - Error messages by validator
result.timestamp           # datetime - When validation ran

result.to_dict()          # Convert to dictionary
```

---

## Getting Help

| Need | File/Command |
|------|-------------|
| Quick start | README.md |
| API reference | README.md → API Reference |
| System design | docs/ARCHITECTURE.md |
| Airflow integration | docs/INTEGRATION_GUIDE.md |
| Status & next steps | docs/PROJECT_STATUS.md |
| Run examples | `python examples/openweather_examples.py` |
| Run tests | `pytest tests/ -v` |
| Run ETL example | `python examples/lakehouse_integration_example.py` |

---

## Raw Layer Validation Pattern

```python
validators = [
    FreshnessValidator("freshness", "dt", max_age_hours=1),
    NullCheckValidator("required_fields", ["city", "temperature"]),
    RangeValidator("ranges", {
        "temperature": {"min": -60, "max": 65},
        "humidity": {"min": 0, "max": 100},
    }),
]
```

---

## Clean Layer Validation Pattern

```python
validators = [
    NullCheckValidator("no_nulls", ["id", "city_name", "measurement_date"]),
    UniquenessValidator("unique_keys", ["city_id", "measurement_date"]),
    RangeValidator("valid_ranges", {
        "temperature_celsius": {"min": -60, "max": 65},
        "humidity_percentage": {"min": 0, "max": 100},
    }),
]
```

---

## Project Structure Quick Reference

```
data-quality-framework/
├── README.md              ← START HERE
├── DELIVERABLES.md        ← What's included
├── src/                   ← Framework code
│   └── data_quality_framework/
│       ├── validators.py  ← Validation rules
│       ├── orchestrator.py ← Run validations
│       ├── config_loader.py ← Load configs
│       └── exceptions.py  ← Error handling
├── config/                ← Validation configs (YAML)
├── examples/              ← Usage examples
├── tests/                 ← Unit tests
└── docs/                  ← Full documentation
    ├── ARCHITECTURE.md    ← System design
    ├── INTEGRATION_GUIDE.md ← Airflow setup
    └── PROJECT_STATUS.md  ← What's done/next
```

---

## Common Patterns

### Pattern 1: Validate and Block
```python
result = orchestrator.run_checks(
    data, validators,
    stop_on_failure=True,  # Raises ValidationError on failure
)
```

### Pattern 2: Validate and Log
```python
result = orchestrator.run_checks(
    data, validators,
    stop_on_failure=False,  # Returns result with errors
)
if not result.passed:
    logger.error(f"Validation failed: {result.errors}")
```

### Pattern 3: Custom Validator
```python
from data_quality_framework.base import BaseValidator

class MyValidator(BaseValidator):
    def validate(self, data):
        # Your logic here
        if check_passes(data):
            return True
        else:
            self.last_errors = ["Your error message"]
            return False
```

---

## Version Information

- **Framework Version**: 0.1.0
- **Python**: 3.9+
- **Key Dependencies**: pandas, pandera, pyyaml
- **Release Date**: December 26, 2024

---

## Quick Links

- 📖 [Full README](README.md)
- 🏗️ [Architecture Guide](docs/ARCHITECTURE.md)
- 🔌 [Airflow Integration](docs/INTEGRATION_GUIDE.md)
- 📊 [Project Status](docs/PROJECT_STATUS.md)
- 💾 [Changelog](CHANGELOG.md)

---

**Ready to use! Start with: `pip install -e ".[dev]"`**
