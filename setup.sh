#!/bin/bash
# Setup script for Config Guardian

set -e

echo "=================================================="
echo "Config Guardian - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo ""
echo "Installing dependencies..."
venv/bin/pip install -q -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Then you can run:"
echo "  python -m config_guardian --root examples --out report.json"
echo "  pytest tests/ -v"
echo ""
echo "Or use the Makefile commands:"
echo "  make test"
echo "  make run"
echo "  make watch"
echo ""
