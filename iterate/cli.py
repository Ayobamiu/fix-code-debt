"""
Command-line interface for the Iterate tool.
"""

import argparse
import sys
from typing import List
from .core.progress_reporter import ProgressType
from .utils.display import print_directory_contents
from .utils.monitoring import monitor_directory


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Iterate - Intelligent file discovery tool with error handling and progress reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  iterate /path/to/directory                    # Basic scan
  iterate /path/to/directory --no-recursive     # Non-recursive scan
  iterate /path/to/directory --max-depth 3      # Limit depth
  iterate /path/to/directory --monitor          # Monitor for changes
  iterate /path/to/directory --progress verbose # Verbose progress
  iterate /path/to/directory --no-cache         # Disable caching
  iterate /path/to/directory --ignore "*.log"   # Custom ignore pattern
        """
    )
    
    # Required arguments
    parser.add_argument("directory", help="Directory to scan")
    
    # Scan options
    parser.add_argument("--recursive", action="store_true", default=True,
                       help="Scan subdirectories recursively (default)")
    parser.add_argument("--no-recursive", action="store_true", dest="no_recursive",
                       help="Do not scan subdirectories")
    parser.add_argument("--max-depth", type=int, help="Maximum depth for recursive scanning")
    
    # Monitoring
    parser.add_argument("--monitor", action="store_true", help="Monitor directory for changes")
    parser.add_argument("--duration", type=int, help="Duration to monitor in seconds")
    
    # Progress reporting
    parser.add_argument("--progress", choices=["silent", "simple", "detailed", "verbose"],
                       default="simple", help="Progress reporting type (default: simple)")
    
    # Caching
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    
    # Ignore patterns
    parser.add_argument("--no-ignore", action="store_true", help="Do not use ignore patterns")
    parser.add_argument("--ignore", action="append", help="Custom ignore pattern (can be used multiple times)")
    
    # Configuration management
    parser.add_argument("--init", action="store_true", help="Initialize project with default configuration")
    parser.add_argument("--create-config", choices=["json", "yaml"], help="Create default configuration file")
    parser.add_argument("--create-ignore", action="store_true", help="Create default .iterateignore file")
    
    # Error handling
    parser.add_argument("--show-errors", action="store_true", default=True,
                       help="Show error information (default)")
    parser.add_argument("--hide-errors", action="store_true", dest="hide_errors",
                       help="Hide error information")
    
    # Verbosity
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    
    args = parser.parse_args()
    
    # Process arguments
    recursive = args.recursive and not args.no_recursive
    ignore_patterns = None if args.no_ignore else (args.ignore or [])
    use_cache = not args.no_cache
    show_errors = args.show_errors and not args.hide_errors
    
    # Determine progress type
    if args.quiet:
        progress_type = ProgressType.SILENT
    elif args.verbose:
        progress_type = ProgressType.VERBOSE
    else:
        progress_type = ProgressType(args.progress)
    
    try:
        if args.init:
            # Initialize project with default configuration
            from .core.config_manager import ConfigManager
            from .core.error_handler import ErrorHandler
            
            error_handler = ErrorHandler()
            config_manager = ConfigManager(error_handler)
            
            print(f"🚀 Initializing Iterate project in: {args.directory}")
            
            # Create both config and ignore files
            try:
                config_file = config_manager.create_default_config(args.directory, "json")
                ignore_file = config_manager.create_ignore_file(args.directory)
                
                print(f"✅ Created configuration file: {config_file}")
                print(f"✅ Created ignore file: {ignore_file}")
                print("📝 Edit these files to customize your project settings")
                
            except Exception as e:
                print(f"❌ Error initializing project: {str(e)}")
                sys.exit(1)
                
        elif args.create_config:
            # Create configuration file
            from .core.config_manager import ConfigManager
            from .core.error_handler import ErrorHandler
            
            error_handler = ErrorHandler()
            config_manager = ConfigManager(error_handler)
            
            try:
                config_file = config_manager.create_default_config(args.directory, args.create_config)
                print(f"✅ Created configuration file: {config_file}")
                
            except Exception as e:
                print(f"❌ Error creating config file: {str(e)}")
                sys.exit(1)
                
        elif args.create_ignore:
            # Create ignore file
            from .core.config_manager import ConfigManager
            from .core.error_handler import ErrorHandler
            
            error_handler = ErrorHandler()
            config_manager = ConfigManager(error_handler)
            
            try:
                ignore_file = config_manager.create_ignore_file(args.directory)
                print(f"✅ Created ignore file: {ignore_file}")
                
            except Exception as e:
                print(f"❌ Error creating ignore file: {str(e)}")
                sys.exit(1)
                
        elif args.monitor:
            # Monitoring mode
            monitor_directory(args.directory, args.duration)
        else:
            # Scan mode
            print_directory_contents(
                directory_path=args.directory,
                recursive=recursive,
                max_depth=args.max_depth,
                ignore_patterns=ignore_patterns,
                use_cache=use_cache,
                progress_type=progress_type,
                show_errors=show_errors
            )
    
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()