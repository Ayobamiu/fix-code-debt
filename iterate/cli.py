"""
Command line interface for Iterate.
"""

import argparse
import sys
from typing import List

from .core.file_finder import FileFinder
from .utils.display import print_directory_contents
from .utils.monitoring import monitor_directory


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Iterate - Intelligent file discovery tool")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--recursive", "-r", action="store_true", default=True, 
                       help="Scan subdirectories (default: True)")
    parser.add_argument("--no-recursive", action="store_true", 
                       help="Only scan top-level directory")
    parser.add_argument("--monitor", "-m", action="store_true", 
                       help="Monitor directory for changes")
    parser.add_argument("--duration", "-d", type=int, default=30, 
                       help="Monitoring duration in seconds (default: 30)")
    parser.add_argument("--max-depth", type=int, 
                       help="Maximum depth for recursive scanning")
    parser.add_argument("--no-ignore", action="store_true",
                       help="Don't use ignore patterns")
    parser.add_argument("--ignore", nargs="+",
                       help="Additional ignore patterns")
    parser.add_argument("--no-cache", action="store_true",
                       help="Don't use caching")
    
    args = parser.parse_args()
    
    # Handle recursive flag
    recursive = args.recursive and not args.no_recursive
    
    # Handle ignore patterns
    ignore_patterns = None if args.no_ignore else (args.ignore or [])
    
    # Handle caching
    use_cache = not args.no_cache
    
    if args.monitor:
        monitor_directory(args.directory, args.duration)
    else:
        print_directory_contents(
            args.directory, 
            recursive, 
            args.max_depth, 
            ignore_patterns, 
            use_cache
        )


if __name__ == "__main__":
    main()