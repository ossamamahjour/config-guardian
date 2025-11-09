"""Core configuration validation logic."""

import logging
import re
from pathlib import Path
from typing import Dict, Any

import yaml

from config_guardian.models import ValidationResult

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration files against required rules."""
    
    REQUIRED_KEYS = {"service", "image", "replicas"}
    IMAGE_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+$")
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Validate a single configuration file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            ValidationResult with issues found
        """
        result = ValidationResult(file_path=str(file_path), is_valid=True)
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                result.add_issue("root", "Configuration must be a YAML dictionary")
                return result
            
            result.config = config
            self._validate_config(config, result)
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            result.add_issue("yaml", f"Invalid YAML syntax: {str(e)}")
        except IOError as e:
            logger.error(f"I/O error reading {file_path}: {e}")
            result.add_issue("io", f"Failed to read file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error validating {file_path}: {e}")
            result.add_issue("unknown", f"Unexpected error: {str(e)}")
        
        return result
    
    def _validate_config(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate configuration dictionary against rules."""
        # Check required keys
        missing_keys = self.REQUIRED_KEYS - config.keys()
        if missing_keys:
            result.add_issue(
                "required_keys",
                f"Missing required keys: {', '.join(sorted(missing_keys))}"
            )
        
        # Validate replicas
        if "replicas" in config:
            self._validate_replicas(config["replicas"], result)
        
        # Validate image
        if "image" in config:
            self._validate_image(config["image"], result)
        
        # Validate env
        if "env" in config:
            self._validate_env(config["env"], result)
    
    def _validate_replicas(self, replicas: Any, result: ValidationResult) -> None:
        """Validate replicas field."""
        if not isinstance(replicas, int):
            result.add_issue("replicas", "replicas must be an integer")
            return
        
        if replicas < 1 or replicas > 50:
            result.add_issue("replicas", "replicas must be between 1 and 50")
    
    def _validate_image(self, image: Any, result: ValidationResult) -> None:
        """Validate image field format."""
        if not isinstance(image, str):
            result.add_issue("image", "image must be a string")
            return
        
        if not self.IMAGE_PATTERN.match(image):
            result.add_issue(
                "image",
                "image must follow pattern <registry>/<service>:<version>"
            )
    
    def _validate_env(self, env: Any, result: ValidationResult) -> None:
        """Validate env field."""
        if not isinstance(env, dict):
            result.add_issue("env", "env must be a dictionary of key-value pairs")
            return
        
        for key, value in env.items():
            if not isinstance(key, str):
                result.add_issue("env", f"env key must be string, got {type(key).__name__}")
                continue
            
            if key != key.upper():
                result.add_issue("env", f"env key '{key}' must be uppercase")
            
            if not isinstance(value, (str, int, float, bool)):
                result.add_issue(
                    "env",
                    f"env value for '{key}' must be a simple type (string, number, or boolean)"
                )
