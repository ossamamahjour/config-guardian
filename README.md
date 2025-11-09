# Config Guardian

**Concurrent Configuration Deployment Validator** - A robust Python tool for validating YAML configuration files with extensible plugin support and real-time file watching capabilities.

## Features

- 🔍 **Recursive File Discovery**: Efficiently scans directories for `.yaml` and `.yml` files
- ✅ **Core Validation Rules**: Validates required fields, data types, and formats
- ⚡ **Concurrent Processing**: Uses ThreadPoolExecutor for fast validation of multiple files
- 🔌 **Plugin System**: Extensible architecture for custom validation rules
- 📊 **Detailed Reporting**: Generates structured JSON reports with validation results
- 👀 **File Watching**: Real-time monitoring and revalidation of configuration changes
- 🧪 **Well Tested**: Comprehensive unit tests for core functionality

## Requirements

- Python 3.11 or higher
- pip (Python package manager)

## Quick Start

### 1. Setup Virtual Environment

```bash
# Navigate to repository
cd config-guardian

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On WSL Ubuntu / Linux
```

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Run Validator

```bash
# Validate all YAML files in examples/ directory
python -m config_guardian --root examples --out report.json

# Or use the Makefile
make run
```

### 4. Run Tests

```bash
# Run all unit tests
pytest tests/ -v

# Or use the Makefile
make test
```

### 5. Watch Mode

```bash
# Monitor examples/ directory for changes and revalidate automatically
python -m config_guardian --root examples --out report.json --watch

# Or use the Makefile
make watch
```

## Command Line Options

```bash
python -m config_guardian [OPTIONS]

Options:
  --root DIR          Root directory to scan (default: current directory)
  --out FILE          Output JSON report path (default: report.json)
  --watch             Enable file watching mode
  --workers N         Number of concurrent workers (default: 4)
  --plugins DIR       Plugin directory path (default: plugins)
  --verbose           Enable verbose logging
```

## Validation Rules

### Core Rules (Built-in)

1. **Required Keys**: `service`, `image`, `replicas` must be present
2. **Replicas**: Must be an integer between 1 and 50
3. **Image Format**: Must match pattern `<registry>/<service>:<version>`
4. **Environment Variables**: Keys must be UPPERCASE; values must be simple types

### Example Valid Configuration

```yaml
service: web-api
image: docker.io/myapp:v1.2.3
replicas: 3
env:
  DATABASE_URL: postgres://db:5432/mydb
  LOG_LEVEL: INFO
  MAX_CONNECTIONS: "100"
```

## Plugin System

### Plugin API

Plugins are Python files placed in the `plugins/` directory. Each plugin must implement:

```python
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate configuration and return list of issues.
    
    Args:
        config: Configuration dictionary from YAML file
        
    Returns:
        List of ValidationIssue objects
    """
    issues = []
    
    # Your validation logic here
    if some_condition:
        issues.append(
            ValidationIssue(
                field="field_name",
                message="Description of the issue",
                severity="error"  # or "warning"
            )
        )
    
    return issues
```

### Included Plugins

#### 1. `check_latest_tag.py`
Ensures Docker images don't use the `latest` tag (enforces version pinning).

```python
# Fails validation
image: docker.io/app:latest

# Passes validation
image: docker.io/app:v1.2.3
```

#### 2. `check_secret_env.py`
Warns when environment variable keys contain "SECRET" (encourages external secret management).

```python
# Triggers warning
env:
  API_SECRET: "my-secret"

# No warning
env:
  API_KEY_REF: "/path/to/secret"
```

### Creating Custom Plugins

1. Create a new `.py` file in the `plugins/` directory
2. Implement the `run_validations(config: Dict[str, Any]) -> List[ValidationIssue]` function
3. Return a list of `ValidationIssue` objects for any problems found
4. The plugin will be automatically discovered and executed

**Example**: Check minimum replicas

```python
# plugins/check_min_replicas.py
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    replicas = config.get("replicas", 0)
    
    if replicas < 3:
        issues.append(
            ValidationIssue(
                field="replicas",
                message="Production services should have at least 3 replicas for HA",
                severity="warning"
            )
        )
    
    return issues
```

## Report Format

The generated `report.json` contains:

```json
{
  "timestamp": "2025-11-09T20:22:42.251Z",
  "scanned_root": "examples",
  "stats": {
    "total_files": 4,
    "valid_files": 1,
    "invalid_files": 3,
    "total_issues": 5
  },
  "valid_files": [
    {"path": "examples/valid_config.yaml"}
  ],
  "invalid_files": [
    {
      "path": "examples/missing_required_key.yaml",
      "issues": [
        {
          "field": "required_keys",
          "message": "Missing required keys: replicas",
          "severity": "error"
        }
      ]
    }
  ],
  "registry_counts": {
    "docker.io": 2,
    "gcr.io": 1
  }
}
```

## Project Structure

```
config-guardian/
├── config_guardian/           # Main package
│   ├── __init__.py
│   ├── __main__.py           # CLI entry point
│   ├── models.py             # Data models
│   ├── cli/                  # Command-line interface
│   ├── discover/             # File discovery
│   ├── validate/             # Core validation logic
│   ├── plugins/              # Plugin loader
│   ├── reporting/            # Report generation
│   └── watcher/              # File watching
├── plugins/                   # Validation plugins
│   ├── check_latest_tag.py
│   └── check_secret_env.py
├── examples/                  # Example YAML files
│   ├── valid_config.yaml
│   ├── missing_required_key.yaml
│   ├── invalid_replicas.yaml
│   └── env_lowercase_keys.yaml
├── tests/                     # Unit tests
│   ├── test_validator.py
│   └── test_plugins.py
├── requirements.txt          # Python dependencies
├── Makefile                  # Build automation
└── README.md                 # This file
```

## WSL Ubuntu Examples

```bash
# Setup
cd /mnt/c/Users/YourUsername/config-guardian  # Adjust path
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run validation
python -m config_guardian --root examples --out report.json

# Run with more workers
python -m config_guardian --root examples --workers 8

# Watch mode with verbose logging
python -m config_guardian --root examples --watch --verbose

# Run tests
pytest tests/ -v

# Clean up
make clean
```

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_validator.py -v

# With coverage (if pytest-cov installed)
pytest tests/ --cov=config_guardian --cov-report=html
```

### Code Quality

```bash
# Basic syntax check
make lint

# Type checking (if mypy installed)
mypy config_guardian/

# Format code (if black installed)
black config_guardian/ tests/
```

## Troubleshooting

### Virtual Environment Issues
```bash
# Deactivate and recreate if needed
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Permission Errors on WSL
```bash
# If files aren't executable
chmod +x config_guardian/__main__.py
```

### Watch Mode Not Detecting Changes
- Ensure `watchdog` is installed: `pip install watchdog`
- Check file permissions in the watched directory
- Some network drives may not support file system events

## License

MIT License - See repository for details.

## Contributing

Contributions welcome! Please ensure:
- All tests pass: `make test`
- Code follows existing style
- New features include tests
- Documentation is updated

---

**Config Guardian** - Built for reliable, scalable configuration validation.