# Config Guardian - Command Reference

## Quick Setup (WSL Ubuntu)

```bash
# Clone/Navigate to repository
cd config-guardian

# Run automated setup
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Validator

### Basic Usage
```bash
# Activate virtual environment first
source venv/bin/activate

# Validate examples directory
python -m config_guardian --root examples --out report.json

# Validate current directory
python -m config_guardian --out report.json

# Validate specific directory
python -m config_guardian --root /path/to/configs --out validation_report.json
```

### With Options
```bash
# Use more workers for faster validation
python -m config_guardian --root examples --workers 8

# Enable verbose logging
python -m config_guardian --root examples --verbose

# Custom plugin directory
python -m config_guardian --root examples --plugins /path/to/plugins

# All options combined
python -m config_guardian \
  --root /path/to/configs \
  --out custom_report.json \
  --workers 8 \
  --plugins ./custom_plugins \
  --verbose
```

### Watch Mode
```bash
# Watch for changes and revalidate automatically
python -m config_guardian --root examples --watch

# Watch with verbose output
python -m config_guardian --root examples --watch --verbose

# Stop watching: Press Ctrl+C
```

## Using Makefile

```bash
# Show available commands
make help

# Install dependencies
make install

# Run tests
make test

# Run validator on examples
make run

# Run in watch mode
make watch

# Clean generated files
make clean

# Run basic lint check
make lint
```

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_validator.py -v
pytest tests/test_plugins.py -v

# Run with detailed output
pytest tests/ -v --tb=long

# Run with coverage (requires pytest-cov)
pip install pytest-cov
pytest tests/ --cov=config_guardian --cov-report=html
```

## Development Commands

```bash
# Check Python syntax
python -m py_compile config_guardian/**/*.py

# Format code (if black is installed)
pip install black
black config_guardian/ tests/ plugins/

# Type checking (if mypy is installed)
pip install mypy
mypy config_guardian/

# Interactive Python with package loaded
source venv/bin/activate
python
>>> from config_guardian.validate import ConfigValidator
>>> validator = ConfigValidator()
```

## Example Workflows

### Validate Production Configs
```bash
# 1. Activate environment
source venv/bin/activate

# 2. Run validation
python -m config_guardian \
  --root /mnt/c/projects/my-app/k8s-configs \
  --out production_validation.json \
  --workers 8

# 3. Check report
cat production_validation.json | jq '.stats'
```

### Continuous Validation During Development
```bash
# Terminal 1: Watch mode
source venv/bin/activate
python -m config_guardian --root ./configs --watch

# Terminal 2: Edit configs
vim configs/service.yaml
# Save - validation runs automatically
```

### Add Custom Plugin
```bash
# 1. Create plugin file
cat > plugins/my_custom_check.py << 'EOF'
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    # Your validation logic
    return issues
EOF

# 2. Run validator (plugin auto-loaded)
python -m config_guardian --root examples
```

## Troubleshooting

### Reset Virtual Environment
```bash
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Fix Permission Issues (WSL)
```bash
chmod +x setup.sh
chmod +x config_guardian/__main__.py
```

### View Detailed Logs
```bash
python -m config_guardian --root examples --verbose 2>&1 | tee validation.log
```

### Check Dependencies
```bash
source venv/bin/activate
pip list
```

## WSL-Specific Commands

```bash
# Access Windows directories
python -m config_guardian --root /mnt/c/Users/YourName/Documents/configs

# Copy report to Windows
cp report.json /mnt/c/Users/YourName/Desktop/

# Run from Windows path
cd /mnt/c/projects/config-guardian
source venv/bin/activate
python -m config_guardian --root ./configs
```

## CI/CD Integration Examples

### GitHub Actions
```yaml
- name: Validate Configs
  run: |
    pip install -r requirements.txt
    python -m config_guardian --root configs --out report.json
    
- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: validation-report
    path: report.json
```

### GitLab CI
```yaml
validate:
  script:
    - pip install -r requirements.txt
    - python -m config_guardian --root configs --out report.json
  artifacts:
    paths:
      - report.json
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

source venv/bin/activate
python -m config_guardian --root configs --out report.json

if [ $? -ne 0 ]; then
  echo "Config validation failed!"
  exit 1
fi
```
