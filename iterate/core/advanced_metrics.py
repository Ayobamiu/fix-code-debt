"""
Advanced code quality metrics for Iterate.
Provides sophisticated analysis beyond basic dependency counting.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComplexityMetrics:
    """Code complexity metrics."""
    cyclomatic_complexity: int
    cognitive_complexity: int
    maintainability_index: float
    lines_of_code: int
    comment_ratio: float


@dataclass
class QualityMetrics:
    """Overall code quality metrics."""
    complexity_score: float
    duplication_score: float
    test_coverage_score: float
    documentation_score: float
    overall_score: float


class AdvancedCodeAnalyzer:
    """Advanced code quality analyzer."""
    
    def __init__(self):
        self.complexity_thresholds = {
            'low': 5,
            'medium': 10,
            'high': 15
        }
    
    def analyze_file_complexity(self, file_path: str) -> Optional[ComplexityMetrics]:
        """Analyze code complexity for a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.py'):
                return self._analyze_python_complexity(content)
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                return self._analyze_js_complexity(content)
            else:
                return None
                
        except Exception as e:
            print(f"⚠️  Error analyzing complexity for {file_path}: {e}")
            return None
    
    def _analyze_python_complexity(self, content: str) -> ComplexityMetrics:
        """Analyze Python code complexity using AST."""
        try:
            tree = ast.parse(content)
            
            # Count lines of code
            lines = content.split('\n')
            loc = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            # Count comments
            comments = len([line for line in lines if line.strip().startswith('#')])
            comment_ratio = comments / max(loc, 1)
            
            # Cyclomatic complexity (simplified)
            complexity = 1  # Base complexity
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, 
                                   ast.With, ast.Try, ast.Assert)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            # Cognitive complexity (simplified)
            cognitive = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For)):
                    cognitive += 1
                elif isinstance(node, ast.BoolOp):
                    cognitive += len(node.values) - 1
                elif isinstance(node, ast.FunctionDef):
                    cognitive += 1
            
            # Maintainability index (simplified)
            # Formula: 171 - 5.2 * ln(avg_cc) - 0.23 * ln(loc) - 16.2 * ln(avg_halstead)
            avg_cc = complexity
            avg_halstead = 20  # Simplified
            maintainability = max(0, 171 - 5.2 * (avg_cc ** 0.5) - 0.23 * (loc ** 0.5) - 16.2 * (avg_halstead ** 0.5))
            
            return ComplexityMetrics(
                cyclomatic_complexity=complexity,
                cognitive_complexity=cognitive,
                maintainability_index=maintainability,
                lines_of_code=loc,
                comment_ratio=comment_ratio
            )
            
        except SyntaxError:
            return ComplexityMetrics(1, 1, 100, 1, 0.0)
    
    def _analyze_js_complexity(self, content: str) -> ComplexityMetrics:
        """Analyze JavaScript/TypeScript code complexity using regex."""
        lines = content.split('\n')
        loc = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        # Count comments
        comments = len([line for line in lines if line.strip().startswith('//')])
        comment_ratio = comments / max(loc, 1)
        
        # Cyclomatic complexity (simplified)
        complexity = 1
        complexity += len(re.findall(r'\b(if|while|for|catch|switch)\b', content))
        complexity += len(re.findall(r'\b(&&|\|\|)\b', content))
        
        # Cognitive complexity (simplified)
        cognitive = 1
        cognitive += len(re.findall(r'\b(if|while|for|catch|switch)\b', content))
        cognitive += len(re.findall(r'\bfunction\b', content))
        
        # Maintainability index (simplified)
        maintainability = max(0, 171 - 5.2 * (complexity ** 0.5) - 0.23 * (loc ** 0.5) - 16.2 * 20)
        
        return ComplexityMetrics(
            cyclomatic_complexity=complexity,
            cognitive_complexity=cognitive,
            maintainability_index=maintainability,
            lines_of_code=loc,
            comment_ratio=comment_ratio
        )
    
    def detect_code_duplication(self, files: List[str]) -> List[Dict[str, Any]]:
        """Detect code duplication across files."""
        duplicates = []
        
        # Simple token-based duplication detection
        file_tokens = {}
        for file_path in files:
            if file_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract function definitions
                    if file_path.endswith('.py'):
                        functions = self._extract_python_functions(content)
                    else:
                        functions = self._extract_js_functions(content)
                    
                    file_tokens[file_path] = functions
                    
                except Exception as e:
                    print(f"⚠️  Error reading {file_path}: {e}")
        
        # Find duplicates
        for file1, functions1 in file_tokens.items():
            for file2, functions2 in file_tokens.items():
                if file1 < file2:  # Avoid duplicate pairs
                    for func1_name, func1_body in functions1.items():
                        for func2_name, func2_body in functions2.items():
                            if func1_body == func2_body and len(func1_body) > 50:  # Significant duplication
                                duplicates.append({
                                    'file1': file1,
                                    'file2': file2,
                                    'function1': func1_name,
                                    'function2': func2_name,
                                    'similarity': 1.0,
                                    'lines': len(func1_body.split('\n'))
                                })
        
        return duplicates
    
    def _extract_python_functions(self, content: str) -> Dict[str, str]:
        """Extract Python function definitions."""
        functions = {}
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function body
                    start = node.lineno - 1
                    end = node.end_lineno if hasattr(node, 'end_lineno') else start + 1
                    lines = content.split('\n')[start:end]
                    functions[node.name] = '\n'.join(lines)
        except SyntaxError:
            pass
        return functions
    
    def _extract_js_functions(self, content: str) -> Dict[str, str]:
        """Extract JavaScript function definitions."""
        functions = {}
        # Simple regex-based extraction
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}'
        matches = re.finditer(function_pattern, content, re.DOTALL)
        for match in matches:
            func_name = match.group(1)
            func_body = match.group(0)
            functions[func_name] = func_body
        return functions
    
    def calculate_quality_score(self, complexity: ComplexityMetrics, 
                              duplicates: List[Dict], 
                              test_coverage: float = 0.0) -> QualityMetrics:
        """Calculate overall quality score."""
        
        # Complexity score (0-1, lower is better)
        complexity_score = max(0, 1 - (complexity.cyclomatic_complexity / 20))
        
        # Duplication score (0-1, lower is better)
        duplication_score = max(0, 1 - (len(duplicates) * 0.1))
        
        # Test coverage score (0-1, higher is better)
        test_coverage_score = test_coverage / 100.0
        
        # Documentation score (0-1, higher is better)
        documentation_score = min(1.0, complexity.comment_ratio * 10)
        
        # Overall score (weighted average)
        overall_score = (
            complexity_score * 0.3 +
            duplication_score * 0.2 +
            test_coverage_score * 0.3 +
            documentation_score * 0.2
        )
        
        return QualityMetrics(
            complexity_score=complexity_score,
            duplication_score=duplication_score,
            test_coverage_score=test_coverage_score,
            documentation_score=documentation_score,
            overall_score=overall_score
        )
    
    def generate_quality_report(self, files: List[str]) -> Dict[str, Any]:
        """Generate comprehensive quality report."""
        report = {
            'files_analyzed': 0,
            'complexity_metrics': {},
            'duplication_findings': [],
            'quality_scores': {},
            'recommendations': []
        }
        
        total_complexity = 0
        high_complexity_files = []
        
        for file_path in files:
            if file_path.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                complexity = self.analyze_file_complexity(file_path)
                if complexity:
                    report['files_analyzed'] += 1
                    report['complexity_metrics'][file_path] = complexity
                    total_complexity += complexity.cyclomatic_complexity
                    
                    if complexity.cyclomatic_complexity > 10:
                        high_complexity_files.append({
                            'file': file_path,
                            'complexity': complexity.cyclomatic_complexity
                        })
        
        # Detect duplication
        report['duplication_findings'] = self.detect_code_duplication(files)
        
        # Calculate quality scores
        avg_complexity = total_complexity / max(report['files_analyzed'], 1)
        avg_metrics = ComplexityMetrics(
            cyclomatic_complexity=int(avg_complexity),
            cognitive_complexity=int(avg_complexity * 0.8),
            maintainability_index=100 - avg_complexity * 2,
            lines_of_code=0,
            comment_ratio=0.1
        )
        
        report['quality_scores'] = self.calculate_quality_score(
            avg_metrics, 
            report['duplication_findings']
        )
        
        # Generate recommendations
        if high_complexity_files:
            report['recommendations'].append(
                f"🔴 {len(high_complexity_files)} files have high complexity. Consider refactoring."
            )
        
        if report['duplication_findings']:
            report['recommendations'].append(
                f"🔄 {len(report['duplication_findings'])} code duplications detected. Consider extracting common functions."
            )
        
        if report['quality_scores'].overall_score < 0.6:
            report['recommendations'].append(
                "⚠️  Overall code quality is below recommended standards. Focus on testing and documentation."
            )
        
        return report 