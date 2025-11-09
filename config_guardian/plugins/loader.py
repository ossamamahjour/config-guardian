"""Plugin discovery and loading."""

import importlib.util
import logging
from pathlib import Path
from typing import List, Callable, Dict, Any

from config_guardian.models import ValidationIssue

logger = logging.getLogger(__name__)


class PluginLoader:
    """Dynamically load and execute validation plugins."""
    
    def __init__(self, plugin_dir: str):
        """
        Initialize plugin loader.
        
        Args:
            plugin_dir: Directory containing plugin Python files
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugins: List[Callable] = []
        self._load_plugins()
    
    def _load_plugins(self) -> None:
        """Load all plugins from the plugin directory."""
        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {self.plugin_dir}")
            return
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file.name}: {e}")
    
    def _load_plugin(self, plugin_file: Path) -> None:
        """Load a single plugin file."""
        module_name = f"plugin_{plugin_file.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if spec is None or spec.loader is None:
            logger.error(f"Failed to load plugin spec for {plugin_file}")
            return
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "run_validations"):
            self.plugins.append(module.run_validations)
            logger.info(f"Loaded plugin: {plugin_file.name}")
        else:
            logger.warning(
                f"Plugin {plugin_file.name} does not implement run_validations()"
            )
    
    def run_plugins(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Run all loaded plugins on a configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of validation issues from all plugins
        """
        issues = []
        
        for plugin in self.plugins:
            try:
                plugin_issues = plugin(config)
                if plugin_issues:
                    issues.extend(plugin_issues)
            except Exception as e:
                logger.error(f"Plugin execution error: {e}")
                issues.append(
                    ValidationIssue(
                        field="plugin",
                        message=f"Plugin error: {str(e)}",
                        severity="error"
                    )
                )
        
        return issues
