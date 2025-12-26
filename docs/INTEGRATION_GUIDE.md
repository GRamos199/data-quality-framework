# Integration Guide: Data Quality Framework with Data Lakehouse Simulation

This guide explains how to integrate the Data Quality Framework with the [data-lakehouse-simulation](https://github.com/yourusername/data-lakehouse-simulation) project.

## 📌 Overview

The Data Quality Framework validates data at each stage of your lakehouse ETL pipeline:

```
Airflow DAG (data-lakehouse-simulation)
    │
    ├─ [Extract] OpenWeather API
    │   └─ → Raw Layer
    │       └─ ✓ Quality Checks (Framework)
    │           ├─ Freshness validation
    │           ├─ Schema validation
    │           └─ Mandatory field checks
    │
    ├─ [Transform] Raw → Clean
    │   └─ → Clean Layer
    │       └─ ✓ Quality Checks (Framework)
    │           ├─ Uniqueness validation
    │           ├─ Range validation
    │           └─ No null checks
    │
    └─ [Load] → Analytics Layer
        (data is guaranteed to be valid)
```

## 🔧 Installation

### Option 1: Add as Git Submodule

```bash
cd data-lakehouse-simulation
git submodule add https://github.com/yourusername/data-quality-framework.git dags/data_quality_framework
```

### Option 2: Install as Package

```bash
# From your lakehouse-simulation project
pip install -e ../data-quality-framework
```

### Option 3: Include in Requirements

```bash
# In your requirements.txt
git+https://github.com/yourusername/data-quality-framework.git@main#egg=data-quality-framework
```

## 🚀 Integration in Airflow DAG

### Basic Setup

```python
# dags/lakehouse_etl_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowException
from datetime import datetime, timedelta
import pandas as pd
from data_quality_framework import (
    NullCheckValidator,
    UniquenessValidator,
    RangeValidator,
    FreshnessValidator,
)
from data_quality_framework.orchestrator import QualityCheckOrchestrator
from data_quality_framework.exceptions import ValidationError

# Configuration
DEFAULT_ARGS = {
    'owner': 'data-engineering',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Initialize orchestrator
quality_orchestrator = QualityCheckOrchestrator()

# ============================================================================
# Task: Extract from OpenWeather API
# ============================================================================
def extract_openweather_api():
    """Extract data from OpenWeather API"""
    import requests
    
    # Your API extraction logic here
    api_key = "your_api_key"
    cities = ["Buenos Aires", "Madrid", "Sydney"]
    
    all_data = []
    for city in cities:
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": api_key, "units": "metric"}
        )
        all_data.append(response.json())
    
    # Convert to DataFrame
    data = pd.DataFrame([
        {
            "id": i,
            "city": d["name"],
            "dt": datetime.fromtimestamp(d["dt"]),
            "temperature": d["main"]["temp"],
            "feels_like": d["main"]["feels_like"],
            "temp_min": d["main"]["temp_min"],
            "temp_max": d["main"]["temp_max"],
            "pressure": d["main"]["pressure"],
            "humidity": d["main"]["humidity"],
            "weather_main": d["weather"][0]["main"],
            "weather_description": d["weather"][0]["description"],
            "wind_speed": d["wind"].get("speed", 0),
            "wind_deg": d["wind"].get("deg", 0),
            "cloudiness": d["clouds"]["all"],
            "rain_1h": d.get("rain", {}).get("1h", 0),
        }
        for i, d in enumerate(all_data)
    ])
    
    # Push to XCom for next tasks
    return data.to_json()


# ============================================================================
# Task: Validate Raw Data Quality
# ============================================================================
def validate_raw_data(ti):
    """Validate data before loading to raw layer"""
    
    # Get data from previous task
    raw_json = ti.xcom_pull(task_ids='extract_api')
    raw_data = pd.read_json(raw_json)
    
    # Define validators for raw layer
    validators = [
        FreshnessValidator(
            name="api_freshness",
            timestamp_column="dt",
            max_age_hours=1,  # API data must be < 1 hour old
        ),
        NullCheckValidator(
            name="mandatory_fields",
            mandatory_columns=[
                "city",
                "dt",
                "temperature",
                "humidity",
                "weather_main",
            ],
        ),
        RangeValidator(
            name="valid_ranges",
            column_ranges={
                "temperature": {"min": -60, "max": 65},
                "humidity": {"min": 0, "max": 100},
                "pressure": {"min": 870, "max": 1085},
                "wind_speed": {"min": 0, "max": 50},
                "cloudiness": {"min": 0, "max": 100},
            },
        ),
    ]
    
    try:
        # Run quality checks
        result = quality_orchestrator.run_checks(
            data=raw_data,
            validators=validators,
            dataset_name="openweather",
            layer="raw",
            stop_on_failure=True,  # Block invalid data
        )
        
        # Log success
        print(f"✓ Raw layer validation passed for {len(raw_data)} records")
        return raw_data.to_json()
        
    except ValidationError as e:
        # Validation failed - block pipeline
        error_msg = f"Raw layer quality checks failed: {e.message}"
        print(f"✗ {error_msg}")
        raise AirflowException(error_msg)


# ============================================================================
# Task: Transform Raw to Clean
# ============================================================================
def transform_raw_to_clean(ti):
    """Transform raw data to clean layer"""
    
    raw_json = ti.xcom_pull(task_ids='validate_raw')
    raw_data = pd.read_json(raw_json)
    
    # Your transformation logic
    clean_data = pd.DataFrame({
        "city_id": raw_data["id"],
        "city_name": raw_data["city"],
        "country": ["AR", "ES", "AU"],  # Hardcoded for example
        "measurement_date": pd.to_datetime(raw_data["dt"]),
        "temperature_celsius": raw_data["temperature"],
        "feels_like_celsius": raw_data["feels_like"],
        "humidity_percentage": raw_data["humidity"],
        "weather_condition": raw_data["weather_main"],
        "wind_speed_ms": raw_data["wind_speed"],
        "cloudiness_percentage": raw_data["cloudiness"],
        "pressure_hpa": raw_data["pressure"],
        "precipitation_mm": raw_data["rain_1h"],
        "data_quality_score": [0.98] * len(raw_data),  # Calculate real score
        "ingestion_timestamp": [datetime.utcnow()] * len(raw_data),
    })
    
    print(f"✓ Transformed {len(clean_data)} records from raw to clean")
    return clean_data.to_json()


# ============================================================================
# Task: Validate Clean Data Quality
# ============================================================================
def validate_clean_data(ti):
    """Validate transformed data before loading to clean layer"""
    
    clean_json = ti.xcom_pull(task_ids='transform')
    clean_data = pd.read_json(clean_json)
    
    # Define validators for clean layer
    validators = [
        NullCheckValidator(
            name="mandatory_fields",
            mandatory_columns=[
                "city_id",
                "city_name",
                "measurement_date",
                "temperature_celsius",
                "humidity_percentage",
            ],
        ),
        UniquenessValidator(
            name="unique_city_date",
            key_columns=["city_id", "measurement_date"],  # One record per city per measurement
        ),
        RangeValidator(
            name="valid_ranges",
            column_ranges={
                "temperature_celsius": {"min": -60, "max": 65},
                "humidity_percentage": {"min": 0, "max": 100},
                "wind_speed_ms": {"min": 0, "max": 50},
                "cloudiness_percentage": {"min": 0, "max": 100},
                "pressure_hpa": {"min": 870, "max": 1085},
                "data_quality_score": {"min": 0, "max": 1},
            },
        ),
    ]
    
    try:
        result = quality_orchestrator.run_checks(
            data=clean_data,
            validators=validators,
            dataset_name="openweather",
            layer="clean",
            stop_on_failure=True,
        )
        
        print(f"✓ Clean layer validation passed for {len(clean_data)} records")
        return clean_data.to_json()
        
    except ValidationError as e:
        error_msg = f"Clean layer quality checks failed: {e.message}"
        print(f"✗ {error_msg}")
        raise AirflowException(error_msg)


# ============================================================================
# Task: Load to Analytics Layer
# ============================================================================
def load_to_analytics(ti):
    """Load validated data to analytics layer"""
    
    clean_json = ti.xcom_pull(task_ids='validate_clean')
    clean_data = pd.read_json(clean_json)
    
    # Your analytics load logic
    # Example: Write to Parquet, SQL database, etc.
    clean_data.to_parquet("s3://analytics-bucket/openweather/latest.parquet")
    
    print(f"✓ Loaded {len(clean_data)} records to analytics layer")
    
    # Generate validation report
    report = quality_orchestrator.generate_report()
    print(f"\nValidation Report:")
    print(f"  Total validations: {report['total_validations']}")
    print(f"  Passed: {report['passed']}")
    print(f"  Failed: {report['failed']}")
    print(f"  Success rate: {report['success_rate']}")


# ============================================================================
# DAG Definition
# ============================================================================
with DAG(
    dag_id='openweather_lakehouse_etl',
    default_args=DEFAULT_ARGS,
    description='OpenWeather ETL with Data Quality Framework',
    schedule_interval='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['openweather', 'quality-framework'],
) as dag:
    
    # Task 1: Extract
    extract = PythonOperator(
        task_id='extract_api',
        python_callable=extract_openweather_api,
    )
    
    # Task 2: Validate Raw
    validate_raw = PythonOperator(
        task_id='validate_raw',
        python_callable=validate_raw_data,
    )
    
    # Task 3: Transform
    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_raw_to_clean,
    )
    
    # Task 4: Validate Clean
    validate_clean = PythonOperator(
        task_id='validate_clean',
        python_callable=validate_clean_data,
    )
    
    # Task 5: Load Analytics
    load = PythonOperator(
        task_id='load_analytics',
        python_callable=load_to_analytics,
    )
    
    # DAG dependencies (with quality gates)
    extract >> validate_raw >> transform >> validate_clean >> load
```

## 📊 Configuration Files in Lakehouse Project

Place configuration files in your dags directory:

```bash
dags/
├── lakehouse_etl_dag.py
├── quality_configs/
│   ├── openweather_raw_validation.yaml
│   └── openweather_clean_validation.yaml
└── ...
```

Then reference in your DAG:

```python
from data_quality_framework import ConfigLoader

# Load configuration
raw_config = ConfigLoader.load_yaml("dags/quality_configs/openweather_raw_validation.yaml")
clean_config = ConfigLoader.load_yaml("dags/quality_configs/openweather_clean_validation.yaml")
```

## 🔄 Advanced: Using ConfigLoader

```python
# dags/quality_check_tasks.py

from data_quality_framework import ConfigLoader, CompositeValidator
from data_quality_framework.validators import (
    FreshnessValidator,
    NullCheckValidator,
    RangeValidator,
)

def build_validators_from_config(config_path):
    """Build validators from YAML configuration"""
    
    config = ConfigLoader.load_yaml(config_path)
    validators = []
    
    for rule in config['rules']:
        rule_type = rule['type']
        
        if rule_type == 'freshness':
            validators.append(FreshnessValidator(
                name=rule['name'],
                timestamp_column=rule['timestamp_column'],
                max_age_hours=rule['max_age_hours'],
            ))
        
        elif rule_type == 'null_check':
            validators.append(NullCheckValidator(
                name=rule['name'],
                mandatory_columns=rule['columns'],
            ))
        
        elif rule_type == 'range':
            validators.append(RangeValidator(
                name=rule['name'],
                column_ranges=rule['columns'],
            ))
    
    return validators
```

## 📈 Monitoring and Logging

### Airflow Integration

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pass to orchestrator
orchestrator = QualityCheckOrchestrator(logger=logger)

# Logs will appear in Airflow task logs
```

### Metrics and Alerts

```python
def quality_check_callback(context):
    """Callback when quality check fails"""
    
    ti = context['task_instance']
    dag_id = context['dag'].dag_id
    
    # Send alert
    send_alert(
        f"Quality check failed in {dag_id}",
        f"Task: {ti.task_id}, Attempt: {ti.try_number}"
    )

# In your DAG:
validate_task = PythonOperator(
    task_id='validate_data',
    python_callable=validate_raw_data,
    on_failure_callback=quality_check_callback,
)
```

## 🧪 Testing Your Integration

```python
# tests/test_lakehouse_integration.py

import pytest
import pandas as pd
from datetime import datetime, timedelta
from dags.quality_check_tasks import build_validators_from_config
from data_quality_framework.orchestrator import QualityCheckOrchestrator

def test_raw_validation_with_valid_data():
    """Test raw layer validation passes with valid data"""
    
    data = pd.DataFrame({
        "id": [1, 2],
        "city": ["NYC", "LA"],
        "dt": [datetime.utcnow(), datetime.utcnow()],
        "temperature": [5.0, 25.0],
        "humidity": [60, 50],
        # ... other required fields
    })
    
    validators = build_validators_from_config("dags/quality_configs/openweather_raw_validation.yaml")
    orchestrator = QualityCheckOrchestrator()
    
    result = orchestrator.run_checks(
        data,
        validators,
        "openweather",
        "raw",
        stop_on_failure=False,
    )
    
    assert result.passed


def test_clean_validation_prevents_duplicates():
    """Test clean layer validation catches duplicates"""
    
    data = pd.DataFrame({
        "city_id": [1, 1, 2],  # Duplicate city_id
        "measurement_date": [
            datetime.utcnow(),
            datetime.utcnow(),  # Same date
            datetime.utcnow(),
        ],
        # ... other fields
    })
    
    validators = build_validators_from_config("dags/quality_configs/openweather_clean_validation.yaml")
    orchestrator = QualityCheckOrchestrator()
    
    result = orchestrator.run_checks(
        data,
        validators,
        "openweather",
        "clean",
        stop_on_failure=False,
    )
    
    assert not result.passed
    assert any("unique" in err.lower() for errs in result.errors.values() for err in errs)
```

## 📚 Common Patterns

### Pattern 1: Conditional Branching

```python
from airflow.operators.python import BranchPythonOperator

def check_quality_branch(ti):
    """Branch based on quality check results"""
    
    clean_json = ti.xcom_pull(task_ids='validate_clean')
    clean_data = pd.read_json(clean_json)
    
    validators = [...]
    result = orchestrator.run_checks(
        clean_data, validators, ..., stop_on_failure=False
    )
    
    if result.passed:
        return 'load_analytics'
    else:
        return 'handle_failure'

branch = BranchPythonOperator(
    task_id='quality_branch',
    python_callable=check_quality_branch,
)
```

### Pattern 2: Dynamic Validation Rules

```python
# Adjust validation rules based on data characteristics
def dynamic_validation(ti, **context):
    """Adjust validators based on data"""
    
    data = pd.read_json(ti.xcom_pull(task_ids='previous'))
    
    # Use different validators based on data volume
    if len(data) > 100000:
        validators = [basic_checks]  # Fast validators for large data
    else:
        validators = [all_checks]  # Thorough for small data
    
    return orchestrator.run_checks(data, validators, ...)
```

### Pattern 3: Reusable Quality Check Templates

```python
# dags/quality_check_templates.py

def create_api_data_validators(timestamp_col, max_age_hours=1):
    """Validators for API data"""
    return [
        FreshnessValidator("api_freshness", timestamp_col, max_age_hours),
        NullCheckValidator("required_fields", ["id", "timestamp"]),
    ]

def create_transformed_data_validators():
    """Validators for transformed data"""
    return [
        NullCheckValidator("no_nulls", ["id", "date"]),
        UniquenessValidator("unique_keys", ["id", "date"]),
    ]

# Use in DAG:
validators = create_api_data_validators("dt", max_age_hours=2)
```

## 🚨 Error Handling

```python
from data_quality_framework.exceptions import ValidationError, ConfigError

def safe_validation_task(ti):
    try:
        # Validation code
        result = orchestrator.run_checks(...)
        return result
        
    except ValidationError as e:
        # Data quality issue
        logger.error(f"Data quality check failed: {e.validation_errors}")
        raise AirflowException(f"Quality gate failure: {e}")
        
    except ConfigError as e:
        # Configuration issue
        logger.error(f"Invalid configuration: {e}")
        raise AirflowException(f"Configuration error: {e}")
        
    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error in validation: {e}")
        raise
```

## 📖 Additional Resources

- [Framework README](../README.md) - Complete framework documentation
- [Architecture Guide](./ARCHITECTURE.md) - Detailed architecture
- [Examples](../examples/) - Runnable code examples
- [OpenWeather Integration](../examples/lakehouse_integration_example.py) - Full integration example

## 🤝 Support

For issues specific to integration with data-lakehouse-simulation:
1. Check the examples in this document
2. Review the framework examples
3. Consult Airflow documentation for task-specific issues

---

**Happy data validating! 🚀**
