"""
Display utilities for file discovery results.
"""

import time
from typing import List, Optional
from ..core.file_finder import FileFinder
from ..core.progress_reporter import ProgressType


def print_directory_contents(directory_path: str, recursive: bool = True, 
                           max_depth: Optional[int] = None, ignore_patterns: Optional[List[str]] = None, 
                           use_cache: bool = True, progress_type: ProgressType = ProgressType.SIMPLE,
                           show_errors: bool = True):
    """
    Print directory contents with comprehensive error handling and progress reporting.
    
    Args:
        directory_path: Path to the directory to scan
        recursive: Whether to scan subdirectories
        max_depth: Maximum depth for recursive scanning
        ignore_patterns: Custom ignore patterns
        use_cache: Whether to use caching
        progress_type: Type of progress reporting
        show_errors: Whether to display error information
    """
    start_time = time.time()
    
    # Create components
    from ..core.error_handler import ErrorHandler
    from ..core.progress_reporter import ProgressReporter
    from ..core.cache_manager import SmartCacheManager
    from ..core.ignore_patterns import IgnorePatterns
    from ..core.config_manager import ConfigManager
    
    error_handler = ErrorHandler()
    progress_reporter = ProgressReporter(progress_type=progress_type)
    cache_manager = SmartCacheManager(".iterate_cache") if use_cache else None
    ignore_handler = IgnorePatterns(ignore_patterns, error_handler)
    config_manager = ConfigManager(error_handler)
    
    # Create file finder with specified options
    finder = FileFinder(
        error_handler=error_handler,
        progress_reporter=progress_reporter,
        cache_manager=cache_manager,
        ignore_patterns=ignore_handler,
        config_manager=config_manager
    )
    
    # Perform the scan
    result = finder.find_files_and_folders(directory_path, recursive, max_depth, ignore_patterns)
    
    # Display results
    _display_scan_results(result, start_time, show_errors)


def _display_scan_results(result: dict, start_time: float, show_errors: bool):
    """Display scan results in a formatted way."""
    print("\n" + "="*60)
    print("SCAN RESULTS")
    print("="*60)
    
    # Check for errors
    if "error" in result:
        print(f"❌ ERROR: {result['error']}")
        return
    
    # Basic statistics
    print(f"📁 Directory: {result.get('directory', 'N/A')}")
    print(f"📊 Files found: {result['total_files']}")
    print(f"📂 Directories found: {result['total_folders']}")
    print(f"⏱️  Scan time: {result.get('scan_time', 0):.2f} seconds")
    
    # Cache information
    if result.get('cached', False):
        if result.get('incremental', False):
            print("🔄 Cache: Incremental update")
            if 'changed_files' in result:
                print(f"   📝 Changed files: {result['changed_files']}")
            if 'new_files' in result:
                print(f"   ➕ New files: {result['new_files']}")
            if 'deleted_files' in result:
                print(f"   ➖ Deleted files: {result['deleted_files']}")
        else:
            print("💾 Cache: Fresh result")
    else:
        print("🆕 Cache: New scan")
    
    # Error summary
    if show_errors and 'errors' in result:
        errors = result['errors']
        if errors.get('total_errors', 0) > 0:
            print(f"\n⚠️  Errors encountered: {errors['total_errors']}")
            for error_type, count in errors.get('error_types', {}).items():
                print(f"   • {error_type}: {count}")
    
    # Display file type statistics if available
    if 'file_stats' in result:
        stats = result['file_stats']
        print(f"📊 File Type Analysis:")
        print(f"   💻 Code files: {len(stats['code_files'])}")
        print(f"   ⚙️  Config files: {len(stats['config_files'])}")
        print(f"   🧪 Test files: {len(stats['test_files'])}")
        print(f"   📄 Other files: {len(stats['other_files'])}")
        
        # Show language breakdown for code files
        if stats['by_language']:
            print(f"   🌐 Languages detected:")
            for lang, count in sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True):
                if count > 0 and lang != 'unknown':
                    print(f"      {lang}: {count} files")
    
    # Display configuration information if available
    if 'config_used' in result:
        config = result['config_used']
        print(f"⚙️  Configuration:")
        scan_config = config.get('scan', {})
        print(f"   🔍 Scan: recursive={scan_config.get('recursive', True)}, max_depth={scan_config.get('max_depth', -1)}")
        
        cache_config = config.get('cache', {})
        print(f"   💾 Cache: enabled={cache_config.get('enabled', True)}")
        
        file_types_config = config.get('file_types', {})
        enabled_langs = file_types_config.get('enabled_languages', [])
        if enabled_langs:
            print(f"   📝 Languages: {', '.join(enabled_langs[:5])}{'...' if len(enabled_langs) > 5 else ''}")
    
    # File listing (if not too many)
    if result['total_files'] <= 50:
        print(f"\n📄 Files ({result['total_files']}):")
        for file_path in result.get('files', [])[:20]:  # Show first 20
            print(f"   {file_path}")
        if result['total_files'] > 20:
            print(f"   ... and {result['total_files'] - 20} more files")
    
    # Directory listing (if not too many)
    if result['total_folders'] <= 20:
        print(f"\n📂 Directories ({result['total_folders']}):")
        for dir_path in result.get('folders', [])[:10]:  # Show first 10
            print(f"   {dir_path}")
        if result['total_folders'] > 10:
            print(f"   ... and {result['total_folders'] - 10} more directories")
    
    print("="*60)