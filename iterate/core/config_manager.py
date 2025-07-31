"""
Configuration management for Iterate tool.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .error_handler import ErrorHandler, ErrorSeverity


class ConfigManager:
    """Manages configuration for the Iterate tool."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        
        # Default configuration
        self.default_config = {
            "scan": {
                "recursive": True,
                "max_depth": 10,
                "follow_symlinks": False,
                "max_file_size": 10 * 1024 * 1024,  # 10MB
            },
            "ignore": {
                "patterns": [
                    ".git", ".svn", ".hg", ".bzr",
                    "node_modules", "__pycache__", ".pytest_cache",
                    "*.pyc", "*.pyo", "*.pyd", "*.so",
                    ".DS_Store", "Thumbs.db", "*.log",
                    ".iterate_cache", "*.cache"
                ],
                "files": [
                    ".gitignore", ".iterateignore"
                ]
            },
            "file_types": {
                "enabled_languages": ["python", "javascript", "typescript", "jsx", "tsx"],
                "include_config_files": True,
                "include_test_files": False,
                "include_documentation": False
            },
            "cache": {
                "enabled": True,
                "directory": ".iterate_cache",
                "max_age": 3600,  # 1 hour
                "incremental_updates": True
            },
            "progress": {
                "type": "simple",
                "update_interval": 0.5,
                "show_eta": True
            },
            "output": {
                "format": "text",
                "show_errors": True,
                "show_stats": True,
                "max_files_display": 50,
                "max_dirs_display": 20
            }
        }
        
        # Configuration file names to look for
        self.config_files = [
            ".iterate.json",
            ".iterate.yaml", 
            ".iterate.yml",
            "iterate.json",
            "iterate.yaml",
            "iterate.yml"
        ]
        
        # Ignore file names
        self.ignore_files = [
            ".iterateignore",
            ".iterate.ignore"
        ]
    
    def load_project_config(self, project_path: str) -> Dict[str, Any]:
        """
        Load configuration for a specific project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Merged configuration dictionary
        """
        try:
            project_path = Path(project_path).resolve()
            config = self.default_config.copy()
            
            # Look for configuration files in project directory
            config_file = self._find_config_file(project_path)
            if config_file:
                project_config = self._load_config_file(config_file)
                config = self._merge_configs(config, project_config)
            
            # Load ignore patterns from .iterateignore files
            ignore_patterns = self._load_ignore_patterns(project_path)
            if ignore_patterns:
                config["ignore"]["patterns"].extend(ignore_patterns)
            
            return config
            
        except Exception as e:
            self.error_handler.handle_error(
                f"Error loading project config for {project_path}: {str(e)}",
                ErrorSeverity.WARNING
            )
            return self.default_config.copy()
    
    def _find_config_file(self, project_path: Path) -> Optional[Path]:
        """Find configuration file in project directory."""
        for config_name in self.config_files:
            config_file = project_path / config_name
            if config_file.exists():
                return config_file
        return None
    
    def _load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            if config_file.suffix in ['.yaml', '.yml']:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:  # .json
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.error_handler.handle_error(
                f"Error loading config file {config_file}: {str(e)}",
                ErrorSeverity.WARNING
            )
            return {}
    
    def _load_ignore_patterns(self, project_path: Path) -> List[str]:
        """Load ignore patterns from .iterateignore files."""
        patterns = []
        
        for ignore_name in self.ignore_files:
            ignore_file = project_path / ignore_name
            if ignore_file.exists():
                try:
                    with open(ignore_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                patterns.append(line)
                except Exception as e:
                    self.error_handler.handle_error(
                        f"Error loading ignore file {ignore_file}: {str(e)}",
                        ErrorSeverity.WARNING
                    )
        
        return patterns
    
    def _merge_configs(self, base_config: Dict, override_config: Dict) -> Dict:
        """Recursively merge configuration dictionaries."""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def create_default_config(self, project_path: str, config_type: str = "json") -> Path:
        """
        Create a default configuration file for a project.
        
        Args:
            project_path: Path to the project directory
            config_type: Type of config file ("json" or "yaml")
            
        Returns:
            Path to the created config file
        """
        try:
            project_path = Path(project_path).resolve()
            
            if config_type == "yaml":
                config_file = project_path / ".iterate.yaml"
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(self.default_config, f, default_flow_style=False, indent=2)
            else:
                config_file = project_path / ".iterate.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(self.default_config, f, indent=2)
            
            return config_file
            
        except Exception as e:
            self.error_handler.handle_error(
                f"Error creating config file in {project_path}: {str(e)}",
                ErrorSeverity.ERROR
            )
            raise
    
    def create_ignore_file(self, project_path: str) -> Path:
        """
        Create a default .iterateignore file for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Path to the created ignore file
        """
        try:
            project_path = Path(project_path).resolve()
            ignore_file = project_path / ".iterateignore"
            
            default_ignores = [
                "# Iterate ignore patterns",
                "# Add patterns to ignore during file discovery",
                "",
                "# Version control",
                ".git/",
                ".svn/",
                ".hg/",
                "",
                "# Dependencies",
                "node_modules/",
                "__pycache__/",
                ".pytest_cache/",
                "",
                "# Build artifacts",
                "dist/",
                "build/",
                "*.pyc",
                "*.pyo",
                "",
                "# IDE and editor files",
                ".vscode/",
                ".idea/",
                "*.swp",
                "*.swo",
                "",
                "# OS files",
                ".DS_Store",
                "Thumbs.db",
                "",
                "# Logs and temporary files",
                "*.log",
                "*.tmp",
                "temp/",
                "tmp/"
            ]
            
            with open(ignore_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(default_ignores))
            
            return ignore_file
            
        except Exception as e:
            self.error_handler.handle_error(
                f"Error creating ignore file in {project_path}: {str(e)}",
                ErrorSeverity.ERROR
            )
            raise
    
    def get_scan_config(self, project_path: str) -> Dict[str, Any]:
        """Get scan-specific configuration."""
        config = self.load_project_config(project_path)
        return config.get("scan", {})
    
    def get_ignore_config(self, project_path: str) -> Dict[str, Any]:
        """Get ignore-specific configuration."""
        config = self.load_project_config(project_path)
        return config.get("ignore", {})
    
    def get_file_types_config(self, project_path: str) -> Dict[str, Any]:
        """Get file types configuration."""
        config = self.load_project_config(project_path)
        return config.get("file_types", {})
    
    def get_cache_config(self, project_path: str) -> Dict[str, Any]:
        """Get cache-specific configuration."""
        config = self.load_project_config(project_path)
        return config.get("cache", {})
    
    def get_progress_config(self, project_path: str) -> Dict[str, Any]:
        """Get progress-specific configuration."""
        config = self.load_project_config(project_path)
        return config.get("progress", {})
    
    def get_output_config(self, project_path: str) -> Dict[str, Any]:
        """Get output-specific configuration."""
        config = self.load_project_config(project_path)
        return config.get("output", {})
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate scan config
        scan_config = config.get("scan", {})
        if "max_depth" in scan_config and not isinstance(scan_config["max_depth"], int):
            errors.append("scan.max_depth must be an integer")
        if "max_file_size" in scan_config and not isinstance(scan_config["max_file_size"], (int, float)):
            errors.append("scan.max_file_size must be a number")
        
        # Validate file types config
        file_types_config = config.get("file_types", {})
        if "enabled_languages" in file_types_config and not isinstance(file_types_config["enabled_languages"], list):
            errors.append("file_types.enabled_languages must be a list")
        
        # Validate cache config
        cache_config = config.get("cache", {})
        if "max_age" in cache_config and not isinstance(cache_config["max_age"], (int, float)):
            errors.append("cache.max_age must be a number")
        
        return errors 