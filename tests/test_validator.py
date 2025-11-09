"""Tests for core validation logic."""

import pytest
from pathlib import Path
import tempfile
import yaml

from config_guardian.validate import ConfigValidator
from config_guardian.models import ValidationResult


class TestConfigValidator:
    """Test ConfigValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ConfigValidator()
    
    @pytest.fixture
    def temp_yaml_file(self, tmp_path):
        """Create a temporary YAML file."""
        def _create(content: dict) -> Path:
            file_path = tmp_path / "test_config.yaml"
            with open(file_path, "w") as f:
                yaml.dump(content, f)
            return file_path
        return _create
    
    def test_valid_config(self, validator, temp_yaml_file):
        """Test validation of a valid configuration."""
        config = {
            "service": "test-service",
            "image": "docker.io/app:v1.0.0",
            "replicas": 5
        }
        file_path = temp_yaml_file(config)
        
        result = validator.validate_file(file_path)
        
        assert result.is_valid
        assert len(result.issues) == 0
    
    def test_missing_required_keys(self, validator, temp_yaml_file):
        """Test detection of missing required keys."""
        config = {
            "service": "test-service",
            "image": "docker.io/app:v1.0.0"
            # Missing replicas
        }
        file_path = temp_yaml_file(config)
        
        result = validator.validate_file(file_path)
        
        assert not result.is_valid
        assert any("replicas" in issue.message.lower() for issue in result.issues)
    
    def test_invalid_replicas_range(self, validator, temp_yaml_file):
        """Test replicas out of valid range."""
        config = {
            "service": "test-service",
            "image": "docker.io/app:v1.0.0",
            "replicas": 100  # Out of range
        }
        file_path = temp_yaml_file(config)
        
        result = validator.validate_file(file_path)
        
        assert not result.is_valid
        assert any("between 1 and 50" in issue.message for issue in result.issues)
    
    def test_invalid_replicas_type(self, validator, temp_yaml_file):
        """Test replicas with wrong type."""
        config = {
            "service": "test-service",
            "image": "docker.io/app:v1.0.0",
            "replicas": "three"  # String instead of int
        }
        file_path = temp_yaml_file(config)
        
        result = validator.validate_file(file_path)
        
        assert not result.is_valid
        assert any("integer" in issue.message.lower() for issue in result.issues)
    
    def test_invalid_image_format(self, validator, temp_yaml_file):
        """Test image with invalid format."""
        invalid_images = [
            "just-a-name",
            "docker.io/app",  # Missing tag
            "app:v1.0.0",  # Missing registry
            "docker.io:v1.0.0",  # Missing service
        ]
        
        for invalid_image in invalid_images:
            config = {
                "service": "test-service",
                "image": invalid_image,
                "replicas": 3
            }
            file_path = temp_yaml_file(config)
            result = validator.validate_file(file_path)
            
            assert not result.is_valid, f"Should fail for image: {invalid_image}"
            assert any("pattern" in issue.message.lower() for issue in result.issues)
    
    def test_env_lowercase_keys(self, validator, temp_yaml_file):
        """Test env with lowercase keys."""
        config = {
            "service": "test-service",
            "image": "docker.io/app:v1.0.0",
            "replicas": 3,
            "env": {
                "UPPER_CASE": "valid",
                "lower_case": "invalid",
                "MixedCase": "invalid"
            }
        }
        file_path = temp_yaml_file(config)
        
        result = validator.validate_file(file_path)
        
        assert not result.is_valid
        assert any("uppercase" in issue.message.lower() for issue in result.issues)
    
    def test_env_valid_uppercase(self, validator, temp_yaml_file):
        """Test env with valid uppercase keys."""
        config = {
            "service": "test-service",
            "image": "docker.io/app:v1.0.0",
            "replicas": 3,
            "env": {
                "DATABASE_URL": "postgres://localhost",
                "PORT": "8080",
                "ENABLED": True
            }
        }
        file_path = temp_yaml_file(config)
        
        result = validator.validate_file(file_path)
        
        assert result.is_valid
        assert len(result.issues) == 0
    
    def test_malformed_yaml(self, validator, tmp_path):
        """Test handling of malformed YAML."""
        file_path = tmp_path / "malformed.yaml"
        with open(file_path, "w") as f:
            f.write("invalid: yaml: content:\n  - broken")
        
        result = validator.validate_file(file_path)
        
        assert not result.is_valid
        assert any("yaml" in issue.field.lower() for issue in result.issues)
