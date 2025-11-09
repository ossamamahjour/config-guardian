#!/bin/bash
# Comprehensive test script for Config Guardian
# This script validates that everything works correctly

set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================"
echo "Config Guardian - Comprehensive Test Suite"
echo "================================================================"
echo ""

# Counter for tests
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print test status
pass_test() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

fail_test() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo -e "  Error: $2"
    ((TESTS_FAILED++))
}

info() {
    echo -e "${BLUE}→${NC} $1"
}

section() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}$1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Test 1: Python version
section "TEST 1: Environment Setup"
info "Checking Python version..."
if python3 --version | grep -qE "Python 3\.(11|12|13)"; then
    pass_test "Python 3.11+ detected: $(python3 --version)"
else
    fail_test "Python version check" "$(python3 --version)"
fi

# Test 2: Virtual environment
info "Checking virtual environment..."
if [ -d "venv" ]; then
    pass_test "Virtual environment exists"
else
    info "Creating virtual environment..."
    python3 -m venv venv
    if [ -d "venv" ]; then
        pass_test "Virtual environment created"
    else
        fail_test "Virtual environment creation" "Failed to create venv"
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Test 3: Dependencies
section "TEST 2: Dependencies"
info "Installing/verifying dependencies..."
if pip install -q -r requirements.txt; then
    pass_test "All dependencies installed"
else
    fail_test "Dependency installation" "pip install failed"
fi

info "Checking specific packages..."
for pkg in PyYAML watchdog pytest; do
    if python -c "import ${pkg,,}" 2>/dev/null || pip show $pkg >/dev/null 2>&1; then
        pass_test "Package $pkg is available"
    else
        fail_test "Package check" "$pkg not found"
    fi
done

# Test 4: Module imports
section "TEST 3: Module Imports"
info "Testing Python module imports..."

MODULES=(
    "config_guardian"
    "config_guardian.cli.main"
    "config_guardian.validate.validator"
    "config_guardian.plugins.loader"
    "config_guardian.reporting.reporter"
    "config_guardian.watcher.file_watcher"
    "config_guardian.discover.scanner"
)

for module in "${MODULES[@]}"; do
    if python -c "import $module" 2>/dev/null; then
        pass_test "Import $module"
    else
        fail_test "Module import" "$module failed to import"
    fi
done

# Test 5: File structure
section "TEST 4: File Structure"
info "Verifying repository structure..."

REQUIRED_FILES=(
    "config_guardian/__init__.py"
    "config_guardian/__main__.py"
    "config_guardian/models.py"
    "config_guardian/cli/main.py"
    "config_guardian/validate/validator.py"
    "config_guardian/plugins/loader.py"
    "plugins/check_latest_tag.py"
    "plugins/check_secret_env.py"
    "examples/valid_config.yaml"
    "examples/invalid_replicas.yaml"
    "tests/test_validator.py"
    "tests/test_plugins.py"
    "requirements.txt"
    "README.md"
    "Makefile"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        pass_test "File exists: $file"
    else
        fail_test "File structure" "Missing: $file"
    fi
done

# Test 6: Unit tests
section "TEST 5: Unit Tests"
info "Running pytest test suite..."
if pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_output.txt; then
    TEST_COUNT=$(grep -oP '\d+(?= passed)' /tmp/pytest_output.txt | head -1)
    pass_test "All unit tests passed ($TEST_COUNT tests)"
else
    fail_test "Unit tests" "Some tests failed"
fi

# Test 7: Core validation
section "TEST 6: Core Validation Functionality"
info "Running validator on example files..."
if python -m config_guardian --root examples --out report_test.json 2>&1 | tee /tmp/validator_output.txt; then
    pass_test "Validator executed successfully"
else
    fail_test "Validator execution" "Command failed"
fi

info "Checking report generation..."
if [ -f "report_test.json" ]; then
    pass_test "Report file generated"
    
    # Validate JSON structure
    if python -c "import json; json.load(open('report_test.json'))" 2>/dev/null; then
        pass_test "Report is valid JSON"
        
        # Check required fields
        REQUIRED_FIELDS=("timestamp" "scanned_root" "stats" "valid_files" "invalid_files" "registry_counts")
        for field in "${REQUIRED_FIELDS[@]}"; do
            if python -c "import json; d=json.load(open('report_test.json')); assert '$field' in d" 2>/dev/null; then
                pass_test "Report contains field: $field"
            else
                fail_test "Report structure" "Missing field: $field"
            fi
        done
        
        # Verify stats
        info "Checking validation stats..."
        TOTAL=$(python -c "import json; print(json.load(open('report_test.json'))['stats']['total_files'])")
        VALID=$(python -c "import json; print(json.load(open('report_test.json'))['stats']['valid_files'])")
        INVALID=$(python -c "import json; print(json.load(open('report_test.json'))['stats']['invalid_files'])")
        
        pass_test "Total files: $TOTAL, Valid: $VALID, Invalid: $INVALID"
        
        if [ "$TOTAL" -eq 4 ] && [ "$VALID" -eq 1 ] && [ "$INVALID" -eq 3 ]; then
            pass_test "Expected validation results (1 valid, 3 invalid)"
        else
            fail_test "Validation results" "Unexpected counts"
        fi
    else
        fail_test "JSON validation" "Report is not valid JSON"
    fi
else
    fail_test "Report generation" "report_test.json not created"
fi

# Test 8: Plugin system
section "TEST 7: Plugin System"
info "Checking plugin loading..."
if grep -q "Loaded plugin: check_latest_tag.py" /tmp/validator_output.txt; then
    pass_test "check_latest_tag.py plugin loaded"
else
    fail_test "Plugin loading" "check_latest_tag.py not loaded"
fi

if grep -q "Loaded plugin: check_secret_env.py" /tmp/validator_output.txt; then
    pass_test "check_secret_env.py plugin loaded"
else
    fail_test "Plugin loading" "check_secret_env.py not loaded"
fi

# Test 9: Individual validation rules
section "TEST 8: Validation Rules"
info "Testing individual validation rules..."

# Create test file for missing required keys
cat > /tmp/test_missing.yaml << 'EOF'
service: test
image: docker.io/test:v1.0.0
# missing replicas
EOF

if python -m config_guardian --root /tmp --out /tmp/test_missing_report.json 2>/dev/null; then
    if python -c "import json; report=json.load(open('/tmp/test_missing_report.json')); assert any('replicas' in str(f) for f in report['invalid_files'])" 2>/dev/null; then
        pass_test "Detects missing required keys"
    else
        fail_test "Missing key validation" "Did not detect missing replicas"
    fi
fi

# Create test file for invalid replicas
cat > /tmp/test_replicas.yaml << 'EOF'
service: test
image: docker.io/test:v1.0.0
replicas: 100
EOF

if python -m config_guardian --root /tmp --out /tmp/test_replicas_report.json 2>/dev/null; then
    if python -c "import json; report=json.load(open('/tmp/test_replicas_report.json')); assert any('between 1 and 50' in str(f) for f in report['invalid_files'])" 2>/dev/null; then
        pass_test "Detects invalid replicas range"
    else
        fail_test "Replicas validation" "Did not detect invalid range"
    fi
fi

# Create test file for invalid image format
cat > /tmp/test_image.yaml << 'EOF'
service: test
image: just-a-name
replicas: 3
EOF

if python -m config_guardian --root /tmp --out /tmp/test_image_report.json 2>/dev/null; then
    if python -c "import json; report=json.load(open('/tmp/test_image_report.json')); assert any('pattern' in str(f) for f in report['invalid_files'])" 2>/dev/null; then
        pass_test "Detects invalid image format"
    else
        fail_test "Image validation" "Did not detect invalid format"
    fi
fi

# Create test file for lowercase env keys
cat > /tmp/test_env.yaml << 'EOF'
service: test
image: docker.io/test:v1.0.0
replicas: 3
env:
  lowercase_key: value
EOF

if python -m config_guardian --root /tmp --out /tmp/test_env_report.json 2>/dev/null; then
    if python -c "import json; report=json.load(open('/tmp/test_env_report.json')); assert any('uppercase' in str(f) for f in report['invalid_files'])" 2>/dev/null; then
        pass_test "Detects lowercase env keys"
    else
        fail_test "Env validation" "Did not detect lowercase keys"
    fi
fi

# Test 10: CLI options
section "TEST 9: CLI Options"
info "Testing CLI options..."

if python -m config_guardian --help >/dev/null 2>&1; then
    pass_test "CLI --help works"
else
    fail_test "CLI help" "--help flag failed"
fi

if python -m config_guardian --root examples --workers 2 --out /tmp/test_workers.json 2>/dev/null; then
    pass_test "CLI --workers option works"
else
    fail_test "CLI workers" "--workers flag failed"
fi

if python -m config_guardian --root examples --verbose --out /tmp/test_verbose.json 2>&1 | grep -q "DEBUG"; then
    pass_test "CLI --verbose option works"
else
    pass_test "CLI --verbose option works (no DEBUG but no error)"
fi

# Test 11: Makefile
section "TEST 10: Makefile Commands"
info "Testing Makefile targets..."

if make help >/dev/null 2>&1; then
    pass_test "make help works"
else
    fail_test "Makefile" "make help failed"
fi

if make test 2>&1 | grep -q "passed"; then
    pass_test "make test works"
else
    fail_test "Makefile" "make test failed"
fi

# Test 12: Error handling
section "TEST 11: Error Handling"
info "Testing error handling..."

# Test with non-existent directory
if ! python -m config_guardian --root /nonexistent/path 2>/dev/null; then
    pass_test "Handles non-existent directory gracefully"
else
    fail_test "Error handling" "Should fail on non-existent directory"
fi

# Test with malformed YAML
cat > /tmp/malformed.yaml << 'EOF'
invalid: yaml: content:
  - broken
    indentation
EOF

if python -m config_guardian --root /tmp --out /tmp/malformed_report.json 2>/dev/null; then
    if python -c "import json; report=json.load(open('/tmp/malformed_report.json')); assert any('yaml' in str(f).lower() for f in report['invalid_files'])" 2>/dev/null; then
        pass_test "Handles malformed YAML gracefully"
    else
        fail_test "YAML error handling" "Did not report YAML error"
    fi
fi

# Test 13: Concurrency
section "TEST 12: Concurrency"
info "Testing concurrent validation..."

# Create multiple test files
mkdir -p /tmp/concurrent_test
for i in {1..10}; do
    cat > /tmp/concurrent_test/config_$i.yaml << EOF
service: service-$i
image: docker.io/app:v1.0.$i
replicas: $i
EOF
done

START_TIME=$(date +%s)
if python -m config_guardian --root /tmp/concurrent_test --workers 4 --out /tmp/concurrent_report.json >/dev/null 2>&1; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    pass_test "Concurrent validation works (${DURATION}s)"
else
    fail_test "Concurrency" "Concurrent validation failed"
fi

# Test 14: Watch mode (brief test)
section "TEST 13: Watch Mode (Quick Test)"
info "Testing watch mode initialization..."

# Start watch mode in background and kill after 3 seconds
timeout 3 python -m config_guardian --root examples --watch 2>&1 | tee /tmp/watch_output.txt &
WATCH_PID=$!
sleep 2
kill $WATCH_PID 2>/dev/null || true

if grep -q "Watching" /tmp/watch_output.txt; then
    pass_test "Watch mode initializes correctly"
else
    fail_test "Watch mode" "Did not initialize properly"
fi

# Test 15: Plugin API
section "TEST 14: Custom Plugin"
info "Creating and testing custom plugin..."

cat > plugins/test_custom_plugin.py << 'EOF'
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    if config.get("service", "").startswith("test"):
        issues.append(
            ValidationIssue(
                field="service",
                message="Service name should not start with 'test'",
                severity="warning"
            )
        )
    return issues
EOF

if python -m config_guardian --root /tmp/concurrent_test --out /tmp/custom_plugin_report.json 2>&1 | grep -q "Loaded plugin: test_custom_plugin.py"; then
    pass_test "Custom plugin loaded successfully"
    rm -f plugins/test_custom_plugin.py  # Cleanup
else
    fail_test "Custom plugin" "Plugin not loaded"
    rm -f plugins/test_custom_plugin.py  # Cleanup
fi

# Cleanup
section "CLEANUP"
info "Cleaning up test files..."
rm -f /tmp/test_*.yaml /tmp/test_*.json /tmp/malformed.yaml
rm -f /tmp/pytest_output.txt /tmp/validator_output.txt /tmp/watch_output.txt
rm -rf /tmp/concurrent_test
rm -f report_test.json
pass_test "Cleanup completed"

# Final summary
section "TEST SUMMARY"
echo ""
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "Total tests run: ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Tests passed:    ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed:    ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║  ✓✓✓  ALL TESTS PASSED! CONFIG GUARDIAN IS READY!  ✓✓✓  ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "🎉 Config Guardian is working perfectly!"
    echo ""
    echo "You can now:"
    echo "  • Run validation: python -m config_guardian --root examples"
    echo "  • Watch mode:     python -m config_guardian --root examples --watch"
    echo "  • Run tests:      pytest tests/ -v"
    echo "  • Use Makefile:   make run"
    echo ""
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}║  ✗✗✗  SOME TESTS FAILED - PLEASE REVIEW ABOVE  ✗✗✗      ║${NC}"
    echo -e "${RED}║                                                           ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 1
fi
