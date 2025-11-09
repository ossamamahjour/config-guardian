"""Report generation functionality."""

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from config_guardian.models import ValidationResult

logger = logging.getLogger(__name__)


class Reporter:
    """Generate validation reports in JSON format."""
    
    def __init__(self, scanned_root: str):
        """
        Initialize reporter.
        
        Args:
            scanned_root: Root directory that was scanned
        """
        self.scanned_root = scanned_root
    
    def generate_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Generate structured report from validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Dictionary containing complete report
        """
        valid_files = []
        invalid_files = []
        registry_counts = defaultdict(int)
        total_issues = 0
        
        for result in results:
            if result.is_valid:
                valid_files.append({"path": result.file_path})
                
                # Count services per registry
                if result.config.get("image"):
                    registry = self._extract_registry(result.config["image"])
                    if registry:
                        registry_counts[registry] += 1
            else:
                issues_data = [
                    {
                        "field": issue.field,
                        "message": issue.message,
                        "severity": issue.severity
                    }
                    for issue in result.issues
                ]
                
                invalid_files.append({
                    "path": result.file_path,
                    "issues": issues_data
                })
                
                total_issues += len([i for i in result.issues if i.severity == "error"])
        
        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scanned_root": self.scanned_root,
            "stats": {
                "total_files": len(results),
                "valid_files": len(valid_files),
                "invalid_files": len(invalid_files),
                "total_issues": total_issues
            },
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "registry_counts": dict(registry_counts)
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str) -> None:
        """
        Save report to JSON file.
        
        Args:
            report: Report dictionary
            output_path: Path to save JSON file
        """
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_path}")
        except IOError as e:
            logger.error(f"Failed to save report to {output_path}: {e}")
            raise
    
    def print_summary(self, report: Dict[str, Any]) -> None:
        """Print concise summary to stdout."""
        stats = report["stats"]
        
        print("\n" + "=" * 60)
        print("CONFIG GUARDIAN - VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Scanned: {report['scanned_root']}")
        print(f"Timestamp: {report['timestamp']}")
        print("-" * 60)
        print(f"Total files:    {stats['total_files']}")
        print(f"Valid files:    {stats['valid_files']}")
        print(f"Invalid files:  {stats['invalid_files']}")
        print(f"Total issues:   {stats['total_issues']}")
        print("-" * 60)
        
        if report["registry_counts"]:
            print("Services per registry:")
            for registry, count in sorted(report["registry_counts"].items()):
                print(f"  {registry}: {count}")
        
        print("=" * 60 + "\n")
    
    @staticmethod
    def _extract_registry(image: str) -> str:
        """Extract registry name from image string."""
        try:
            # Format: <registry>/<service>:<version>
            return image.split("/")[0]
        except (IndexError, AttributeError):
            return ""
