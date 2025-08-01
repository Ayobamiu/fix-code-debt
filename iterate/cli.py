"""
Command-line interface for the Iterate tool.
"""

import argparse
import sys
from typing import List
from .core.progress_reporter import ProgressType
from .utils.display import print_directory_contents
from .utils.monitoring import monitor_directory
from .integrations.repository_analyzer import RepositoryAnalyzer


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
    
    # Dependency analysis
    parser.add_argument("--analyze-deps", action="store_true", help="Analyze dependencies")
    parser.add_argument("--export-deps", help="Export dependencies to file")
    parser.add_argument("--impact", help="Show impact analysis for a specific file")
    
    # GitHub integration
    parser.add_argument("--github", action="store_true", help="Enable GitHub integration")
    parser.add_argument("--github-auth", action="store_true", help="Authenticate with GitHub")
    parser.add_argument("--github-oauth", action="store_true", help="Authenticate with GitHub using OAuth")
    parser.add_argument("--github-issues", action="store_true", help="Create GitHub issues for debt findings")
    parser.add_argument("--github-analysis", action="store_true", help="Perform full GitHub repository analysis")
    
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
        elif args.analyze_deps or args.export_deps or args.impact:
            # Dependency analysis mode
            from .core.error_handler import ErrorHandler
            from .core.progress_reporter import ProgressReporter
            from .utils.dependency_analyzer import DependencyAnalyzer
            
            error_handler = ErrorHandler()
            progress_reporter = ProgressReporter(progress_type)
            
            analyzer = DependencyAnalyzer(
                directory=args.directory,
                error_handler=error_handler,
                progress_reporter=progress_reporter
            )
            
            if args.analyze_deps:
                print(f"🔍 Analyzing dependencies in: {args.directory}")
                
                # First, do a file discovery scan to show accurate counts
                file_finder = analyzer.file_finder
                discovery_result = file_finder.find_files_and_folders(
                    args.directory, 
                    max_depth=args.max_depth
                )
                total_files_found = len(discovery_result.get('files', []))
                total_dirs_found = len(discovery_result.get('folders', []))
                
                print(f"📁 File Discovery: {total_files_found} files, {total_dirs_found} directories")
                
                # Now do dependency analysis
                dependencies, all_files = analyzer.analyze_codebase()
                analyzer.print_analysis_summary(dependencies, all_files)
                
                if args.export_deps:
                    analyzer.export_analysis(dependencies, args.export_deps)
                    
            elif args.impact:
                print(f"🎯 Impact analysis for: {args.impact}")
                impacted_files = analyzer.get_impact_analysis(args.impact)
                if impacted_files:
                    print(f"Files that would be impacted:")
                    for file_path in impacted_files:
                        print(f"  - {file_path}")
                else:
                    print("No files would be impacted by changes to this file.")
        
        # GitHub integration
        elif args.github_auth:
            print("🔐 Setting up GitHub authentication...")
            from .integrations.github_client import GitHubClient
            
            github_client = GitHubClient()
            if github_client.authenticate():
                print("✅ GitHub authentication successful!")
            else:
                print("❌ GitHub authentication failed.")
                sys.exit(1)
        
        elif args.github_oauth:
            print("🔐 Setting up GitHub OAuth authentication...")
            from .integrations.simple_oauth import SimpleGitHubOAuthClient
            
            oauth_client = SimpleGitHubOAuthClient()
            if oauth_client.authenticate():
                print("✅ GitHub OAuth authentication successful!")
            else:
                print("❌ GitHub OAuth authentication failed.")
                sys.exit(1)
        
        elif args.github_analysis:
            print("🔍 Starting GitHub repository analysis...")
            from .core.error_handler import ErrorHandler
            
            error_handler = ErrorHandler()
            analyzer = RepositoryAnalyzer(error_handler=error_handler)
            
            analysis = analyzer.analyze_repository(args.directory)
            analyzer.print_analysis_summary(analysis)
            
            if args.github_issues and analysis.debt_score > 0.6:
                print("\n📝 Creating GitHub issues for debt findings...")
                issues_created = analyzer.create_debt_issues(analysis)
                if issues_created:
                    print(f"✅ Created {len(issues_created)} GitHub issues")
                else:
                    print("⚠️  No issues created (debt score too low or authentication failed)")
        
        elif args.github_issues:
            print("📝 Creating GitHub issues for debt findings...")
            from .core.error_handler import ErrorHandler
            from .core.progress_reporter import ProgressReporter
            from .utils.dependency_analyzer import DependencyAnalyzer
            
            error_handler = ErrorHandler()
            progress_reporter = ProgressReporter(progress_type)
            
            analyzer = DependencyAnalyzer(
                directory=args.directory,
                error_handler=error_handler,
                progress_reporter=progress_reporter
            )
            
            dependencies, all_files = analyzer.analyze_codebase()
            
            # Create repository analyzer for GitHub integration
            repo_analyzer = RepositoryAnalyzer(error_handler=error_handler)
            analysis = repo_analyzer._analyze_local_only(args.directory)
            analysis.dependencies = dependencies
            
            issues_created = repo_analyzer.create_debt_issues(analysis)
            if issues_created:
                print(f"✅ Created {len(issues_created)} GitHub issues")
            else:
                print("⚠️  No issues created (debt score too low or authentication failed)")
                    
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