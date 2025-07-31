"""
Iterate - Intelligent file discovery and analysis tool.
"""

__version__ = "0.1.0"
__author__ = "Iterate Team"

# Core components
from .core.file_finder import FileFinder
from .core.cache_manager import CacheManager
from .core.error_handler import ErrorHandler
from .core.progress_reporter import ProgressReporter
from .core.file_types import FileTypeDetector
from .core.config_manager import ConfigManager
from .core.dependency_mapper import DependencyMapper, Dependency, FileDependencies

# Utility components
from .utils.dependency_analyzer import DependencyAnalyzer

__all__ = [
    "FileFinder",
    "CacheManager", 
    "ErrorHandler",
    "ProgressReporter",
    "FileTypeDetector",
    "ConfigManager",
    "DependencyMapper",
    "Dependency",
    "FileDependencies",
    "DependencyAnalyzer"
]