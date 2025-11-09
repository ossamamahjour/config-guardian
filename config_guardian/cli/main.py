"""Main CLI entrypoint."""

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from config_guardian.discover import find_yaml_files
from config_guardian.validate import ConfigValidator
from config_guardian.plugins import PluginLoader
from config_guardian.reporting import Reporter
from config_guardian.watcher import FileWatcher
from config_guardian.models import ValidationResult

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def validate_with_plugins(
    file_path: Path,
    validator: ConfigValidator,
    plugin_loader: PluginLoader
) -> ValidationResult:
    """
    Validate a file with core validator and plugins.
    
    Args:
        file_path: Path to file
        validator: Core validator instance
        plugin_loader: Plugin loader instance
        
    Returns:
        ValidationResult with all issues
    """
    result = validator.validate_file(file_path)
    
    # Run plugins if config loaded successfully
    if result.config:
        plugin_issues = plugin_loader.run_plugins(result.config)
        result.issues.extend(plugin_issues)
        
        # Mark as invalid if plugins found errors
        if any(issue.severity == "error" for issue in plugin_issues):
            result.is_valid = False
    
    return result


def run_validation(
    root_dir: str,
    output_path: str,
    workers: int,
    plugins_dir: str
) -> None:
    """
    Run validation on all YAML files in directory.
    
    Args:
        root_dir: Root directory to scan
        output_path: Path for output JSON report
        workers: Number of concurrent workers
        plugins_dir: Directory containing plugins
    """
    logger.info(f"Starting validation for: {root_dir}")
    
    # Discover files
    yaml_files = find_yaml_files(root_dir)
    
    if not yaml_files:
        logger.warning("No YAML files found")
        print("⚠️  No YAML files found in the specified directory.")
        return
    
    # Load plugins
    plugin_loader = PluginLoader(plugins_dir)
    
    # Validate files concurrently
    validator = ConfigValidator()
    results: List[ValidationResult] = []
    
    logger.info(f"Validating {len(yaml_files)} files with {workers} workers...")
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(validate_with_plugins, f, validator, plugin_loader): f
            for f in yaml_files
        }
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                file_path = futures[future]
                logger.error(f"Failed to validate {file_path}: {e}")
                results.append(
                    ValidationResult(
                        file_path=str(file_path),
                        is_valid=False,
                        issues=[]
                    )
                )
    
    # Generate and save report
    reporter = Reporter(root_dir)
    report = reporter.generate_report(results)
    reporter.save_report(report, output_path)
    reporter.print_summary(report)


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Config Guardian - Concurrent Configuration Deployment Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory to scan for YAML files (default: current directory)"
    )
    
    parser.add_argument(
        "--out",
        type=str,
        default="report.json",
        help="Output path for JSON report (default: report.json)"
    )
    
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for file changes and revalidate"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent workers (default: 4)"
    )
    
    parser.add_argument(
        "--plugins",
        type=str,
        default="plugins",
        help="Directory containing validation plugins (default: plugins)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Validate root directory exists
    if not Path(args.root).exists():
        logger.error(f"Root directory does not exist: {args.root}")
        sys.exit(1)
    
    if args.watch:
        # Run initial validation
        run_validation(args.root, args.out, args.workers, args.plugins)
        
        # Start watching
        def on_change():
            run_validation(args.root, args.out, args.workers, args.plugins)
        
        watcher = FileWatcher(args.root, on_change)
        watcher.start()
    else:
        # Run once
        run_validation(args.root, args.out, args.workers, args.plugins)


if __name__ == "__main__":
    main()
