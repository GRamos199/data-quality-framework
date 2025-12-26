.PHONY: help install install-dev test test-cov lint format examples clean

help:
	@echo "Data Quality Framework - Common Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install        - Install the package"
	@echo "  make install-dev    - Install with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run test suite"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo ""
	@echo "Development:"
	@echo "  make lint           - Run linting checks"
	@echo "  make format         - Format code with black"
	@echo ""
	@echo "Examples:"
	@echo "  make examples       - Run all examples"
	@echo "  make example-validators - Run validator examples"
	@echo "  make example-etl    - Run ETL integration example"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make clean-test     - Clean test cache"
	@echo ""

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/data_quality_framework --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Checking Python syntax and style..."
	python -m py_compile src/data_quality_framework/*.py
	python -m py_compile tests/*.py
	python -m py_compile examples/*.py
	@echo "✓ All files have valid syntax"

format:
	@echo "Formatting code..."
	black src/data_quality_framework/ tests/ examples/ setup.py --line-length=88
	@echo "✓ Code formatted"

examples:
	@echo "========================================"
	@echo "Running All Examples"
	@echo "========================================"
	@echo ""
	@echo "1. Validator Examples"
	@echo "-----------------------------------"
	python examples/openweather_examples.py
	@echo ""
	@echo "2. ETL Integration Example"
	@echo "-----------------------------------"
	python examples/lakehouse_integration_example.py
	@echo ""
	@echo "✓ All examples completed"

example-validators:
	python examples/openweather_examples.py

example-etl:
	python examples/lakehouse_integration_example.py

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	@echo "✓ Cleaned build artifacts"

clean-test:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -name ".coverage" -delete
	@echo "✓ Cleaned test cache"

setup-git:
	git init
	git add .
	git commit -m "Initial commit: Data Quality Framework"
	@echo ""
	@echo "Next step: git remote add origin <your-repo-url>"
	@echo "Then: git push -u origin main"

.DEFAULT_GOAL := help
