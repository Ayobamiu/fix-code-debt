"""
AI-powered documentation generation for Iterate.
Generates docstrings, best practice recommendations, and documentation.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentationSuggestion:
    """A documentation suggestion with actual docstring code."""
    file_path: str
    function_name: str
    suggestion_type: str
    description: str
    original_code: str
    suggested_docstring: str
    best_practices: List[str]
    confidence: float


@dataclass
class DocumentationCoverage:
    """Documentation coverage information for a file."""
    file_path: str
    total_functions: int
    documented_functions: int
    coverage_percentage: float
    missing_docs: List[str]
    suggested_docs: List[DocumentationSuggestion]


class DocumentationGenerator:
    """AI-powered documentation generator for improving code documentation."""
    
    def __init__(self):
        self.doc_patterns = {
            'python': {
                'google': '"""\n{description}\n\nArgs:\n{args}\n\nReturns:\n{returns}\n\nRaises:\n{raises}\n"""',
                'numpy': '"""\n{description}\n\nParameters\n----------\n{params}\n\nReturns\n-------\n{returns}\n\nRaises\n------\n{raises}\n"""',
                'simple': '"""\n{description}\n"""'
            },
            'javascript': {
                'jsdoc': '/**\n * {description}\n * @param {{{type}}} {param} - {description}\n * @returns {{{type}}} {description}\n */',
                'simple': '// {description}'
            }
        }
    
    def analyze_file_for_documentation(self, file_path: str) -> DocumentationCoverage:
        """Analyze a file and generate documentation suggestions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.py'):
                return self._analyze_python_file_for_docs(file_path, content)
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                return self._analyze_js_file_for_docs(file_path, content)
            else:
                return DocumentationCoverage(file_path, 0, 0, 0.0, [], [])
                
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path} for documentation: {e}")
            return DocumentationCoverage(file_path, 0, 0, 0.0, [], [])
    
    def _analyze_python_file_for_docs(self, file_path: str, content: str) -> DocumentationCoverage:
        """Analyze Python file for documentation coverage and generate suggestions."""
        try:
            tree = ast.parse(content)
            
            # Find all functions
            functions = []
            documented_functions = []
            missing_docs = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    
                    # Check if function has docstring
                    if (node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)):
                        documented_functions.append(node.name)
                    else:
                        missing_docs.append(node.name)
            
            # Calculate coverage
            coverage_percentage = len(documented_functions) / max(len(functions), 1) * 100
            
            # Generate documentation suggestions
            suggested_docs = []
            for func_name in missing_docs[:5]:  # Limit to top 5
                suggestion = self._generate_python_docstring(file_path, func_name, tree)
                if suggestion:
                    suggested_docs.append(suggestion)
            
            return DocumentationCoverage(
                file_path=file_path,
                total_functions=len(functions),
                documented_functions=len(documented_functions),
                coverage_percentage=coverage_percentage,
                missing_docs=missing_docs,
                suggested_docs=suggested_docs
            )
            
        except SyntaxError:
            return DocumentationCoverage(file_path, 0, 0, 0.0, [], [])
    
    def _generate_python_docstring(self, file_path: str, func_name: str, tree: ast.AST) -> Optional[DocumentationSuggestion]:
        """Generate a Python docstring for a specific function."""
        # Find the function definition
        target_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                target_function = node
                break
        
        if not target_function:
            return None
        
        # Analyze function parameters
        params = [arg.arg for arg in target_function.args.args]
        
        # Generate docstring
        docstring = self._generate_python_docstring_code(func_name, params, target_function)
        
        # Generate best practices
        best_practices = self._generate_best_practices(target_function)
        
        return DocumentationSuggestion(
            file_path=file_path,
            function_name=func_name,
            suggestion_type="docstring",
            description=f"Missing docstring for function '{func_name}'",
            original_code=f"def {func_name}({', '.join(params)}):",
            suggested_docstring=docstring,
            best_practices=best_practices,
            confidence=0.8
        )
    
    def _generate_python_docstring_code(self, func_name: str, params: List[str], func_node: ast.FunctionDef) -> str:
        """Generate Python docstring code for a function."""
        # Analyze function complexity
        complexity = self._calculate_function_complexity(func_node)
        
        # Generate description based on function name and parameters
        description = self._generate_function_description(func_name, params)
        
        # Generate args section
        args_section = ""
        if params:
            args_section = "\n".join([f"    {param}: Description of {param}" for param in params])
        
        # Generate returns section
        returns_section = "    Description of return value"
        
        # Generate raises section
        raises_section = "    Exception: Description of when this exception is raised"
        
        # Use Google style docstring
        docstring = f'''"""
{description}

Args:
{args_section}

Returns:
{returns_section}

Raises:
{raises_section}
"""'''
        
        return docstring
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Try, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _generate_function_description(self, func_name: str, params: List[str]) -> str:
        """Generate a description for a function based on its name and parameters."""
        # Simple heuristic-based description generation
        if 'get' in func_name.lower():
            return f"Get {func_name[3:].replace('_', ' ')}"
        elif 'set' in func_name.lower():
            return f"Set {func_name[3:].replace('_', ' ')}"
        elif 'create' in func_name.lower():
            return f"Create {func_name[6:].replace('_', ' ')}"
        elif 'update' in func_name.lower():
            return f"Update {func_name[6:].replace('_', ' ')}"
        elif 'delete' in func_name.lower():
            return f"Delete {func_name[6:].replace('_', ' ')}"
        elif 'analyze' in func_name.lower():
            return f"Analyze {func_name[7:].replace('_', ' ')}"
        elif 'generate' in func_name.lower():
            return f"Generate {func_name[9:].replace('_', ' ')}"
        elif 'handle' in func_name.lower():
            return f"Handle {func_name[6:].replace('_', ' ')}"
        elif 'process' in func_name.lower():
            return f"Process {func_name[7:].replace('_', ' ')}"
        elif 'validate' in func_name.lower():
            return f"Validate {func_name[8:].replace('_', ' ')}"
        elif 'format' in func_name.lower():
            return f"Format {func_name[6:].replace('_', ' ')}"
        elif 'parse' in func_name.lower():
            return f"Parse {func_name[5:].replace('_', ' ')}"
        elif 'convert' in func_name.lower():
            return f"Convert {func_name[7:].replace('_', ' ')}"
        elif 'find' in func_name.lower():
            return f"Find {func_name[4:].replace('_', ' ')}"
        elif 'check' in func_name.lower():
            return f"Check {func_name[5:].replace('_', ' ')}"
        elif 'is_' in func_name.lower():
            return f"Check if {func_name[3:].replace('_', ' ')}"
        elif 'has_' in func_name.lower():
            return f"Check if has {func_name[4:].replace('_', ' ')}"
        elif 'can_' in func_name.lower():
            return f"Check if can {func_name[4:].replace('_', ' ')}"
        elif 'should_' in func_name.lower():
            return f"Check if should {func_name[7:].replace('_', ' ')}"
        elif 'will_' in func_name.lower():
            return f"Check if will {func_name[5:].replace('_', ' ')}"
        else:
            return f"Perform {func_name.replace('_', ' ')} operation"
    
    def _generate_best_practices(self, func_node: ast.FunctionDef) -> List[str]:
        """Generate best practice recommendations for a function."""
        practices = []
        
        # Check function length
        if len(func_node.body) > 20:
            practices.append("Consider breaking down this long function into smaller functions")
        
        # Check parameter count
        if len(func_node.args.args) > 5:
            practices.append("Consider using a parameter object for functions with many parameters")
        
        # Check complexity
        complexity = self._calculate_function_complexity(func_node)
        if complexity > 10:
            practices.append("Consider reducing complexity by extracting helper functions")
        
        # Check for nested conditionals
        nested_ifs = self._find_nested_conditionals(func_node)
        if nested_ifs:
            practices.append("Consider using early returns to reduce nesting")
        
        # Check for magic numbers
        magic_numbers = self._find_magic_numbers(func_node)
        if magic_numbers:
            practices.append("Consider extracting magic numbers as named constants")
        
        # Check for long lines
        long_lines = self._find_long_lines(func_node)
        if long_lines:
            practices.append("Consider breaking long lines for better readability")
        
        return practices
    
    def _find_nested_conditionals(self, func_node: ast.FunctionDef) -> List[ast.If]:
        """Find deeply nested conditional statements."""
        nested_ifs = []
        
        def find_nested(node, depth=0):
            if isinstance(node, ast.If) and depth > 2:
                nested_ifs.append(node)
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.If):
                    find_nested(child, depth + 1)
                else:
                    find_nested(child, depth)
        
        find_nested(func_node)
        return nested_ifs
    
    def _find_magic_numbers(self, func_node: ast.FunctionDef) -> List[int]:
        """Find magic numbers in a function."""
        magic_numbers = []
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                value = node.value
                if value not in [0, 1, -1] and value not in magic_numbers:
                    magic_numbers.append(value)
        
        return magic_numbers
    
    def _find_long_lines(self, func_node: ast.FunctionDef) -> List[str]:
        """Find long lines in a function."""
        long_lines = []
        
        # This is a simplified check - in practice, you'd analyze the actual source
        return long_lines
    
    def _analyze_js_file_for_docs(self, file_path: str, content: str) -> DocumentationCoverage:
        """Analyze JavaScript file for documentation coverage and generate suggestions."""
        # Find functions using regex
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
        matches = re.finditer(function_pattern, content, re.DOTALL)
        
        functions = [match.group(1) for match in matches]
        
        # Find documented functions
        documented_functions = []
        missing_docs = []
        
        for func_name in functions:
            # Check if function has JSDoc comment
            jsdoc_pattern = rf'/\*\*[\s\S]*?\*/\s*function\s+{func_name}'
            if re.search(jsdoc_pattern, content):
                documented_functions.append(func_name)
            else:
                missing_docs.append(func_name)
        
        # Calculate coverage
        coverage_percentage = len(documented_functions) / max(len(functions), 1) * 100
        
        # Generate documentation suggestions
        suggested_docs = []
        for func_name in missing_docs[:5]:  # Limit to top 5
            suggestion = self._generate_js_docstring(file_path, func_name, content)
            if suggestion:
                suggested_docs.append(suggestion)
        
        return DocumentationCoverage(
            file_path=file_path,
            total_functions=len(functions),
            documented_functions=len(documented_functions),
            coverage_percentage=coverage_percentage,
            missing_docs=missing_docs,
            suggested_docs=suggested_docs
        )
    
    def _generate_js_docstring(self, file_path: str, func_name: str, content: str) -> Optional[DocumentationSuggestion]:
        """Generate a JavaScript docstring for a specific function."""
        # Extract function parameters
        func_pattern = rf'function\s+{func_name}\s*\(([^)]*)\)'
        match = re.search(func_pattern, content)
        
        params = []
        if match:
            param_str = match.group(1).strip()
            if param_str:
                params = [p.strip() for p in param_str.split(',')]
        
        # Generate JSDoc comment
        jsdoc = self._generate_js_docstring_code(func_name, params)
        
        return DocumentationSuggestion(
            file_path=file_path,
            function_name=func_name,
            suggestion_type="jsdoc",
            description=f"Missing JSDoc for function '{func_name}'",
            original_code=f"function {func_name}({', '.join(params)}) {{",
            suggested_docstring=jsdoc,
            best_practices=["Consider adding parameter types", "Add return type annotation"],
            confidence=0.7
        )
    
    def _generate_js_docstring_code(self, func_name: str, params: List[str]) -> str:
        """Generate JavaScript JSDoc code for a function."""
        description = self._generate_function_description(func_name, params)
        
        jsdoc = f"""/**
 * {description}
"""
        
        # Add parameter documentation
        for param in params:
            jsdoc += f" * @param {{any}} {param} - Description of {param}\n"
        
        jsdoc += f""" * @returns {{any}} Description of return value
 */"""
        
        return jsdoc
    
    def generate_documentation_report(self, files: List[str]) -> Dict[str, Any]:
        """Generate comprehensive documentation report."""
        report = {
            'files_analyzed': 0,
            'total_functions': 0,
            'documented_functions': 0,
            'overall_coverage': 0.0,
            'file_coverage': {},
            'suggestions': []
        }
        
        total_functions = 0
        total_documented = 0
        
        for file_path in files:
            if file_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                coverage = self.analyze_file_for_documentation(file_path)
                
                report['files_analyzed'] += 1
                report['file_coverage'][file_path] = coverage
                total_functions += coverage.total_functions
                total_documented += coverage.documented_functions
                
                report['suggestions'].extend(coverage.suggested_docs)
        
        report['total_functions'] = total_functions
        report['documented_functions'] = total_documented
        report['overall_coverage'] = total_documented / max(total_functions, 1) * 100
        
        return report 