"""Plugin B: Check that env does not contain keys with 'SECRET' substring."""

from typing import Dict, Any, List
from config_guardian.models import ValidationIssue


def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate that env keys do not contain 'SECRET' substring.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of validation issues
    """
    issues = []
    
    env = config.get("env")
    if env and isinstance(env, dict):
        for key in env.keys():
            if isinstance(key, str) and "SECRET" in key.upper():
                issues.append(
                    ValidationIssue(
                        field="env",
                        message=f"Environment key '{key}' contains 'SECRET' - secrets should be managed externally",
                        severity="warning"
                    )
                )
    
    return issues
