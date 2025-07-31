"""
Simple dependency analyzer utility.
Integrates FileFinder with DependencyMapper for easy analysis.
"""

from typing import Dict, List
from ..core.file_finder import FileFinder
from ..core.dependency_mapper import DependencyMapper, FileDependencies
from ..core.error_handler import ErrorHandler
from ..core.progress_reporter import ProgressReporter


class DependencyAnalyzer:
    """
    High-level dependency analyzer that combines file finding and dependency mapping.
    """
    
    def __init__(self, directory: str, error_handler: ErrorHandler, progress_reporter: ProgressReporter):
        self.directory = directory
        self.error_handler = error_handler
        self.progress_reporter = progress_reporter
        
        # Initialize components
        self.file_finder = FileFinder(
            error_handler=error_handler,
            progress_reporter=progress_reporter
        )
        
        self.dependency_mapper = DependencyMapper(
            error_handler=error_handler,
            progress_reporter=progress_reporter
        )
    
    def analyze_codebase(self) -> Dict[str, FileDependencies]:
        """
        Analyze the entire codebase for dependencies.
        Returns mapping of file_path -> FileDependencies.
        """
        # Find all files
        result = self.file_finder.find_files_and_folders(self.directory)
        files = result.get('files', [])
        folders = result.get('folders', [])
        code_files = [f for f in files if f.endswith(('.py', '.js', '.jsx', '.ts', '.tsx'))]
        
        # Analyze dependencies
        dependencies = self.dependency_mapper.analyze_codebase(code_files)
        
        # Save results
        self.dependency_mapper.save_dependencies(dependencies)
        
        return dependencies, files
    
    def get_impact_analysis(self, file_path: str) -> List[str]:
        """
        Get files that would be impacted if the given file changes.
        """
        dependencies = self.dependency_mapper.load_dependencies()
        return self.dependency_mapper.get_impact_analysis(file_path, dependencies)
    
    def print_analysis_summary(self, dependencies: Dict[str, FileDependencies], all_files: List[str] = None):
        """Print a summary of the dependency analysis."""
        total_files = len(dependencies)
        total_imports = sum(len(deps.imports) for deps in dependencies.values())
        total_exports = sum(len(deps.exports) for deps in dependencies.values())
        
        print(f"\n📊 Dependency Analysis Summary:")
        print(f"   Files analyzed: {total_files}")
        print(f"   Total imports: {total_imports}")
        print(f"   Total exports: {total_exports}")
        
        # Show file type breakdown if we have all_files
        if all_files:
            python_files = [f for f in all_files if f.endswith('.py')]
            js_files = [f for f in all_files if f.endswith(('.js', '.jsx'))]
            ts_files = [f for f in all_files if f.endswith(('.ts', '.tsx'))]
            code_files = [f for f in all_files if f.endswith(('.py', '.js', '.jsx', '.ts', '.tsx'))]
            
            print(f"\n📁 File Type Breakdown:")
            print(f"   Total code files found: {len(code_files)}")
            print(f"   Python files (.py): {len(python_files)}")
            print(f"   JavaScript files (.js/.jsx): {len(js_files)}")
            print(f"   TypeScript files (.ts/.tsx): {len(ts_files)}")
            print(f"   Other code files: {len(all_files) - len(code_files)}")
            
            if len(code_files) == 0:
                print(f"\n⚠️  No supported code files found!")
                print(f"   Supported: Python (.py), JavaScript (.js/.jsx), TypeScript (.ts/.tsx)")
            elif len(python_files) == 0 and len(js_files) + len(ts_files) > 0:
                print(f"\n✅ Found {len(js_files) + len(ts_files)} JavaScript/TypeScript files - analyzing them!")
        
        if dependencies:
            print(f"\n📁 Files with dependencies:")
            for file_path, deps in dependencies.items():
                print(f"   {file_path}: {len(deps.imports)} imports, {len(deps.exports)} exports")
    
    def export_analysis(self, dependencies: Dict[str, FileDependencies], output_file: str = "dependencies.json"):
        """Export dependency analysis to JSON file."""
        try:
            data = {path: deps.to_dict() for path, deps in dependencies.items()}
            with open(output_file, 'w') as f:
                import json
                json.dump(data, f, indent=2)
            print(f"✅ Dependencies exported to {output_file}")
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                context={"operation": "export_analysis", "output_file": output_file}
            ) 