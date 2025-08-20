"""
Command-line interface for the Iterate tool.
"""

import argparse
import sys
from typing import List
from .core.progress_reporter import ProgressType
from .core.duplicate_pr_manager import DuplicatePRManager
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
    
    # Duplicate PR management
    parser.add_argument("--create-pr", action="store_true", help="Create GitHub PR from duplicate findings")
    parser.add_argument("--group-duplicates", action="store_true", help="Group duplicates for PR creation")
    parser.add_argument("--max-per-group", type=int, default=3, help="Maximum duplicates per group (default: 3)")
    parser.add_argument("--auto-group", action="store_true", help="Automatically group duplicates without user input")
    parser.add_argument("--save-template", help="Save current duplicate grouping as a template")
    parser.add_argument("--load-template", help="Load a saved duplicate grouping template")
    parser.add_argument("--list-templates", action="store_true", help="List available duplicate grouping templates")
    parser.add_argument("--weekly-scan", action="store_true", help="Run weekly duplicate scan and group for PR creation")
    
    # Cache management
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cache data")
    parser.add_argument("--cache-info", action="store_true", help="Show detailed cache information")
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
                print("🔍 Analyzing dependencies...")
                dependencies = analyzer.analyze_dependencies()
                if dependencies:
                    print(f"✅ Found {len(dependencies)} dependency relationships")
                    for dep in dependencies[:10]:  # Show first 10
                        print(f"   📄 {dep.source} -> {dep.target}")
                    if len(dependencies) > 10:
                        print(f"   ... and {len(dependencies) - 10} more")
                else:
                    print("ℹ️  No dependencies found")
            
            if args.export_deps:
                print(f"📤 Exporting dependencies to: {args.export_deps}")
                success = analyzer.export_dependencies(args.export_deps)
                if success:
                    print("✅ Dependencies exported successfully")
                else:
                    print("❌ Failed to export dependencies")
            
            if args.impact:
                print(f"🎯 Analyzing impact for: {args.impact}")
                impact = analyzer.analyze_impact(args.impact)
                if impact:
                    print(f"📊 Impact analysis for {args.impact}:")
                    print(f"   📁 Files affected: {len(impact.affected_files)}")
                    print(f"   🔗 Dependencies: {len(impact.dependencies)}")
                    print(f"   ⚠️  Risk level: {impact.risk_level}")
                else:
                    print("ℹ️  No impact analysis available")
        
        elif args.list_templates or args.save_template or args.load_template or args.weekly_scan:
            # Template management mode
            from .core.duplicate_pr_manager import DuplicatePRManager
            from .core.error_handler import ErrorHandler
            
            error_handler = ErrorHandler()
            pr_manager = DuplicatePRManager(error_handler=error_handler)
            
            if args.list_templates:
                print("📚 Available duplicate grouping templates:")
                templates = pr_manager.list_templates()
                if templates:
                    for i, template in enumerate(templates, 1):
                        print(f"   {i}. {template}")
                else:
                    print("   No templates found")
            
            if args.save_template:
                print(f"💾 Saving duplicate grouping as template: {args.save_template}")
                print("   Use --find-duplicates --group-duplicates first to create a grouping")
            
            if args.load_template:
                print(f"📂 Loading template: {args.load_template}")
                print("   Use --create-pr to create a PR from this template")
            
            if args.weekly_scan:
                print("📅 Running weekly duplicate scan...")
                print("   Use --find-duplicates --group-duplicates to see the results")
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
        elif args.intelligence or args.intelligent_refactor or args.find_duplicates or args.cross_file_refactor or args.create_pr or args.group_duplicates or args.weekly_scan:
            print("🧠 Initializing Intelligent Codebase Features...")
            from .core.intelligent_ai_generator import IntelligentAIGenerator
            from .core.error_handler import ErrorHandler
            from .core.duplicate_pr_manager import DuplicatePRManager
            
            error_handler = ErrorHandler()
            intelligent_generator = IntelligentAIGenerator(error_handler=error_handler)
            
            # Initialize duplicate PR manager if needed
            duplicate_pr_manager = None
            if args.create_pr or args.group_duplicates or args.weekly_scan:
                duplicate_pr_manager = DuplicatePRManager(error_handler=error_handler)
            
            # Initialize codebase intelligence (always initialize for any intelligent feature)
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
                    print(f"🎯 Found {len(duplicates)} duplicate patterns:\n")
                    
                    # Sort by severity (critical -> high -> medium -> low)
                    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                    sorted_duplicates = sorted(duplicates, key=lambda x: severity_order.get(x.get('severity', 'low'), 4))
                    
                    for duplicate in sorted_duplicates:
                        # Severity emoji
                        severity_emoji = {
                            "critical": "🔴",
                            "high": "🟠", 
                            "medium": "🟡",
                            "low": "🟢"
                        }
                        
                        print(f"{severity_emoji.get(duplicate.get('severity', 'low'), '⚪')} {duplicate.get('severity', 'unknown').upper()} - {duplicate.get('description', 'Unknown')}")
                        print(f"   ID: {duplicate.get('id', 'unknown')}")
                        print(f"   Pattern: {duplicate.get('pattern', 'unknown')}")
                        print(f"   Occurrences: {duplicate.get('occurrence_count', 0)}")
                        print(f"   Similarity: {duplicate.get('similarity_score', 0):.1%}")
                        print(f"   Refactoring Type: {duplicate.get('refactoring_type', 'unknown')}")
                        print(f"   Estimated Effort: {duplicate.get('estimated_effort', 'unknown')}")
                        print(f"   Impact: {duplicate.get('impact', 'unknown')}")
                        print(f"   Suggestion: {duplicate.get('suggestion', 'unknown')}")
                        
                        # Show target files
                        print("   Target Files:")
                        for target_file in duplicate.get('target_files', []):
                            print(f"     📄 {target_file.get('file_path', 'unknown')}")
                            print(f"        Function: {target_file.get('function_name', 'unknown')}")
                            print(f"        Lines: {target_file.get('line_start', 0)}-{target_file.get('line_end', 0)}")
                            print(f"        Complexity: {target_file.get('complexity', 0)}")
                        
                        # Show code snippets
                        print("   Code Snippets:")
                        for snippet in duplicate.get('code_snippets', [])[:2]:  # Show first 2 snippets
                            print(f"     📝 {snippet.get('file_path', 'unknown')} - {snippet.get('function_name', 'unknown')}")
                            print(f"        {snippet.get('code_preview', '')[:100]}...")
                        
                        print("-" * 80)
                    
                    # Handle duplicate PR management if requested
                    if duplicate_pr_manager and (args.create_pr or args.group_duplicates):
                        print("\n🎯 Duplicate PR Management Options:")
                        print("   • Use --create-pr to create a GitHub PR from these duplicates")
                        print("   • Use --group-duplicates to group duplicates for PR creation")
                        print("   • Use --max-per-group N to set maximum duplicates per group")
                        
                else:
                    print("ℹ️  No duplicate code patterns found")
            
            # Group duplicates for PR creation
            if args.group_duplicates and duplicate_pr_manager:
                print("\n🔍 Grouping duplicates for PR creation...")
                duplicates = intelligent_generator.find_duplicate_code()
                if duplicates:
                    groups = duplicate_pr_manager.group_duplicates(duplicates, args.max_per_group)
                    if groups:
                        print(f"✅ Created {len(groups)} duplicate groups")
                        
                        # Display grouping options
                        duplicate_pr_manager.display_grouping_options(groups)
                        
                        # Get user selection if not auto-group
                        if not args.auto_group:
                            selected_groups = duplicate_pr_manager.get_user_selection(groups)
                        else:
                            selected_groups = groups
                            print(f"✅ Auto-selected all {len(groups)} groups")
                        
                        # Save template if requested
                        if args.save_template and selected_groups:
                            duplicate_pr_manager.save_template(args.save_template, selected_groups)
                        
                        # Create PR if requested
                        if args.create_pr and selected_groups:
                            print("\n🚀 Creating GitHub PR from selected duplicate groups...")
                            pr_template = duplicate_pr_manager.create_pr_template(selected_groups)
                            if pr_template:
                                success = duplicate_pr_manager.create_github_pr(pr_template, selected_groups)
                                if success:
                                    print("✅ GitHub PR created successfully!")
                                else:
                                    print("❌ Failed to create GitHub PR")
                            else:
                                print("❌ Failed to create PR template")
                    else:
                        print("❌ Failed to group duplicates")
                else:
                    print("ℹ️  No duplicates found to group")
            
            # Create PR directly from duplicates
            if args.create_pr and not args.group_duplicates and duplicate_pr_manager:
                print("\n🚀 Creating GitHub PR from duplicate findings...")
                duplicates = intelligent_generator.find_duplicate_code()
                if duplicates:
                    # Auto-group duplicates
                    groups = duplicate_pr_manager.group_duplicates(duplicates, args.max_per_group)
                    if groups:
                        print(f"✅ Auto-grouped {len(duplicates)} duplicates into {len(groups)} groups")
                        
                        # Create PR template
                        pr_template = duplicate_pr_manager.create_pr_template(groups)
                        if pr_template:
                            success = duplicate_pr_manager.create_github_pr(pr_template, groups)
                            if success:
                                print("✅ GitHub PR created successfully!")
                            else:
                                print("❌ Failed to create GitHub PR")
                        else:
                            print("❌ Failed to create PR template")
                    else:
                        print("❌ Failed to group duplicates")
                else:
                    print("ℹ️  No duplicates found to create PR from")
            
            # Load template
            if args.load_template and duplicate_pr_manager:
                print(f"\n📂 Loading template: {args.load_template}")
                groups = duplicate_pr_manager.load_template(args.load_template)
                if groups:
                    print(f"✅ Loaded template with {len(groups)} groups")
                    
                    # Display loaded groups
                    duplicate_pr_manager.display_grouping_options(groups)
                    
                    # Create PR if requested
                    if args.create_pr:
                        print("\n🚀 Creating GitHub PR from loaded template...")
                        pr_template = duplicate_pr_manager.create_pr_template(groups)
                        if pr_template:
                            success = duplicate_pr_manager.create_github_pr(pr_template, groups)
                            if success:
                                print("✅ GitHub PR created successfully!")
                            else:
                                print("❌ Failed to create GitHub PR")
                        else:
                            print("❌ Failed to create PR template")
                else:
                    print("❌ Failed to load template")
            
            # List templates
            if args.list_templates and duplicate_pr_manager:
                print("\n📚 Available duplicate grouping templates:")
                templates = duplicate_pr_manager.list_templates()
                if templates:
                    for i, template in enumerate(templates, 1):
                        print(f"   {i}. {template}")
                else:
                    print("   No templates found")
            
            # Weekly scan
            if args.weekly_scan and duplicate_pr_manager:
                print("\n📅 Running weekly duplicate scan...")
                duplicates = intelligent_generator.find_duplicate_code()
                if duplicates:
                    print(f"🔍 Found {len(duplicates)} duplicates in weekly scan")
                    
                    # Group duplicates
                    groups = duplicate_pr_manager.group_duplicates(duplicates, args.max_per_group)
                    if groups:
                        print(f"✅ Grouped into {len(groups)} manageable chunks")
                        
                        # Display weekly summary
                        print("\n📊 Weekly Duplicate Summary:")
                        total_effort = sum(group.estimated_effort_hours for group in groups)
                        total_files = len(set().union(*[set(group.files_affected) for group in groups]))
                        
                        print(f"   📁 Total files affected: {total_files}")
                        print(f"   ⏱️  Total estimated effort: {total_effort:.1f} hours")
                        print(f"   🎯 Groups ready for PR creation: {len(groups)}")
                        
                        # Ask if user wants to create PRs
                        print("\n🎯 Would you like to create PRs for these groups?")
                        print("   • Use --create-pr to create PRs now")
                        print("   • Use --save-template weekly_scan to save for later")
                        
                    else:
                        print("❌ Failed to group duplicates")
                else:
                    print("ℹ️  No duplicates found in weekly scan")
            
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
            
            # Cache management
            if args.cache_stats:
                print("📊 Cache Statistics:")
                insights = intelligent_generator.get_codebase_insights()
                cache_stats = insights.get("summary", {}).get("cache_stats", {})
                if cache_stats:
                    print(f"  📁 Cached files: {cache_stats.get('cached_files', 0)}")
                    print(f"  🕒 Last analysis: {cache_stats.get('last_analysis', 'Never')}")
                    print(f"  🔄 Last Git commit: {cache_stats.get('last_git_commit', 'None')}")
                    print(f"  📊 Total files analyzed: {cache_stats.get('total_files_analyzed', 0)}")
                    print(f"  🧩 Total chunks generated: {cache_stats.get('total_chunks_generated', 0)}")
                    print(f"  💾 Cache size: {cache_stats.get('cache_size_mb', 0)} MB")
                else:
                    print("  ℹ️  No cache statistics available")
            
            if args.clear_cache:
                print("🗑️  Clearing cache...")
                success = intelligent_generator.clear_cache()
                if success:
                    print("✅ Cache cleared successfully!")
                else:
                    print("❌ Failed to clear cache")
            
            if args.cache_info:
                print("ℹ️  Cache Information:")
                print("  📁 Cache directory: .iterate_cache/")
                print("  🗄️  Vector database: ChromaDB")
                print("  🔍 Change detection: Git + File system monitoring")
                print("  ⚡ Smart caching: Only processes changed files")
                print("  💾 Cache persistence: JSON + ChromaDB")
                    
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