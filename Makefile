.PHONY: help install test run clean lint

help:
	@echo "Config Guardian - Makefile Commands"
	@echo ""
	@echo "  make install    Install dependencies in virtualenv"
	@echo "  make test       Run unit tests with pytest"
	@echo "  make run        Run validator on examples/ directory"
	@echo "  make watch      Run validator in watch mode"
	@echo "  make lint       Run code quality checks (if available)"
	@echo "  make clean      Remove generated files and cache"
	@echo ""

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

run:
	python -m config_guardian --root examples --out report.json

watch:
	python -m config_guardian --root examples --out report.json --watch

lint:
	@echo "Running basic Python syntax check..."
	python -m py_compile config_guardian/**/*.py
	@echo "Lint check completed."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f report.json
	@echo "Cleaned up generated files."
