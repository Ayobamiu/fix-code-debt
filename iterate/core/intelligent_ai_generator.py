"""
Intelligent AI Generator that combines RAG (CodebaseIntelligence) with AI generation.
Provides context-aware code analysis and suggestions.
"""

import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from .codebase_intelligence import CodebaseIntelligence, CodebaseContext
from .ai_code_generator import AICodeGenerator, AICodeSuggestion
from .dependency_mapper import DependencyMapper
from .error_handler import ErrorHandler
from .progress_reporter import ProgressReporter


@dataclass
class IntelligentSuggestion:
    """An intelligent suggestion with context."""
    suggestion: AICodeSuggestion
    confidence_score: float
    reasoning: str
    cross_file_impact: List[str] = None


class IntelligentAIGenerator:
    """Intelligent AI Generator that combines RAG with AI generation."""
    
    def __init__(self, error_handler=None):
        self.error_handler = error_handler or ErrorHandler()
        self.initialized = False
        self.codebase_intelligence = None
        self.ai_generator = None
        self.dependency_mapper = None
        self.directory = None
        
    def initialize_codebase(self, directory: str) -> bool:
        """Initialize the codebase intelligence system."""
        try:
            self.directory = directory
            
            # Initialize components
            self.codebase_intelligence = CodebaseIntelligence(error_handler=self.error_handler)
            self.ai_generator = AICodeGenerator()
            
            # Initialize dependency mapper with progress reporter
            progress_reporter = ProgressReporter()
            self.dependency_mapper = DependencyMapper(
                error_handler=self.error_handler,
                progress_reporter=progress_reporter
            )
            
            # Initialize codebase intelligence
            success = self.codebase_intelligence.initialize(directory)
            
            if success:
                self.initialized = True
                return True
            else:
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "initialize_intelligent_generator", "directory": directory})
            return False
    
    def generate_intelligent_refactoring(self, query: str) -> List[IntelligentSuggestion]:
        """Generate intelligent refactoring suggestions with context."""
        if not self.initialized:
            return []
        
        try:
            # Query codebase for relevant context
            context = self.codebase_intelligence.query_codebase(query, max_results=5)
            
            if not context.relevant_chunks:
                return []
            
            suggestions = []
            
            # Generate suggestions for each relevant chunk
            for chunk in context.relevant_chunks:
                if chunk.chunk_type == "function" and chunk.complexity > 3:
                    # Generate AI refactoring suggestion
                    ai_suggestion = self.ai_generator.generate_refactoring_suggestion(
                        chunk.file_path,
                        chunk.content,
                        {"cyclomatic_complexity": chunk.complexity, "lines_of_code": len(chunk.content.split('\n'))}
                    )
                    
                    if ai_suggestion:
                        # Calculate confidence based on complexity and context relevance
                        confidence = min(0.9, 0.5 + (chunk.complexity * 0.1))
                        
                        # Get cross-file impact
                        cross_file_impact = self._get_cross_file_impact(chunk, context)
                        
                        intelligent_suggestion = IntelligentSuggestion(
                            suggestion=ai_suggestion,
                            confidence_score=confidence,
                            reasoning=f"High complexity function ({chunk.complexity}) with {len(context.related_files)} related files",
                            cross_file_impact=cross_file_impact
                        )
                        
                        suggestions.append(intelligent_suggestion)
            
            return suggestions
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "generate_intelligent_refactoring", "query": query})
            return []
    
    def find_duplicate_code(self) -> List[Dict[str, Any]]:
        """Find duplicate code patterns using semantic similarity."""
        if not self.initialized:
            return []
        
        try:
            # Get all chunks from codebase intelligence
            summary = self.codebase_intelligence.get_codebase_summary()
            
            if summary["total_chunks"] == 0:
                return []
            
            # Query for similar patterns
            duplicates = []
            
            # Look for common patterns
            patterns = [
                "input validation",
                "error handling",
                "data processing",
                "utility functions",
                "configuration loading"
            ]
            
            for pattern in patterns:
                context = self.codebase_intelligence.query_codebase(pattern, max_results=10)
                
                if len(context.relevant_chunks) > 1:
                    # Group by similarity
                    grouped_chunks = self._group_similar_chunks(context.relevant_chunks)
                    
                    for group in grouped_chunks:
                        if len(group) > 1:
                            duplicate = {
                                "function_name": pattern,
                                "occurrences": len(group),
                                "files": [chunk.file_path for chunk in group],
                                "suggestion": f"Consider extracting '{pattern}' into a shared utility function"
                            }
                            duplicates.append(duplicate)
            
            return duplicates
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "find_duplicate_code"})
            return []
    
    def suggest_cross_file_refactoring(self) -> List[Dict[str, Any]]:
        """Suggest cross-file refactoring opportunities."""
        if not self.initialized:
            return []
        
        try:
            # Get codebase summary
            summary = self.codebase_intelligence.get_codebase_summary()
            
            if summary["unique_files"] < 2:
                return []
            
            opportunities = []
            
            # Look for common patterns across files
            patterns = [
                "import statements",
                "configuration",
                "logging setup",
                "database connection",
                "API client"
            ]
            
            for pattern in patterns:
                context = self.codebase_intelligence.query_codebase(pattern, max_results=15)
                
                if len(context.related_files) > 1:
                    opportunity = {
                        "pattern": pattern,
                        "files_affected": context.related_files,
                        "suggestion": f"Consider creating a shared module for {pattern}"
                    }
                    opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "suggest_cross_file_refactoring"})
            return []
    
    def generate_context_aware_tests(self, target_file: str) -> Optional[str]:
        """Generate context-aware tests for a specific file."""
        if not self.initialized:
            return None
        
        try:
            # Query codebase for context about the target file
            context = self.codebase_intelligence.query_codebase(f"test {target_file}", max_results=5)
            
            # Get the target file content
            if not os.path.exists(target_file):
                return None
            
            with open(target_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Find functions in the target file
            functions = []
            lines = file_content.split('\n')
            
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    function_name = line.split('def ')[1].split('(')[0].strip()
                    functions.append(function_name)
            
            if not functions:
                return None
            
            # Generate tests for the first function
            test_suggestion = self.ai_generator.generate_test_suggestion(
                target_file,
                file_content,
                functions[0]
            )
            
            if test_suggestion:
                return test_suggestion.ai_generated_code
            
            return None
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "generate_context_aware_tests", "target_file": target_file})
            return None
    
    def get_codebase_insights(self) -> Dict[str, Any]:
        """Get comprehensive codebase insights."""
        if not self.initialized:
            return {"summary": {"total_chunks": 0, "unique_files": 0, "functions": 0, "classes": 0, "imports": 0, "average_complexity": 0.0, "high_complexity_functions": 0}, "total_duplicates": 0, "total_opportunities": 0}
        
        try:
            # Get basic summary
            summary = self.codebase_intelligence.get_codebase_summary()
            
            # Get duplicates
            duplicates = self.find_duplicate_code()
            total_duplicates = len(duplicates)
            
            # Get cross-file opportunities
            opportunities = self.suggest_cross_file_refactoring()
            total_opportunities = len(opportunities)
            
            return {
                "summary": summary,
                "total_duplicates": total_duplicates,
                "total_opportunities": total_opportunities
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "get_codebase_insights"})
            return {"summary": {"total_chunks": 0, "unique_files": 0, "functions": 0, "classes": 0, "imports": 0, "average_complexity": 0.0, "high_complexity_functions": 0}, "total_duplicates": 0, "total_opportunities": 0}
    
    def update_context_for_file(self, file_path: str) -> bool:
        """Update context when a file changes."""
        if not self.initialized:
            return False
        
        try:
            return self.codebase_intelligence.update_context(file_path)
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "update_context_for_file", "file_path": file_path})
            return False
    
    def _get_cross_file_impact(self, chunk, context: CodebaseContext) -> List[str]:
        """Get cross-file impact for a chunk."""
        impact_files = []
        
        # Check if this function is used in other files
        if chunk.function_name:
            # Query for function usage
            usage_context = self.codebase_intelligence.query_codebase(chunk.function_name, max_results=10)
            
            for usage_chunk in usage_context.relevant_chunks:
                if usage_chunk.file_path != chunk.file_path:
                    impact_files.append(usage_chunk.file_path)
        
        return list(set(impact_files))
    
    def _group_similar_chunks(self, chunks) -> List[List]:
        """Group chunks by similarity."""
        if len(chunks) <= 1:
            return []
        
        groups = []
        processed = set()
        
        for i, chunk1 in enumerate(chunks):
            if i in processed:
                continue
            
            group = [chunk1]
            processed.add(i)
            
            for j, chunk2 in enumerate(chunks[i+1:], i+1):
                if j in processed:
                    continue
                
                # Simple similarity check (could be enhanced with embeddings)
                if (chunk1.function_name == chunk2.function_name and 
                    chunk1.chunk_type == chunk2.chunk_type):
                    group.append(chunk2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
