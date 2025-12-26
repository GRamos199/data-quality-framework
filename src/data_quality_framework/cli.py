"""
Command-line interface for Data Quality Framework
Built with Click for easy command creation
"""

import click
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

from data_quality_framework.orchestrator import QualityCheckOrchestrator
from data_quality_framework.config_loader import ConfigLoader
from data_quality_framework.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

@click.group()
def cli():
    """
    Data Quality Framework CLI
    
    A powerful tool for validating data quality in your lakehouse pipelines.
    """
    pass

# Validation Commands

@cli.command()
@click.option('--config', required=True, help='Path to validation config (YAML)')
@click.option('--data', required=True, help='Path to data file (JSON or CSV)')
@click.option('--dataset', required=True, help='Dataset name')
@click.option('--layer', required=True, help='Data layer (raw, clean, etc.)')
@click.option('--stop-on-failure', is_flag=True, default=False, help='Stop on first failure')
def validate(config: str, data: str, dataset: str, layer: str, stop_on_failure: bool):
    """
    Validate data against a configuration
    
    Example:
        dqf validate --config config/raw.yaml --data data.json --dataset openweather --layer raw
    """
    try:
        click.echo(f"\n🔍 Starting validation...")
        click.echo(f"   Config: {config}")
        click.echo(f"   Data: {data}")
        click.echo(f"   Dataset: {dataset}")
        click.echo(f"   Layer: {layer}\n")
        
        start_time = datetime.utcnow()
        
        # Load configuration
        config_obj = ConfigLoader.load_yaml(config)
        
        # Load data
        data_path = Path(data)
        if data_path.suffix == '.json':
            with open(data) as f:
                data_obj = json.load(f)
            df = pd.DataFrame([data_obj] if isinstance(data_obj, dict) else data_obj)
        elif data_path.suffix == '.csv':
            df = pd.read_csv(data)
        else:
            raise ValueError("Unsupported file format. Use JSON or CSV.")
        
        click.echo(f"   Loaded {len(df)} rows\n")
        
        # Run validation
        orchestrator = QualityCheckOrchestrator()
        result = orchestrator.run_checks(
            data=df,
            validators=[],
            dataset_name=dataset,
            layer=layer,
            stop_on_failure=stop_on_failure
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Display results
        if result.passed:
            click.secho(f"✅ Validation PASSED", fg='green', bold=True)
        else:
            click.secho(f"❌ Validation FAILED", fg='red', bold=True)
        
        click.echo(f"\n📊 Results:")
        click.echo(f"   Execution time: {execution_time:.3f}s")
        click.echo(f"   Rows validated: {len(df)}")
        
        if result.errors:
            click.echo(f"\n⚠️  Errors:")
            for error_type, messages in result.errors.items():
                click.echo(f"   - {error_type}:")
                for msg in messages:
                    click.echo(f"     • {msg}")
        
        # Save to database
        db.add_validation_run(
            dataset_name=dataset,
            layer=layer,
            passed=result.passed,
            execution_time=execution_time,
            config_path=config,
            errors=result.errors,
            row_count=len(df)
        )
        
        return 0 if result.passed else 1
        
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg='red')
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        return 1

@cli.command()
@click.option('--dataset', required=True, help='Dataset name')
@click.option('--limit', default=10, help='Number of records to show')
def history(dataset: str, limit: int):
    """
    Show validation history for a dataset
    
    Example:
        dqf history --dataset openweather --limit 5
    """
    try:
        click.echo(f"\n📋 Validation History: {dataset}\n")
        
        runs = db.get_validation_history(dataset, limit=limit)
        
        if not runs:
            click.secho("No validation history found", fg='yellow')
            return
        
        # Display in table format
        click.echo(f"{'#':<3} {'Timestamp':<20} {'Layer':<10} {'Status':<8} {'Time (s)':<8}")
        click.echo("-" * 60)
        
        for i, run in enumerate(runs, 1):
            status = "✅ PASS" if run.passed else "❌ FAIL"
            click.echo(
                f"{i:<3} {run.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<20} "
                f"{run.layer:<10} {status:<8} {run.execution_time_seconds:<8.3f}"
            )
        
        # Show stats
        stats = db.get_validation_stats(dataset)
        click.echo(f"\n📊 Statistics:")
        click.echo(f"   Total runs: {stats['total_runs']}")
        click.echo(f"   Passed: {stats['passed']}")
        click.echo(f"   Failed: {stats['failed']}")
        click.echo(f"   Pass rate: {stats['pass_rate']:.1f}%")
        click.echo(f"   Avg time: {stats['avg_execution_time']:.3f}s\n")
        
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg='red')
        logger.error(f"History error: {str(e)}", exc_info=True)

# Configuration Commands

@cli.command()
def list_configs():
    """List all available validation configurations"""
    try:
        click.echo(f"\n📂 Available Configurations:\n")
        
        config_dir = Path("config")
        if not config_dir.exists():
            click.secho("No config directory found", fg='yellow')
            return
        
        configs = list(config_dir.glob("*.yaml"))
        
        if not configs:
            click.secho("No configurations found", fg='yellow')
            return
        
        for config_file in sorted(configs):
            try:
                config = ConfigLoader.load_yaml(str(config_file))
                dataset = config.get('dataset', 'unknown')
                layer = config.get('layer', 'unknown')
                rules_count = len(config.get('rules', []))
                
                click.echo(f"  📋 {config_file.stem}")
                click.echo(f"     Dataset: {dataset}")
                click.echo(f"     Layer: {layer}")
                click.echo(f"     Rules: {rules_count}\n")
            except Exception as e:
                click.secho(f"  ⚠️  {config_file.stem} (error: {str(e)})", fg='yellow')
        
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg='red')

@cli.command()
@click.option('--name', required=True, help='Configuration name')
def show_config(name: str):
    """Show details of a configuration"""
    try:
        config = ConfigLoader.load_yaml(f"config/{name}.yaml")
        
        click.echo(f"\n📋 Configuration: {name}\n")
        click.echo(json.dumps(config, indent=2))
        
    except FileNotFoundError:
        click.secho(f"❌ Configuration not found: {name}", fg='red')
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg='red')

# Database Commands

@cli.command()
def init_db():
    """Initialize the database"""
    try:
        click.echo("\n🗄️  Initializing database...")
        db.create_tables()
        click.secho("✅ Database initialized successfully", fg='green')
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg='red')

@cli.command()
def stats():
    """Show validation statistics"""
    try:
        click.echo(f"\n📊 Database Statistics\n")
        
        session = db.get_session()
        try:
            from data_quality_framework.database import ValidationRun
            
            total_runs = session.query(ValidationRun).count()
            passed_runs = session.query(ValidationRun).filter(
                ValidationRun.passed == True
            ).count()
            
            datasets = session.query(ValidationRun.dataset_name).distinct().all()
            
            click.echo(f"Total validation runs: {total_runs}")
            click.echo(f"Passed: {passed_runs}")
            click.echo(f"Failed: {total_runs - passed_runs}")
            
            if total_runs > 0:
                click.echo(f"Pass rate: {(passed_runs/total_runs)*100:.1f}%")
            
            click.echo(f"\nDatasets validated: {len(datasets)}")
            for dataset in datasets:
                click.echo(f"  - {dataset[0]}")
        finally:
            session.close()
        
    except Exception as e:
        click.secho(f"❌ Error: {str(e)}", fg='red')

# Help command
@cli.command()
def examples():
    """Show usage examples"""
    examples_text = """
    📚 Data Quality Framework CLI Examples
    
    1. Validate data:
       $ dqf validate --config config/raw.yaml --data data.json --dataset openweather --layer raw
    
    2. Show validation history:
       $ dqf history --dataset openweather --limit 10
    
    3. List configurations:
       $ dqf list-configs
    
    4. Show configuration details:
       $ dqf show-config --name raw
    
    5. Initialize database:
       $ dqf init-db
    
    6. Show statistics:
       $ dqf stats
    
    For more help on a specific command:
       $ dqf COMMAND --help
    """
    click.echo(examples_text)

if __name__ == '__main__':
    cli()
