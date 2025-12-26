# Quick Start Guide - Data Quality Framework

## 🚀 Run Everything Quickly

### Step 1: Activate the virtual environment
```bash
cd /home/george/data-quality-framework
source venv/bin/activate
```

### Step 2: Run the tests (21 tests)
```bash
pytest tests/ -v
```

**Expected output:**
```
test_validators.py::TestNullCheckValidator::test_valid_no_nulls PASSED
test_validators.py::TestNullCheckValidator::test_invalid_with_nulls PASSED
...
===================== 21 passed in 0.43s =====================
```

### Step 3: Run framework examples
```bash
python examples/openweather_examples.py
```

**Expected output:**
```
======================================================================
EXAMPLE 1: Valid Raw OpenWeather Data
======================================================================
✓ All quality checks passed for openweather (raw)
...
EXAMPLE 6: Clean Data with Duplicate Records
======================================================================
✗ Quality checks failed for openweather (raw): ['Unique City-Date']
```

### Step 4: Run the complete ETL integration
```bash
python examples/lakehouse_integration_example.py
```

**Expected output:**
```
[EXTRACT] Fetching data from OpenWeather API...
✓ Extracted 3 records from API

[LOAD RAW] Validating data before loading to raw layer...
✓ Raw layer validation passed

[TRANSFORM] Cleaning and transforming raw data...
✓ Transformed 3 records

[LOAD CLEAN] Validating transformed data before loading...
✓ Clean layer validation passed

[PUBLISH] Loading to Analytics layer...
✓ Published 3 records to Analytics

✓ PIPELINE COMPLETED SUCCESSFULLY
```

---

## 📊 How to Use Your JSON File from the Previous Project

### Step 1: Create script to read your JSON

```python
# test_your_data.py
import pandas as pd
import json
from data_quality_framework import (
    NullCheckValidator,
    RangeValidator,
    SchemaValidator,
)
from data_quality_framework.orchestrator import QualityCheckOrchestrator

# Read your JSON
with open('your_file.json', 'r') as f:
    data_dict = json.load(f)

# Convert to DataFrame (adjust based on your structure)
df = pd.DataFrame(data_dict)

# Create custom validators for your data
validators = [
    NullCheckValidator("mandatory_fields", ["field1", "field2"]),
    RangeValidator("valid_ranges", {
        "temperature": {"min": -60, "max": 65},
        "humidity": {"min": 0, "max": 100},
    }),
]

# Run validation
orchestrator = QualityCheckOrchestrator()
result = orchestrator.run_checks(
    df,
    validators,
    dataset_name="my_dataset",
    layer="raw",
    stop_on_failure=False,
)

# View results
if result.passed:
    print("✓ Data is valid!")
else:
    print("✗ Data is invalid:")
    for validator, errors in result.errors.items():
        print(f"  {validator}: {errors}")
```

### Step 2: Where to put your JSON file

**Option A: In the root**
```bash
/home/george/data-quality-framework/
├── your_file.json    ← Here
├── test_your_data.py
└── ...
```

**Option B: In `data/` folder** (recommended)
```bash
/home/george/data-quality-framework/
├── data/
│   └── your_file.json    ← Here
├── test_your_data.py
└── ...
```

### Step 3: Run your test
```bash
python test_your_data.py
```

---

## 🎯 Expected JSON Structure

### If your JSON has weather data:
```json
{
  "id": 1,
  "city": "Buenos Aires",
  "dt": "2025-12-26T10:30:00",
  "temperature": 28.5,
  "humidity": 65,
  "pressure": 1013
}
```

### If it's an array:
```json
[
  {
    "id": 1,
    "city": "Buenos Aires",
    "temperature": 28.5
  },
  {
    "id": 2,
    "city": "Madrid",
    "temperature": 15.2
  }
]
```

---

## 📁 Configuration with YAML

You can also create a YAML configuration for automatic validation:

```yaml
# config/my_dataset_validation.yaml
dataset: "my_dataset"
layer: "raw"

rules:
  - type: "null_check"
    name: "mandatory_fields"
    columns: ["city", "temperature"]
    enabled: true

  - type: "range"
    name: "valid_temperatures"
    columns:
      temperature:
        min: -60
        max: 65
      humidity:
        min: 0
        max: 100
    enabled: true

on_failure: "log_and_stop"
```

Then use it:
```python
from data_quality_framework import ConfigLoader

config = ConfigLoader.load_yaml("config/my_dataset_validation.yaml")
print(config)
```

---

## 🧪 Available Validator Types

| Validator | Purpose | Example |
|-----------|---------|---------|
| **NullCheckValidator** | Check mandatory fields | `NullCheckValidator("nulls", ["city", "temperature"])` |
| **RangeValidator** | Values within ranges | `RangeValidator("ranges", {"temp": {"min": -60, "max": 65}})` |
| **UniquenessValidator** | Unique keys | `UniquenessValidator("unique", ["city", "date"])` |
| **SchemaValidator** | Data types | `SchemaValidator("schema", {"id": "int64", "city": "string"})` |
| **FreshnessValidator** | Recent data | `FreshnessValidator("fresh", "timestamp", max_age_hours=1)` |
| **CustomValidator** | Custom logic | `CustomValidator("custom", lambda df: custom_logic(df))` |

---

## 🔍 Debug Errors

If there are errors, check the detailed result:

```python
result = orchestrator.run_checks(df, validators, ...)

# View details
print(f"Passed: {result.passed}")
print(f"Validators run: {result.validators_run}")
print(f"Failed validators: {result.failed_validators}")
print(f"Errors: {result.errors}")

# View full report
report = orchestrator.generate_report()
print(report)
```

---

## 📚 Important Files

| File | Purpose |
|------|---------|
| [README.md](README.md) | Complete documentation |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) | How to integrate with Airflow |
| [examples/openweather_examples.py](examples/openweather_examples.py) | Validator examples |
| [examples/lakehouse_integration_example.py](examples/lakehouse_integration_example.py) | Complete ETL |
| [src/data_quality_framework/validators.py](src/data_quality_framework/validators.py) | Validator code |

---

## ✅ Execution Checklist

- [ ] `source venv/bin/activate` - Environment activated
- [ ] `pytest tests/ -v` - 21 tests passing
- [ ] `python examples/openweather_examples.py` - Examples working
- [ ] `python examples/lakehouse_integration_example.py` - Complete ETL
- [ ] Your JSON file copied to `/data/` or root
- [ ] Your script `test_your_data.py` created
- [ ] Your script running successfully

---

## 🆘 Common Issues

### "ModuleNotFoundError: No module named 'data_quality_framework'"
```bash
pip install -e .
```

### "Validator failed: Column not found"
Make sure the column name exists (case-sensitive):
```python
# Check available columns
print(df.columns.tolist())
```

### "Tests failing after changes"
```bash
pytest tests/ -v --tb=short
```

---

Ready to go! Now you're all set to run everything. 🚀
