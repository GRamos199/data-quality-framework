"""
Example: How to use the Data Quality Framework with your JSON file
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
from data_quality_framework import (
    NullCheckValidator,
    RangeValidator,
    SchemaValidator,
    UniquenessValidator,
    FreshnessValidator,
)
from data_quality_framework.orchestrator import QualityCheckOrchestrator
from data_quality_framework.exceptions import ValidationError


def load_json_data(file_path):
    """Load JSON file and convert to DataFrame"""
    print(f"\n[LOAD] Reading JSON file: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data_dict = json.load(f)
        
        # Handle both single object and array
        if isinstance(data_dict, dict):
            df = pd.DataFrame([data_dict])
        else:
            df = pd.DataFrame(data_dict)
        
        print(f"✓ Loaded {len(df)} records")
        print(f"  Columns: {', '.join(df.columns.tolist())}")
        print(f"  Data types:\n{df.dtypes}")
        
        return df
    
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON format in: {file_path}")
        return None
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return None


def validate_raw_data(df):
    """
    Example 1: Basic validation with built-in validators
    Customize these validators based on your data structure
    """
    print("\n[VALIDATE RAW] Running quality checks...")
    
    # Create validators for your data
    # ADJUST THESE BASED ON YOUR JSON STRUCTURE!
    validators = [
        # Check that important columns are not null
        NullCheckValidator(
            "mandatory_fields",
            mandatory_columns=[col for col in df.columns[:3]]  # First 3 columns as mandatory
        ),
        # Check numeric columns are in reasonable ranges
        # UniquenessValidator("unique_id", "id") if "id" in df.columns else None,
    ]
    
    # Remove None validators
    validators = [v for v in validators if v is not None]
    
    orchestrator = QualityCheckOrchestrator()
    
    try:
        result = orchestrator.run_checks(
            df,
            validators,
            dataset_name="my_dataset",
            layer="raw",
            stop_on_failure=False,
        )
        
        if result.passed:
            print(f"✓ All validation checks passed!")
            print(f"  Validators run: {', '.join(result.validators_run)}")
        else:
            print(f"✗ Validation failed:")
            print(f"  Failed validators: {', '.join(result.failed_validators)}")
            for validator_name, errors in result.errors.items():
                print(f"  {validator_name}:")
                for error in errors:
                    print(f"    - {error}")
        
        return result
    
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return None


def show_data_summary(df):
    """Show summary of your data"""
    print("\n[SUMMARY] Data Overview:")
    print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nData types:")
    print(df.dtypes)
    print(f"\nMissing values:")
    print(df.isnull().sum())


def create_custom_validators(df):
    """
    Example 2: Create custom validators based on your data
    """
    print("\n[CUSTOM] Creating validators for your specific data...")
    
    validators = []
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if numeric_cols:
        # For numeric columns, check if they're in reasonable ranges
        ranges = {}
        for col in numeric_cols:
            col_min = df[col].min()
            col_max = df[col].max()
            print(f"  {col}: [{col_min}, {col_max}]")
            ranges[col] = {"min": col_min * 0.8, "max": col_max * 1.2}
        
        validators.append(
            RangeValidator("numeric_ranges", ranges)
        )
    
    return validators


def main():
    """Main execution"""
    
    # ====================================================================
    # STEP 1: Load your JSON file
    # ====================================================================
    # Options:
    # - Put JSON in root: /home/george/data-quality-framework/data.json
    # - Put JSON in data/: /home/george/data-quality-framework/data/data.json
    # - Put JSON anywhere and use full path
    
    json_files = [
        "data.json",              # Root directory
        "data/data.json",         # data/ folder
        "data/example_data.json", # Example file in data folder
        "input.json",             # Or your specific filename
    ]
    
    df = None
    for json_file in json_files:
        if Path(json_file).exists():
            df = load_json_data(json_file)
            if df is not None:
                break
    
    if df is None:
        print("\n✗ No JSON file found!")
        print("\nTry one of these:")
        print("  1. Put your JSON in: /home/george/data-quality-framework/data.json")
        print("  2. Or in: /home/george/data-quality-framework/data/data.json")
        print("  3. Or modify the json_files list above with your filename")
        return
    
    # ====================================================================
    # STEP 2: Show data summary
    # ====================================================================
    show_data_summary(df)
    
    # ====================================================================
    # STEP 3: Run basic validation
    # ====================================================================
    result = validate_raw_data(df)
    
    # ====================================================================
    # STEP 4: Create and run custom validators
    # ====================================================================
    custom_validators = create_custom_validators(df)
    
    if custom_validators:
        print("\n[RUN CUSTOM] Running custom validators...")
        orchestrator = QualityCheckOrchestrator()
        custom_result = orchestrator.run_checks(
            df,
            custom_validators,
            dataset_name="my_dataset",
            layer="raw",
            stop_on_failure=False,
        )
        
        if custom_result.passed:
            print(f"✓ Custom validation passed!")
        else:
            print(f"✗ Custom validation failed")
            for validator_name, errors in custom_result.errors.items():
                print(f"  {validator_name}:")
                for error in errors:
                    print(f"    - {error}")
    
    # ====================================================================
    # STEP 5: Generate report
    # ====================================================================
    print("\n[REPORT]:")
    print("=" * 60)
    print("✓ Data Quality Framework validation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
