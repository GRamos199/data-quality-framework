#!/bin/bash
# Quick start script for Data Quality Framework

echo "=========================================="
echo "Data Quality Framework - Quick Start"
echo "=========================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"
echo ""

# Install dependencies
echo "📌 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Install in development mode
echo "📌 Installing framework in development mode..."
pip install -q -e .
echo "✓ Framework installed"
echo ""

# Run tests
echo "📌 Running test suite..."
echo ""
python -m pytest tests/ -v --tb=short
echo ""

# Run examples
echo "=========================================="
echo "Running Examples"
echo "=========================================="
echo ""

echo "🔍 Example 1: All Validator Types"
echo "-----------------------------------"
python examples/openweather_examples.py 2>&1 | head -100
echo ""

echo "🔌 Example 2: Lakehouse ETL Integration"
echo "---------------------------------------"
python examples/lakehouse_integration_example.py
echo ""

echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Read: README.md"
echo "  2. Review: docs/ARCHITECTURE.md"
echo "  3. Integrate: docs/INTEGRATION_GUIDE.md"
echo "  4. Check: examples/ for more examples"
echo ""
