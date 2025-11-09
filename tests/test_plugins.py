"""Tests for plugin system."""

import pytest
from pathlib import Path
import tempfile

from config_guardian.plugins import PluginLoader
from config_guardian.models import ValidationIssue


class TestPluginLoader:
    """Test PluginLoader class."""
    
    @pytest.fixture
    def plugin_dir(self, tmp_path):
        """Create a temporary plugin directory."""
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        return plugin_dir
    
    def test_load_valid_plugin(self, plugin_dir):
        """Test loading a valid plugin."""
        plugin_code = '''
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    if config.get("test_field") == "invalid":
        issues.append(ValidationIssue("test_field", "Test error", "error"))
    return issues
'''
        plugin_file = plugin_dir / "test_plugin.py"
        plugin_file.write_text(plugin_code)
        
        loader = PluginLoader(str(plugin_dir))
        
        assert len(loader.plugins) == 1
    
    def test_plugin_execution(self, plugin_dir):
        """Test that loaded plugins execute correctly."""
        plugin_code = '''
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    if config.get("test_field") == "bad_value":
        issues.append(ValidationIssue("test_field", "Bad value detected", "error"))
    return issues
'''
        plugin_file = plugin_dir / "test_plugin.py"
        plugin_file.write_text(plugin_code)
        
        loader = PluginLoader(str(plugin_dir))
        
        # Test with invalid config
        config_invalid = {"test_field": "bad_value"}
        issues = loader.run_plugins(config_invalid)
        assert len(issues) == 1
        assert issues[0].message == "Bad value detected"
        
        # Test with valid config
        config_valid = {"test_field": "good_value"}
        issues = loader.run_plugins(config_valid)
        assert len(issues) == 0
    
    def test_skip_files_without_run_validations(self, plugin_dir):
        """Test that plugins without run_validations are skipped."""
        plugin_code = '''
def some_other_function():
    pass
'''
        plugin_file = plugin_dir / "invalid_plugin.py"
        plugin_file.write_text(plugin_code)
        
        loader = PluginLoader(str(plugin_dir))
        
        assert len(loader.plugins) == 0
    
    def test_multiple_plugins_execution(self, plugin_dir):
        """Test execution of multiple plugins."""
        plugin1_code = '''
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    if "field1" not in config:
        issues.append(ValidationIssue("field1", "Field1 missing", "error"))
    return issues
'''
        plugin2_code = '''
from typing import Dict, Any, List
from config_guardian.models import ValidationIssue

def run_validations(config: Dict[str, Any]) -> List[ValidationIssue]:
    issues = []
    if "field2" not in config:
        issues.append(ValidationIssue("field2", "Field2 missing", "warning"))
    return issues
'''
        (plugin_dir / "plugin1.py").write_text(plugin1_code)
        (plugin_dir / "plugin2.py").write_text(plugin2_code)
        
        loader = PluginLoader(str(plugin_dir))
        
        assert len(loader.plugins) == 2
        
        # Both plugins should detect issues
        config = {}
        issues = loader.run_plugins(config)
        assert len(issues) == 2
        assert any(i.field == "field1" for i in issues)
        assert any(i.field == "field2" for i in issues)
    
    def test_check_latest_tag_plugin(self):
        """Test the check_latest_tag plugin."""
        # Import the actual plugin
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "plugins"))
        
        try:
            from check_latest_tag import run_validations
            
            # Test with latest tag
            config_latest = {"image": "docker.io/app:latest"}
            issues = run_validations(config_latest)
            assert len(issues) == 1
            assert "latest" in issues[0].message.lower()
            
            # Test with specific version
            config_version = {"image": "docker.io/app:v1.2.3"}
            issues = run_validations(config_version)
            assert len(issues) == 0
        finally:
            sys.path.pop(0)
    
    def test_check_secret_env_plugin(self):
        """Test the check_secret_env plugin."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "plugins"))
        
        try:
            from check_secret_env import run_validations
            
            # Test with SECRET in env key
            config_secret = {
                "env": {
                    "API_SECRET": "mysecret",
                    "DATABASE_URL": "postgres://db"
                }
            }
            issues = run_validations(config_secret)
            assert len(issues) == 1
            assert "SECRET" in issues[0].message
            assert issues[0].severity == "warning"
            
            # Test without SECRET
            config_no_secret = {
                "env": {
                    "DATABASE_URL": "postgres://db",
                    "LOG_LEVEL": "INFO"
                }
            }
            issues = run_validations(config_no_secret)
            assert len(issues) == 0
        finally:
            sys.path.pop(0)
