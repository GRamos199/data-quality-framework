"""
Example scripts demonstrating the framework usage with real OpenWeather scenarios
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from datetime import datetime, timedelta
from data_quality_framework import (
    SchemaValidator,
    NullCheckValidator,
    UniquenessValidator,
    RangeValidator,
    FreshnessValidator,
    CompositeValidator,
)
from data_quality_framework.orchestrator import QualityCheckOrchestrator


def create_valid_raw_data() -> pd.DataFrame:
    """Create valid OpenWeather raw API data"""
    now = datetime.utcnow()
    
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "city": ["Buenos Aires", "Madrid", "Sydney", "Tokyo", "New York"],
        "dt": [now - timedelta(minutes=30) for _ in range(5)],
        "temperature": [28.5, 15.2, 22.1, 12.8, 5.3],
        "feels_like": [27.8, 14.5, 21.5, 11.2, 4.1],
        "temp_min": [26.0, 13.0, 20.0, 10.0, 2.0],
        "temp_max": [30.0, 17.0, 24.0, 15.0, 8.0],
        "pressure": [1013, 1020, 1015, 1018, 1025],
        "humidity": [65, 45, 55, 70, 60],
        "weather_main": ["Clear", "Cloudy", "Partly Cloudy", "Rainy", "Snowy"],
        "weather_description": ["clear sky", "overcast clouds", "partly cloudy", "light rain", "light snow"],
        "wind_speed": [5.2, 8.1, 3.5, 12.0, 6.8],
        "wind_deg": [230, 180, 90, 270, 45],
        "cloudiness": [0, 80, 40, 95, 100],
        "rain_1h": [0.0, 0.0, 0.0, 2.5, 0.0],
    })


def create_invalid_raw_data_missing_fields() -> pd.DataFrame:
    """Create invalid data with missing required fields"""
    now = datetime.utcnow()
    
    data = create_valid_raw_data()
    # Introduce nulls in mandatory fields
    data.loc[0, "city"] = None
    data.loc[1, "temperature"] = None
    data.loc[2, "humidity"] = None
    return data


def create_invalid_raw_data_out_of_range() -> pd.DataFrame:
    """Create data with out-of-range values"""
    data = create_valid_raw_data()
    # Temperature way too high
    data.loc[0, "temperature"] = 150.0
    # Invalid humidity
    data.loc[1, "humidity"] = 250
    # Impossible wind speed
    data.loc[2, "wind_speed"] = 200.0
    return data


def create_invalid_raw_data_stale() -> pd.DataFrame:
    """Create data that's too old (API ingestion should be recent)"""
    old_time = datetime.utcnow() - timedelta(days=5)
    
    data = create_valid_raw_data()
    data["dt"] = [old_time for _ in range(len(data))]
    return data


def create_valid_clean_data() -> pd.DataFrame:
    """Create valid transformed/clean data"""
    now = datetime.utcnow()
    
    return pd.DataFrame({
        "city_id": [1, 2, 3, 4, 5],
        "city_name": ["Buenos Aires", "Madrid", "Sydney", "Tokyo", "New York"],
        "country": ["AR", "ES", "AU", "JP", "US"],
        "measurement_date": [now - timedelta(hours=1) for _ in range(5)],
        "temperature_celsius": [28.5, 15.2, 22.1, 12.8, 5.3],
        "feels_like_celsius": [27.8, 14.5, 21.5, 11.2, 4.1],
        "humidity_percentage": [65, 45, 55, 70, 60],
        "weather_condition": ["Clear", "Cloudy", "Partly Cloudy", "Rainy", "Snowy"],
        "wind_speed_ms": [5.2, 8.1, 3.5, 12.0, 6.8],
        "cloudiness_percentage": [0, 80, 40, 95, 100],
        "pressure_hpa": [1013, 1020, 1015, 1018, 1025],
        "precipitation_mm": [0.0, 0.0, 0.0, 2.5, 0.0],
        "data_quality_score": [0.98, 0.95, 0.99, 0.92, 0.97],
        "ingestion_timestamp": [now for _ in range(5)],
    })


def create_invalid_clean_data_duplicates() -> pd.DataFrame:
    """Create clean data with duplicate city-date combinations"""
    data = create_valid_clean_data()
    # Add duplicate row
    duplicate = data.iloc[0].copy()
    data = pd.concat([data, pd.DataFrame([duplicate])], ignore_index=True)
    return data


def create_invalid_clean_data_wrong_schema() -> pd.DataFrame:
    """Create clean data with wrong data types"""
    data = create_valid_clean_data()
    # Change temperature to string (wrong type)
    data["temperature_celsius"] = data["temperature_celsius"].astype(str)
    # Add a column that shouldn't exist
    data["extra_column"] = [1, 2, 3, 4, 5, 6]
    return data


def example_1_valid_raw_validation():
    """Example 1: Valid raw data passes all checks"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Valid Raw OpenWeather Data")
    print("="*70)
    
    data = create_valid_raw_data()
    print(f"\nDataset shape: {data.shape}")
    print(f"Columns: {data.columns.tolist()}")
    print(f"\nFirst row:\n{data.iloc[0]}")
    
    # Define validators
    validators = [
        FreshnessValidator("API Freshness", "dt", max_age_hours=1),
        NullCheckValidator("Mandatory Fields", ["city", "dt", "temperature", "humidity"]),
        RangeValidator(
            "Valid Ranges",
            {
                "temperature": {"min": -60, "max": 65},
                "humidity": {"min": 0, "max": 100},
                "pressure": {"min": 870, "max": 1085},
            },
        ),
    ]
    
    # Run checks
    orchestrator = QualityCheckOrchestrator()
    result = orchestrator.run_checks(
        data,
        validators,
        dataset_name="openweather",
        layer="raw",
        stop_on_failure=False,
    )
    
    print(f"\n{result}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")


def example_2_invalid_missing_fields():
    """Example 2: Raw data with missing mandatory fields"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Raw Data with Missing Required Fields")
    print("="*70)
    
    data = create_invalid_raw_data_missing_fields()
    print(f"\nDataset shape: {data.shape}")
    print(f"Nulls per column:\n{data.isnull().sum()}")
    
    validators = [
        NullCheckValidator(
            "Mandatory Fields",
            ["city", "dt", "temperature", "humidity", "weather_main"],
        ),
    ]
    
    orchestrator = QualityCheckOrchestrator()
    result = orchestrator.run_checks(
        data,
        validators,
        dataset_name="openweather",
        layer="raw",
        stop_on_failure=False,
    )
    
    print(f"\n{result}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")
    if result.errors:
        print(f"\nValidation Errors:")
        for validator_name, errors in result.errors.items():
            print(f"  {validator_name}:")
            for error in errors:
                print(f"    - {error}")


def example_3_invalid_out_of_range():
    """Example 3: Raw data with out-of-range values"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Raw Data with Out-of-Range Values")
    print("="*70)
    
    data = create_invalid_raw_data_out_of_range()
    print(f"\nDataset shape: {data.shape}")
    print(f"\nProblematic values:")
    print(f"  Temperature max: {data['temperature'].max()}°C (should be < 65)")
    print(f"  Humidity max: {data['humidity'].max()}% (should be < 100)")
    print(f"  Wind speed max: {data['wind_speed'].max()} m/s (should be < 50)")
    
    validators = [
        RangeValidator(
            "Valid Ranges",
            {
                "temperature": {"min": -60, "max": 65},
                "humidity": {"min": 0, "max": 100},
                "wind_speed": {"min": 0, "max": 50},
            },
        ),
    ]
    
    orchestrator = QualityCheckOrchestrator()
    result = orchestrator.run_checks(
        data,
        validators,
        dataset_name="openweather",
        layer="raw",
        stop_on_failure=False,
    )
    
    print(f"\n{result}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")
    if result.errors:
        print(f"\nValidation Errors:")
        for validator_name, errors in result.errors.items():
            for error in errors:
                print(f"  - {error}")


def example_4_stale_data():
    """Example 4: API data that's too old"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Stale API Data (Too Old)")
    print("="*70)
    
    data = create_invalid_raw_data_stale()
    oldest_record = data["dt"].min()
    age_hours = (datetime.utcnow() - oldest_record).total_seconds() / 3600
    print(f"\nOldest record: {oldest_record}")
    print(f"Age: {age_hours:.1f} hours (max allowed: 1 hour)")
    
    validators = [
        FreshnessValidator("API Freshness", "dt", max_age_hours=1),
    ]
    
    orchestrator = QualityCheckOrchestrator()
    result = orchestrator.run_checks(
        data,
        validators,
        dataset_name="openweather",
        layer="raw",
        stop_on_failure=False,
    )
    
    print(f"\n{result}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")
    if result.errors:
        print(f"\nValidation Errors:")
        for error in result.errors.get("API Freshness", []):
            print(f"  - {error}")


def example_5_valid_clean_data():
    """Example 5: Valid clean/transformed data"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Valid Transformed Clean Data")
    print("="*70)
    
    data = create_valid_clean_data()
    print(f"\nDataset shape: {data.shape}")
    print(f"Expected columns: {len(data.columns)}")
    
    validators = [
        NullCheckValidator(
            "Mandatory Fields",
            ["city_id", "city_name", "measurement_date", "temperature_celsius"],
        ),
        UniquenessValidator("Unique City-Date", ["city_id", "measurement_date"]),
        RangeValidator(
            "Valid Ranges",
            {
                "temperature_celsius": {"min": -60, "max": 65},
                "humidity_percentage": {"min": 0, "max": 100},
                "data_quality_score": {"min": 0, "max": 1},
            },
        ),
    ]
    
    orchestrator = QualityCheckOrchestrator()
    result = orchestrator.run_checks(
        data,
        validators,
        dataset_name="openweather",
        layer="clean",
        stop_on_failure=False,
    )
    
    print(f"\n{result}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")


def example_6_duplicate_clean_records():
    """Example 6: Clean data with duplicate city-date combinations"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Clean Data with Duplicate Records")
    print("="*70)
    
    data = create_invalid_clean_data_duplicates()
    duplicates = data[["city_id", "measurement_date"]].duplicated().sum()
    print(f"\nDataset shape: {data.shape}")
    print(f"Duplicate city_id-measurement_date combinations: {duplicates}")
    
    validators = [
        UniquenessValidator("Unique City-Date", ["city_id", "measurement_date"]),
    ]
    
    orchestrator = QualityCheckOrchestrator()
    result = orchestrator.run_checks(
        data,
        validators,
        dataset_name="openweather",
        layer="clean",
        stop_on_failure=False,
    )
    
    print(f"\n{result}")
    print(f"Status: {'✓ PASSED' if result.passed else '✗ FAILED'}")
    if result.errors:
        print(f"\nValidation Errors:")
        for error in result.errors.get("Unique City-Date", []):
            print(f"  - {error}")


def main():
    """Run all examples"""
    examples = [
        example_1_valid_raw_validation,
        example_2_invalid_missing_fields,
        example_3_invalid_out_of_range,
        example_4_stale_data,
        example_5_valid_clean_data,
        example_6_duplicate_clean_records,
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ ERROR in {example_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("All Examples Completed")
    print("="*70)


if __name__ == "__main__":
    main()
