"""
Integration example showing how to use the framework in a real ETL pipeline
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from datetime import datetime, timedelta
from data_quality_framework import (
    NullCheckValidator,
    UniquenessValidator,
    RangeValidator,
    FreshnessValidator,
)
from data_quality_framework.orchestrator import QualityCheckOrchestrator
from data_quality_framework.exceptions import ValidationError


class LakehouseETLPipeline:
    """
    Example ETL Pipeline that integrates with the Data Quality Framework
    
    Simulates: API -> Raw Layer -> Quality Checks -> Clean Layer -> Analytics
    """
    
    def __init__(self):
        self.orchestrator = QualityCheckOrchestrator()
        self.raw_data = None
        self.clean_data = None
    
    def extract_from_api(self):
        """Step 1: Extract data from OpenWeather API (simulated)"""
        print("\n[EXTRACT] Fetching data from OpenWeather API...")
        
        now = datetime.utcnow()
        self.raw_data = pd.DataFrame({
            "id": [1, 2, 3],
            "city": ["Buenos Aires", "Madrid", "Sydney"],
            "dt": [now - timedelta(minutes=i*15) for i in range(3)],
            "temperature": [28.5, 15.2, 22.1],
            "feels_like": [27.8, 14.5, 21.5],
            "temp_min": [26.0, 13.0, 20.0],
            "temp_max": [30.0, 17.0, 24.0],
            "pressure": [1013, 1020, 1015],
            "humidity": [65, 45, 55],
            "weather_main": ["Clear", "Cloudy", "Partly Cloudy"],
            "weather_description": ["clear sky", "overcast clouds", "partly cloudy"],
            "wind_speed": [5.2, 8.1, 3.5],
            "wind_deg": [230, 180, 90],
            "cloudiness": [0, 80, 40],
            "rain_1h": [0.0, 0.0, 0.0],
        })
        
        print(f"✓ Extracted {len(self.raw_data)} records from API")
        return self.raw_data
    
    def load_raw_layer(self, data: pd.DataFrame):
        """Step 2: Load into RAW layer with quality checks"""
        print("\n[LOAD RAW] Validating data before loading to raw layer...")
        
        validators = [
            FreshnessValidator("API Freshness", "dt", max_age_hours=1),
            NullCheckValidator("Mandatory Fields", ["city", "dt", "temperature"]),
            RangeValidator(
                "Valid Ranges",
                {
                    "temperature": {"min": -60, "max": 65},
                    "humidity": {"min": 0, "max": 100},
                },
            ),
        ]
        
        try:
            result = self.orchestrator.run_checks(
                data,
                validators,
                dataset_name="openweather",
                layer="raw",
                stop_on_failure=True,  # Block invalid data
            )
            
            print(f"✓ Raw layer validation passed")
            print(f"  Validators run: {', '.join(result.validators_run)}")
            return True
            
        except ValidationError as e:
            print(f"✗ Raw layer validation FAILED")
            print(f"  Error: {e}")
            return False
    
    def transform_raw_to_clean(self):
        """Step 3: Transform raw to clean layer"""
        if self.raw_data is None:
            raise ValueError("No raw data to transform")
        
        print("\n[TRANSFORM] Cleaning and transforming raw data...")
        
        # Simulate transformation
        self.clean_data = pd.DataFrame({
            "city_id": self.raw_data["id"],
            "city_name": self.raw_data["city"],
            "country": ["AR", "ES", "AU"],
            "measurement_date": self.raw_data["dt"],
            "temperature_celsius": self.raw_data["temperature"],
            "feels_like_celsius": self.raw_data["feels_like"],
            "humidity_percentage": self.raw_data["humidity"],
            "weather_condition": self.raw_data["weather_main"],
            "wind_speed_ms": self.raw_data["wind_speed"],
            "cloudiness_percentage": self.raw_data["cloudiness"],
            "pressure_hpa": self.raw_data["pressure"],
            "precipitation_mm": self.raw_data["rain_1h"],
            "data_quality_score": [0.98, 0.95, 0.99],
            "ingestion_timestamp": [datetime.utcnow()] * len(self.raw_data),
        })
        
        print(f"✓ Transformed {len(self.clean_data)} records")
        return self.clean_data
    
    def load_clean_layer(self, data: pd.DataFrame):
        """Step 4: Load into CLEAN layer with quality checks"""
        print("\n[LOAD CLEAN] Validating transformed data before loading...")
        
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
        
        try:
            result = self.orchestrator.run_checks(
                data,
                validators,
                dataset_name="openweather",
                layer="clean",
                stop_on_failure=True,  # Block invalid data from reaching analytics
            )
            
            print(f"✓ Clean layer validation passed")
            print(f"  Validators run: {', '.join(result.validators_run)}")
            return True
            
        except ValidationError as e:
            print(f"✗ Clean layer validation FAILED")
            print(f"  Error: {e}")
            return False
    
    def publish_to_analytics(self):
        """Step 5: Publish to analytics layer"""
        if self.clean_data is None:
            raise ValueError("No clean data to publish")
        
        print("\n[PUBLISH] Loading to Analytics layer...")
        print(f"✓ Published {len(self.clean_data)} records to Analytics")
        print(f"  Columns available: {', '.join(self.clean_data.columns.tolist())}")
    
    def run_pipeline(self):
        """Execute the complete ETL pipeline with quality gates"""
        print("\n" + "="*70)
        print("LAKEHOUSE ETL PIPELINE WITH QUALITY GATES")
        print("="*70)
        
        try:
            # Step 1: Extract
            self.extract_from_api()
            
            # Step 2: Validate and load raw
            if not self.load_raw_layer(self.raw_data):
                print("\n⚠️  Pipeline halted: Raw layer validation failed")
                return False
            
            # Step 3: Transform
            self.transform_raw_to_clean()
            
            # Step 4: Validate and load clean
            if not self.load_clean_layer(self.clean_data):
                print("\n⚠️  Pipeline halted: Clean layer validation failed")
                return False
            
            # Step 5: Publish
            self.publish_to_analytics()
            
            print("\n" + "="*70)
            print("✓ PIPELINE COMPLETED SUCCESSFULLY")
            print("="*70)
            
            # Print summary report
            report = self.orchestrator.generate_report()
            print(f"\nValidation Summary:")
            print(f"  Total validations: {report['total_validations']}")
            print(f"  Passed: {report['passed']}")
            print(f"  Failed: {report['failed']}")
            print(f"  Success rate: {report['success_rate']}")
            
            return True
            
        except Exception as e:
            print(f"\n✗ PIPELINE ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run the ETL pipeline example"""
    pipeline = LakehouseETLPipeline()
    success = pipeline.run_pipeline()
    
    print(f"\nFinal Status: {'✓ SUCCESS' if success else '✗ FAILURE'}")


if __name__ == "__main__":
    main()
