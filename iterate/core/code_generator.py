"""
AI-powered code generation for Iterate.
Provides refactoring suggestions with actual code examples.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RefactoringSuggestion:
    """A specific refactoring suggestion with code examples."""
    file_path: str
    line_number: int
    suggestion_type: str
    description: str
    original_code: str
    suggested_code: str
    complexity_reduction: float
    confidence: float


@dataclass
class CodeImprovement:
    """Complete code improvement for a file."""
    file_path: str
    original_content: str
    improved_content: str
    changes_made: List[str]
    complexity_reduction: float
    quality_improvement: float


class CodeGenerator:
    """AI-powered code generator for refactoring suggestions."""
    
    def __init__(self):
        self.complexity_thresholds = {
            'high': 10,
            'medium': 7,
            'low': 5
        }
    
    def analyze_file_for_refactoring(self, file_path: str, complexity_metrics: Dict[str, Any]) -> List[RefactoringSuggestion]:
        """Analyze a file and generate refactoring suggestions."""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.py'):
                suggestions.extend(self._analyze_python_file(file_path, content, complexity_metrics))
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                suggestions.extend(self._analyze_js_file(file_path, content, complexity_metrics))
                
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path} for refactoring: {e}")
        
        return suggestions
    
    def _analyze_python_file(self, file_path: str, content: str, complexity_metrics: Dict[str, Any]) -> List[RefactoringSuggestion]:
        """Analyze Python file for refactoring opportunities."""
        suggestions = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            # Find complex functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    suggestions.extend(self._analyze_python_function(node, lines, file_path))
            
            # Find complex conditionals
            suggestions.extend(self._analyze_python_conditionals(tree, lines, file_path))
            
            # Find long functions
            suggestions.extend(self._analyze_python_long_functions(tree, lines, file_path))
            
        except SyntaxError:
            pass
        
        return suggestions
    
    def _analyze_python_function(self, func_node: ast.FunctionDef, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze a Python function for refactoring opportunities."""
        suggestions = []
        
        # Get function body
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 1
        func_lines = lines[start_line:end_line]
        func_content = '\n'.join(func_lines)
        
        # Calculate function complexity
        complexity = self._calculate_function_complexity(func_node)
        
        if complexity > self.complexity_thresholds['high']:
            # Suggest breaking down complex function
            suggestion = self._suggest_function_breakdown(func_node, func_content, complexity, file_path)
            if suggestion:
                suggestions.append(suggestion)
        
        # Check for nested conditionals
        nested_ifs = self._find_nested_conditionals(func_node)
        if nested_ifs:
            suggestion = self._suggest_simplified_conditionals(func_node, func_content, nested_ifs, file_path)
            if suggestion:
                suggestions.append(suggestion)
        
        # Check for long parameter lists
        if len(func_node.args.args) > 5:
            suggestion = self._suggest_parameter_object(func_node, func_content, file_path)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Try, ast.Assert)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
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
    
    def _suggest_function_breakdown(self, func_node: ast.FunctionDef, func_content: str, complexity: int, file_path: str) -> Optional[RefactoringSuggestion]:
        """Suggest breaking down a complex function."""
        # Extract potential helper functions
        helper_functions = self._extract_helper_functions(func_node)
        
        if helper_functions:
            original_code = func_content
            suggested_code = self._generate_breakdown_suggestion(func_node, helper_functions)
            
            return RefactoringSuggestion(
                file_path=file_path,
                line_number=func_node.lineno,
                suggestion_type="function_breakdown",
                description=f"Function '{func_node.name}' is too complex (complexity: {complexity}). Consider breaking it down into smaller functions.",
                original_code=original_code,
                suggested_code=suggested_code,
                complexity_reduction=complexity * 0.6,
                confidence=0.8
            )
        
        return None
    
    def _extract_helper_functions(self, func_node: ast.FunctionDef) -> List[Tuple[str, str]]:
        """Extract potential helper functions from a complex function."""
        helpers = []
        
        # Look for repeated patterns
        patterns = self._find_repeated_patterns(func_node)
        
        for i, pattern in enumerate(patterns):
            helper_name = f"_{func_node.name}_helper_{i+1}"
            helpers.append((helper_name, pattern))
        
        return helpers
    
    def _find_repeated_patterns(self, func_node: ast.FunctionDef) -> List[str]:
        """Find repeated code patterns in a function."""
        patterns = []
        
        # Simple pattern: repeated if-else blocks
        if_blocks = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                if_blocks.append(ast.unparse(node))
        
        # Find similar if blocks
        for i, block1 in enumerate(if_blocks):
            for j, block2 in enumerate(if_blocks[i+1:], i+1):
                if self._similar_patterns(block1, block2):
                    patterns.append(block1)
        
        return patterns
    
    def _similar_patterns(self, pattern1: str, pattern2: str) -> bool:
        """Check if two code patterns are similar."""
        # Simple similarity check
        return len(pattern1) > 20 and len(pattern2) > 20 and pattern1[:50] == pattern2[:50]
    
    def _generate_breakdown_suggestion(self, func_node: ast.FunctionDef, helpers: List[Tuple[str, str]]) -> str:
        """Generate code suggestion for function breakdown."""
        suggestion = f"""# Refactored version of {func_node.name}
"""
        
        # Add helper functions
        for helper_name, helper_code in helpers:
            suggestion += f"""
def {helper_name}(self):
    {helper_code}
"""
        
        # Add main function
        suggestion += f"""
def {func_node.name}(self):
    # Main logic using helper functions
    result = self.{helpers[0][0]}()
    # ... rest of the logic
    return result
"""
        
        return suggestion
    
    def _suggest_simplified_conditionals(self, func_node: ast.FunctionDef, func_content: str, nested_ifs: List[ast.If], file_path: str) -> Optional[RefactoringSuggestion]:
        """Suggest simplified conditional logic."""
        if not nested_ifs:
            return None
        
        original_code = func_content
        suggested_code = self._generate_simplified_conditionals(func_node, nested_ifs)
        
        return RefactoringSuggestion(
            file_path=file_path,
            line_number=func_node.lineno,
            suggestion_type="simplified_conditionals",
            description=f"Function '{func_node.name}' has deeply nested conditionals. Consider using early returns or guard clauses.",
            original_code=original_code,
            suggested_code=suggested_code,
            complexity_reduction=len(nested_ifs) * 0.5,
            confidence=0.7
        )
    
    def _generate_simplified_conditionals(self, func_node: ast.FunctionDef, nested_ifs: List[ast.If]) -> str:
        """Generate simplified conditional logic."""
        suggestion = f"""# Simplified version of {func_node.name}
def {func_node.name}(self):
    # Use early returns to reduce nesting
    if not self.condition1:
        return None
    
    if not self.condition2:
        return None
    
    # Main logic here
    return result
"""
        return suggestion
    
    def _suggest_parameter_object(self, func_node: ast.FunctionDef, func_content: str, file_path: str) -> Optional[RefactoringSuggestion]:
        """Suggest using parameter objects for long parameter lists."""
        if len(func_node.args.args) <= 5:
            return None
        
        original_code = func_content
        suggested_code = self._generate_parameter_object(func_node)
        
        return RefactoringSuggestion(
            file_path=file_path,
            line_number=func_node.lineno,
            suggestion_type="parameter_object",
            description=f"Function '{func_node.name}' has too many parameters. Consider using a parameter object.",
            original_code=original_code,
            suggested_code=suggested_code,
            complexity_reduction=0.3,
            confidence=0.6
        )
    
    def _generate_parameter_object(self, func_node: ast.FunctionDef) -> str:
        """Generate parameter object suggestion."""
        param_names = [arg.arg for arg in func_node.args.args]
        
        suggestion = f"""# Parameter object for {func_node.name}
@dataclass
class {func_node.name}Params:
    {chr(10).join(f'    {param}: Any' for param in param_names)}

def {func_node.name}(params: {func_node.name}Params):
    # Use params.{param_names[0]}, params.{param_names[1]}, etc.
    pass
"""
        return suggestion
    
    def _analyze_python_conditionals(self, tree: ast.AST, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze Python conditionals for simplification opportunities."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check for complex boolean expressions
                if self._is_complex_boolean(node.test):
                    suggestion = self._suggest_boolean_simplification(node, lines, file_path)
                    if suggestion:
                        suggestions.append(suggestion)
        
        return suggestions
    
    def _is_complex_boolean(self, test_node: ast.expr) -> bool:
        """Check if a boolean expression is complex."""
        if isinstance(test_node, ast.BoolOp):
            return len(test_node.values) > 3
        return False
    
    def _suggest_boolean_simplification(self, if_node: ast.If, lines: List[str], file_path: str) -> Optional[RefactoringSuggestion]:
        """Suggest boolean expression simplification."""
        start_line = if_node.lineno - 1
        end_line = if_node.end_lineno if hasattr(if_node, 'end_lineno') else start_line + 1
        if_content = '\n'.join(lines[start_line:end_line])
        
        original_code = if_content
        suggested_code = self._generate_boolean_simplification(if_node)
        
        return RefactoringSuggestion(
            file_path=file_path,
            line_number=if_node.lineno,
            suggestion_type="boolean_simplification",
            description="Complex boolean expression detected. Consider extracting to a helper method.",
            original_code=original_code,
            suggested_code=suggested_code,
            complexity_reduction=0.4,
            confidence=0.7
        )
    
    def _generate_boolean_simplification(self, if_node: ast.If) -> str:
        """Generate boolean simplification suggestion."""
        return """# Extract complex boolean to helper method
def is_valid_condition(self, param1, param2, param3):
    return (param1 and param2) or (param3 and param1)

if self.is_valid_condition(a, b, c):
    # ... rest of the logic
    pass
"""
    
    def _analyze_python_long_functions(self, tree: ast.AST, lines: List[str], file_path: str) -> List[RefactoringSuggestion]:
        """Analyze Python functions for length issues."""
        suggestions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno - 1
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                func_length = end_line - start_line
                
                if func_length > 50:  # Long function threshold
                    suggestion = self._suggest_function_split(node, lines, file_path, func_length)
                    if suggestion:
                        suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_function_split(self, func_node: ast.FunctionDef, lines: List[str], file_path: str, func_length: int) -> Optional[RefactoringSuggestion]:
        """Suggest splitting a long function."""
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno if hasattr(func_node, 'end_lineno') else start_line + 1
        func_content = '\n'.join(lines[start_line:end_line])
        
        original_code = func_content
        suggested_code = self._generate_function_split(func_node, func_length)
        
        return RefactoringSuggestion(
            file_path=file_path,
            line_number=func_node.lineno,
            suggestion_type="function_split",
            description=f"Function '{func_node.name}' is too long ({func_length} lines). Consider splitting into smaller functions.",
            original_code=original_code,
            suggested_code=suggested_code,
            complexity_reduction=func_length * 0.1,
            confidence=0.8
        )
    
    def _generate_function_split(self, func_node: ast.FunctionDef, func_length: int) -> str:
        """Generate function split suggestion."""
        return f"""# Split {func_node.name} into smaller functions
def {func_node.name}_part1(self):
    # First part of the logic
    pass

def {func_node.name}_part2(self):
    # Second part of the logic
    pass

def {func_node.name}(self):
    # Main function orchestrating the parts
    result1 = self.{func_node.name}_part1()
    result2 = self.{func_node.name}_part2()
    return self.combine_results(result1, result2)
"""
    
    def _analyze_js_file(self, file_path: str, content: str, complexity_metrics: Dict[str, Any]) -> List[RefactoringSuggestion]:
        """Analyze JavaScript/TypeScript file for refactoring opportunities."""
        suggestions = []
        
        # Find complex functions using regex
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
        matches = re.finditer(function_pattern, content, re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            func_content = match.group(0)
            
            # Analyze function complexity
            complexity = self._calculate_js_complexity(func_content)
            
            if complexity > self.complexity_thresholds['high']:
                suggestion = self._suggest_js_function_breakdown(func_name, func_content, complexity, file_path)
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _calculate_js_complexity(self, func_content: str) -> int:
        """Calculate complexity of a JavaScript function."""
        complexity = 1
        
        # Count control flow statements
        complexity += len(re.findall(r'\b(if|while|for|catch|switch)\b', func_content))
        complexity += len(re.findall(r'\b(&&|\|\|)\b', func_content))
        
        return complexity
    
    def _suggest_js_function_breakdown(self, func_name: str, func_content: str, complexity: int, file_path: str) -> Optional[RefactoringSuggestion]:
        """Suggest breaking down a complex JavaScript function."""
        original_code = func_content
        suggested_code = self._generate_js_breakdown_suggestion(func_name, complexity)
        
        return RefactoringSuggestion(
            file_path=file_path,
            line_number=1,  # Approximate
            suggestion_type="js_function_breakdown",
            description=f"Function '{func_name}' is too complex (complexity: {complexity}). Consider breaking it down into smaller functions.",
            original_code=original_code,
            suggested_code=suggested_code,
            complexity_reduction=complexity * 0.6,
            confidence=0.7
        )
    
    def _generate_js_breakdown_suggestion(self, func_name: str, complexity: int) -> str:
        """Generate JavaScript function breakdown suggestion."""
        return f"""// Refactored version of {func_name}
function {func_name}_helper1() {{
    // Helper function 1
    return result1;
}}

function {func_name}_helper2() {{
    // Helper function 2
    return result2;
}}

function {func_name}() {{
    // Main function using helpers
    const result1 = {func_name}_helper1();
    const result2 = {func_name}_helper2();
    return combineResults(result1, result2);
}}
"""
    
    def generate_complete_improvement(self, file_path: str, suggestions: List[RefactoringSuggestion]) -> Optional[CodeImprovement]:
        """Generate a complete improved version of a file."""
        if not suggestions:
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            improved_content = original_content
            changes_made = []
            total_complexity_reduction = 0
            
            # Apply suggestions in order
            for suggestion in suggestions:
                if suggestion.confidence > 0.6:  # Only apply high-confidence suggestions
                    improved_content = self._apply_suggestion(improved_content, suggestion)
                    changes_made.append(suggestion.description)
                    total_complexity_reduction += suggestion.complexity_reduction
            
            if changes_made:
                return CodeImprovement(
                    file_path=file_path,
                    original_content=original_content,
                    improved_content=improved_content,
                    changes_made=changes_made,
                    complexity_reduction=total_complexity_reduction,
                    quality_improvement=len(changes_made) * 0.1
                )
        
        except Exception as e:
            print(f"⚠️  Error generating improvement for {file_path}: {e}")
        
        return None
    
    def _apply_suggestion(self, content: str, suggestion: RefactoringSuggestion) -> str:
        """Apply a refactoring suggestion to the content."""
        # Simple string replacement for now
        # In a real implementation, this would use AST manipulation
        return content.replace(suggestion.original_code, suggestion.suggested_code) 