"""
Display and output formatting utilities.
"""

import time
from typing import List, Dict

from ..core.file_finder import FileFinder


def print_directory_contents(directory_path: str, recursive: bool = True, max_depth: int = None, ignore_patterns: List[str] = None, use_cache: bool = True):
    """
    Print all files and folders in a directory in a readable format.
    
    Args:
        directory_path (str): Path to the directory
        recursive (bool): Whether to search subdirectories recursively
        max_depth (int): Maximum depth for recursive scanning
        ignore_patterns (List[str]): Custom ignore patterns
        use_cache (bool): Whether to use caching
    """
    start_time = time.time()
    
    finder = FileFinder(use_cache=use_cache)
    result = finder.find_files_and_folders(directory_path, recursive, max_depth, ignore_patterns)
    
    end_time = time.time()
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # Determine cache status
    if result.get("cached", False):
        if result.get("incremental", False):
            cache_status = "🔄 Incremental update"
            changes = []
            if result.get("new_files", 0) > 0:
                changes.append(f"+{result['new_files']} new")
            if result.get("deleted_files", 0) > 0:
                changes.append(f"-{result['deleted_files']} deleted")
            if result.get("changed_files", 0) > 0:
                changes.append(f"~{result['changed_files']} changed")
            if changes:
                cache_status += f" ({', '.join(changes)})"
        else:
            cache_status = "🔄 Cached (no changes)"
    else:
        cache_status = "⚡ Fresh scan"
    
    print(f"📁 Directory: {result['directory']}")
    print(f"🔍 Search: {'Recursive' if result['recursive'] else 'Top-level only'}")
    if max_depth is not None:
        print(f"📏 Max Depth: {max_depth}")
    print(f"{cache_status} | Time: {end_time - start_time:.4f}s")
    print(f"📊 Files: {result['total_files']:,}")
    print(f"📁 Folders: {result['total_folders']:,}")
    if result.get('ignored_count', 0) > 0:
        print(f"🚫 Ignored: {result['ignored_count']:,}")
    print(f"🚀 Speed: {result['total_files'] / (end_time - start_time):,.0f} files/second")
    print("=" * 50)
    
    if result['total_files'] > 0:
        print(f"\n📄 Files (showing first 20):")
        for file in sorted(result['files'])[:20]:
            print(f"  📄 {file}")
        if len(result['files']) > 20:
            print(f"  ... and {len(result['files']) - 20} more files")
    
    if result['total_folders'] > 0:
        print(f"\n📁 Folders (showing first 20):")
        for folder in sorted(result['folders'])[:20]:
            print(f"  📁 {folder}")
        if len(result['folders']) > 20:
            print(f"  ... and {len(result['folders']) - 20} more folders")