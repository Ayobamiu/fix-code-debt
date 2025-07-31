"""
Conservative dependency mapping system.
Focuses on reliability and clean code over complexity.
"""

import ast
import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from enum import Enum

from .error_handler import ErrorHandler
from .progress_reporter import ProgressReporter


class DependencyType(Enum):
    """Types of dependencies we can detect."""
    IMPORT = "import"
    FROM_IMPORT = "from_import"
    FUNCTION_CALL = "function_call"
    CLASS_INHERITANCE = "class_inheritance"


@dataclass
class Dependency:
    """Represents a single dependency."""
    source_file: str
    target_file: str
    dependency_type: DependencyType
    line_number: int
    element_name: str
    is_resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "dependency_type": self.dependency_type.value,
            "line_number": self.line_number,
            "element_name": self.element_name,
            "is_resolved": self.is_resolved
        }


@dataclass
class FileDependencies:
    """Dependencies for a single file."""
    file_path: str
    imports: List[Dependency]
    exports: List[str]  # Function/class names defined in this file
    dependencies: List[Dependency]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "imports": [dep.to_dict() for dep in self.imports],
            "exports": self.exports,
            "dependencies": [dep.to_dict() for dep in self.dependencies]
        }


class DependencyMapper:
    """
    Conservative dependency mapper using Python AST.
    Focuses on reliability and clean code.
    """
    
    def __init__(self, error_handler: ErrorHandler, progress_reporter: ProgressReporter):
        self.error_handler = error_handler
        self.progress_reporter = progress_reporter
        self.cache_file = ".dependency_cache/dependencies.json"
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        cache_dir = Path(self.cache_file).parent
        cache_dir.mkdir(exist_ok=True)
    
    def analyze_file(self, file_path: str) -> Optional[FileDependencies]:
        """
        Analyze a single file for dependencies.
        Returns None if file cannot be analyzed.
        """
        try:
            if file_path.endswith('.py'):
                return self._analyze_python_file(file_path)
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                return self._analyze_js_ts_file(file_path)
            else:
                return None
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                context={"operation": "analyze_file", "file_path": file_path}
            )
            return None
    
    def _analyze_python_file(self, file_path: str) -> Optional[FileDependencies]:
        """Analyze a Python file using AST."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            imports = self._extract_imports(tree, file_path)
            exports = self._extract_exports(tree)
            dependencies = imports.copy()  # For now, imports are our dependencies
            
            return FileDependencies(
                file_path=file_path,
                imports=imports,
                exports=exports,
                dependencies=dependencies
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                context={"operation": "analyze_python_file", "file_path": file_path}
            )
            return None
    
    def _analyze_js_ts_file(self, file_path: str) -> Optional[FileDependencies]:
        """Analyze a JavaScript/TypeScript file using regex."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imports = self._extract_js_ts_imports(file_path, content)
            exports = self._extract_js_ts_exports(content)
            dependencies = imports.copy()  # For now, imports are our dependencies
            
            return FileDependencies(
                file_path=file_path,
                imports=imports,
                exports=exports,
                dependencies=dependencies
            )
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                context={"operation": "analyze_js_ts_file", "file_path": file_path}
            )
            return None
    
    def _extract_imports(self, tree: ast.AST, file_path: str) -> List[Dependency]:
        """Extract import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(Dependency(
                        source_file=file_path,
                        target_file=f"{alias.name}.py",  # Simplified
                        dependency_type=DependencyType.IMPORT,
                        line_number=node.lineno,
                        element_name=alias.name
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(Dependency(
                        source_file=file_path,
                        target_file=f"{module}.py",  # Simplified
                        dependency_type=DependencyType.FROM_IMPORT,
                        line_number=node.lineno,
                        element_name=alias.name
                    ))
        
        return imports
    
    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """Extract function and class definitions (potential exports)."""
        exports = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                exports.append(node.name)
        
        return exports
    
    def analyze_codebase(self, files: List[str]) -> Dict[str, FileDependencies]:
        """
        Analyze entire codebase for dependencies.
        Returns mapping of file_path -> FileDependencies.
        """
        # Get the directory being analyzed (from first file)
        analysis_dir = os.path.dirname(files[0]) if files else "unknown"
        
        self.progress_reporter.start_scan(
            directory=analysis_dir,
            estimated_files=len(files),
            estimated_dirs=0
        )
        
        results = {}
        processed = 0
        
        for file_path in files:
            if file_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                result = self.analyze_file(file_path)
                if result:
                    results[file_path] = result
            
            processed += 1
            if processed % 10 == 0:  # Update progress every 10 files
                self.progress_reporter.update_progress(
                    current_file=os.path.basename(file_path),
                    current_directory=os.path.dirname(file_path),
                    files_processed=processed,
                    directories_processed=0,
                    total_files_found=len(files),
                    total_directories_found=0
                )
        
        self.progress_reporter.finish_scan(
            total_files=len(files),
            total_directories=0
        )
        
        return results
    
    def save_dependencies(self, dependencies: Dict[str, FileDependencies]):
        """Save dependencies to cache file."""
        try:
            data = {path: deps.to_dict() for path, deps in dependencies.items()}
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                context={"operation": "save_dependencies", "cache_file": self.cache_file}
            )
    
    def load_dependencies(self) -> Dict[str, FileDependencies]:
        """Load dependencies from cache file."""
        try:
            if not os.path.exists(self.cache_file):
                return {}
            
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to FileDependencies objects
            dependencies = {}
            for path, deps_dict in data.items():
                # Reconstruct FileDependencies from dict
                # This is simplified - in production we'd want proper deserialization
                dependencies[path] = FileDependencies(
                    file_path=path,
                    imports=[],  # Would need to reconstruct Dependency objects
                    exports=deps_dict.get('exports', []),
                    dependencies=[]
                )
            
            return dependencies
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                context={"operation": "load_dependencies", "cache_file": self.cache_file}
            )
            return {}
    
    def get_impact_analysis(self, file_path: str, dependencies: Dict[str, FileDependencies]) -> List[str]:
        """
        Get list of files that would be impacted if the given file changes.
        Conservative implementation - just returns direct dependents.
        """
        impacted = []
        
        for dep_path, dep_data in dependencies.items():
            for dep in dep_data.dependencies:
                if dep.target_file == file_path:
                    impacted.append(dep_path)
        
        return list(set(impacted))  # Remove duplicates
    
    def _extract_js_ts_imports(self, file_path: str, content: str) -> List[Dependency]:
        """Extract import statements from JavaScript/TypeScript using regex."""
        imports = []
        
        # Common import patterns
        import_patterns = [
            # ES6 imports
            r'import\s+(\{[^}]*\})\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            # CommonJS imports
            r'const\s+(\w+)\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'var\s+(\w+)\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'let\s+(\w+)\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                
                if len(match.groups()) >= 2:
                    # Named import or require
                    element_name = match.group(1)
                    module_name = match.group(2)
                else:
                    # Default import
                    element_name = match.group(1) if match.groups() else "default"
                    module_name = match.group(1)
                
                # Clean up element name (remove braces for destructuring)
                element_name = re.sub(r'[{}]', '', element_name).strip()
                
                imports.append(Dependency(
                    source_file=file_path,
                    target_file=f"{module_name}.js",  # Simplified
                    dependency_type=DependencyType.IMPORT,
                    line_number=line_number,
                    element_name=element_name
                ))
        
        return imports
    
    def _extract_js_ts_exports(self, content: str) -> List[str]:
        """Extract exports from JavaScript/TypeScript using regex."""
        exports = []
        
        # Export patterns
        export_patterns = [
            # Named exports
            r'export\s+(?:const|let|var|function|class)\s+(\w+)',
            r'export\s+\{\s*([^}]+)\s*\}',
            # Default exports
            r'export\s+default\s+(?:function|class)\s+(\w+)',
            r'export\s+default\s+(\w+)',
            # Function/class declarations
            r'(?:export\s+)?(?:function|class)\s+(\w+)',
        ]
        
        for pattern in export_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                if match.groups():
                    export_name = match.group(1).strip()
                    # Handle multiple exports in braces
                    if '{' in export_name:
                        # Split by comma and clean up
                        multiple_exports = [exp.strip() for exp in export_name.split(',')]
                        exports.extend(multiple_exports)
                    else:
                        exports.append(export_name)
        
        return list(set(exports))  # Remove duplicates 