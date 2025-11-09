"""Plugin A: Check that image tag is not 'latest'."""

from typing import Dict, Any, List
from config_guardian.models import ValidationIssue


def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate that image tag is not 'latest'.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        List of validation issues
    """
    issues = []
    
    image = config.get("image")
    if image and isinstance(image, str):
        # Extract tag from image (format: registry/service:tag)
        if ":" in image:
            tag = image.split(":")[-1]
            if tag.lower() == "latest":
                issues.append(
                    ValidationIssue(
                        field="image",
                        message="Image tag should not be 'latest' - use specific version tags",
                        severity="error"
                    )
                )
    
    return issues
