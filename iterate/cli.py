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
    
    # Dependency analysis
    parser.add_argument("--analyze-deps", action="store_true", help="Analyze dependencies")
    parser.add_argument("--export-deps", help="Export dependencies to file")
    parser.add_argument("--impact", help="Show impact analysis for a specific file")
    
    # GitHub MCP integration
    parser.add_argument("--github", action="store_true", help="Enable GitHub MCP integration")
    parser.add_argument("--github-mcp", action="store_true", help="Use GitHub MCP for enhanced analysis")
    parser.add_argument("--github-issues", action="store_true", help="Create GitHub issues for debt findings")
    parser.add_argument("--github-analysis", action="store_true", help="Perform full GitHub repository analysis")
    parser.add_argument("--github-pr-comments", action="store_true", help="Comment on high debt pull requests")
    
    parser.add_argument("--ai-refactor", action="store_true", help="Generate AI-powered refactoring suggestions")
    parser.add_argument("--ai-improve", action="store_true", help="Generate improved code versions")
    parser.add_argument("--ai-tests", action="store_true", help="Generate AI-powered test suggestions")
    parser.add_argument("--ai-test-files", action="store_true", help="Generate complete test files")
    parser.add_argument("--ai-docs", action="store_true", help="Generate AI-powered documentation suggestions")
    parser.add_argument("--ai-best-practices", action="store_true", help="Generate best practice recommendations")
    parser.add_argument("--ai-true", action="store_true", help="Use true AI (OpenAI) for code generation")
    parser.add_argument("--openai-key", help="OpenAI API key for AI generation")
    parser.add_argument("--save-ai", action="store_true", help="Save AI-generated code to files")
    parser.add_argument("--ai-output-dir", default="ai_generated", help="Directory to save AI-generated code")
    
    # In-place AI application modes
    parser.add_argument("--ai-apply", action="store_true", help="Apply AI changes directly to files (automatic mode)")
    parser.add_argument("--ai-interactive", action="store_true", help="Apply AI changes interactively with confirmation")
    parser.add_argument("--ai-preview", action="store_true", help="Preview AI changes without applying them")
    parser.add_argument("--no-pr", action="store_true", help="Don't create PR in automatic mode")
    parser.add_argument("--no-git", action="store_true", help="Disable Git integration")
    
    # Intelligent codebase features
    parser.add_argument("--intelligence", action="store_true", help="Initialize codebase intelligence system")
    parser.add_argument("--intelligent-refactor", help="Generate intelligent refactoring suggestions")
    parser.add_argument("--find-duplicates", action="store_true", help="Find duplicate code patterns")
    parser.add_argument("--cross-file-refactor", action="store_true", help="Suggest cross-file refactoring opportunities")
    parser.add_argument("--context-aware-tests", help="Generate context-aware tests for a file")
    parser.add_argument("--codebase-insights", action="store_true", help="Get insights about the codebase")
    parser.add_argument("--update-context", help="Update context for a specific file")
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
        
        # GitHub MCP integration
        elif args.github_analysis or args.github_issues or args.github_pr_comments:
            print("🔍 Starting GitHub MCP repository analysis...")
            from .core.error_handler import ErrorHandler
            from .integrations.mcp_repository_analyzer import MCPRepositoryAnalyzer
            
            error_handler = ErrorHandler()
            analyzer = MCPRepositoryAnalyzer(error_handler=error_handler)
            
            analysis = analyzer.analyze_repository(args.directory)
            analyzer.print_analysis_summary(analysis)
            
            if args.github_issues and analysis.debt_score > 0.5:
                print("\n📝 Creating GitHub issues for debt findings...")
                issues_created = analyzer.create_debt_issues(analysis)
                if issues_created:
                    print(f"✅ Created {len(issues_created)} GitHub issues")
                else:
                    print("⚠️  No issues created (debt score too low or authentication failed)")
            
            if args.github_pr_comments:
                print("\n💬 Commenting on high debt pull requests...")
                commented_count = analyzer.comment_on_high_debt_prs(analysis)
                if commented_count > 0:
                    print(f"✅ Commented on {commented_count} pull requests")
                else:
                    print("ℹ️  No high debt pull requests found")
        # Intelligent codebase features
        elif args.intelligence or args.intelligent_refactor or args.find_duplicates or args.cross_file_refactor or args.context_aware_tests or args.codebase_insights or args.update_context:
            print("🧠 Initializing Intelligent Codebase Features...")
            from .core.intelligent_ai_generator import IntelligentAIGenerator
            from .core.error_handler import ErrorHandler
            
            error_handler = ErrorHandler()
            intelligent_generator = IntelligentAIGenerator(error_handler=error_handler)
            
            # Initialize codebase intelligence
            if args.intelligence:
                print("🔍 Initializing codebase intelligence system...")
                success = intelligent_generator.initialize_codebase(args.directory)
                if success:
                    print("✅ Codebase intelligence initialized successfully!")
                else:
                    print("❌ Failed to initialize codebase intelligence")
                    return
            
            # Generate intelligent refactoring suggestions
            if args.intelligent_refactor:
                print(f"🤖 Generating intelligent refactoring suggestions for: {args.intelligent_refactor}")
                suggestions = intelligent_generator.generate_intelligent_refactoring(args.intelligent_refactor)
                if suggestions:
                    print(f"🎯 Found {len(suggestions)} intelligent suggestions:")
                    for i, suggestion in enumerate(suggestions, 1):
                        print(f"{i}. {suggestion.suggestion.file_path} - {suggestion.suggestion.function_name}")
                        print(f"   Confidence: {suggestion.confidence_score:.1%}")
                        print(f"   Reasoning: {suggestion.reasoning}")
                        if suggestion.cross_file_impact:
                            print("   Cross-file impact: " + ", ".join(suggestion.cross_file_impact))
                else:
                    print("ℹ️  No intelligent refactoring suggestions found")
            
            # Find duplicate code
            if args.find_duplicates:
                print("🔍 Finding duplicate code patterns...")
                duplicates = intelligent_generator.find_duplicate_code()
                if duplicates:
                    print(f"🎯 Found {len(duplicates)} duplicate patterns:")
                    for duplicate in duplicates:
                        print("📁 Function: " + duplicate.get("function_name", ""))
                        print("   Occurrences: " + str(duplicate.get("occurrences", 0)))
                        print("   Files: " + ", ".join(duplicate.get("files", [])))
                        print("   Suggestion: " + duplicate.get("suggestion", ""))
                else:
                    print("ℹ️  No duplicate code patterns found")
            
            # Cross-file refactoring suggestions
            if args.cross_file_refactor:
                print("🔍 Analyzing cross-file refactoring opportunities...")
                suggestions = intelligent_generator.suggest_cross_file_refactoring()
                if suggestions:
                    print(f"🎯 Found {len(suggestions)} cross-file opportunities:")
                    for suggestion in suggestions:
                        print("📁 Pattern: " + suggestion.get("pattern", ""))
                        print("   Files affected: " + str(len(suggestion.get("files_affected", []))))
                        print("   Suggestion: " + suggestion.get("suggestion", ""))
                else:
                    print("ℹ️  No cross-file refactoring opportunities found")
            
            # Generate context-aware tests
            if args.context_aware_tests:
                print(f"🧪 Generating context-aware tests for: {args.context_aware_tests}")
                test_code = intelligent_generator.generate_context_aware_tests(args.context_aware_tests)
                if test_code:
                    print("✅ Generated context-aware test code:")
                    print("```python")
                    print(test_code)
                    print("```")
                else:
                    print("ℹ️  No context-aware tests generated")
            
            # Get codebase insights
            if args.codebase_insights:
                print("📊 Getting codebase insights...")
                insights = intelligent_generator.get_codebase_insights()
                if insights:
                    summary = insights.get("summary", {})
                    print("📁 Total chunks: " + str(summary.get("total_chunks", 0)))
                    print("📄 Unique files: " + str(summary.get("unique_files", 0)))
                    print("🔧 Functions: " + str(summary.get("functions", 0)))
                    print("🏗️  Classes: " + str(summary.get("classes", 0)))
                    print("📦 Imports: " + str(summary.get("imports", 0)))
                    print("📊 Average complexity: " + str(round(summary.get("average_complexity", 0), 1)))
                    print("⚠️  High complexity functions: " + str(summary.get("high_complexity_functions", 0)))
                    print("🔄 Duplicates found: " + str(insights.get("total_duplicates", 0)))
                    print("🎯 Cross-file opportunities: " + str(insights.get("total_opportunities", 0)))
                else:
                    print("ℹ️  No insights available")
            
            # Update context for a specific file
            if args.update_context:
                print(f"🔄 Updating context for: {args.update_context}")
                success = intelligent_generator.update_context_for_file(args.update_context)
                if success:
                    print("✅ Context updated successfully!")
                else:
                    print("ℹ️  No changes detected or update failed")
                    
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