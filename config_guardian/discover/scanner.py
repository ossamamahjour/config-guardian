"""YAML file discovery functionality."""

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def find_yaml_files(root_dir: str) -> List[Path]:
    """
    Recursively find all .yaml and .yml files under the given directory.
    
    Args:
        root_dir: Root directory to scan
        
    Returns:
        List of Path objects for all YAML files found
    """
    root_path = Path(root_dir).resolve()
    
    if not root_path.exists():
        logger.error(f"Root directory does not exist: {root_dir}")
        return []
    
    if not root_path.is_dir():
        logger.error(f"Root path is not a directory: {root_dir}")
        return []
    
    yaml_files = []
    
    # Use rglob for efficient recursive search
    for pattern in ("*.yaml", "*.yml"):
        yaml_files.extend(root_path.rglob(pattern))
    
    logger.info(f"Found {len(yaml_files)} YAML files under {root_dir}")
    return sorted(yaml_files)
