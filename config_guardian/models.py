"""Data models for validation results."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    
    field: str
    message: str
    severity: str = "error"  # error or warning


@dataclass
class ValidationResult:
    """Result of validating a single configuration file."""
    
    file_path: str
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    
    def add_issue(self, field: str, message: str, severity: str = "error") -> None:
        """Add a validation issue."""
        self.issues.append(ValidationIssue(field=field, message=message, severity=severity))
        if severity == "error":
            self.is_valid = False
