"""
Core functionality for file discovery and analysis.
"""

from .file_finder import FileFinder
from .cache_manager import CacheManager
from .ignore_patterns import IgnorePatterns

__all__ = ["FileFinder", "CacheManager", "IgnorePatterns"]