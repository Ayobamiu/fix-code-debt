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
        """Find duplicate code patterns using semantic similarity and return structured data."""
        if not self.initialized:
            return []
        
        try:
            # Get all chunks from codebase intelligence
            summary = self.codebase_intelligence.get_codebase_summary()
            
            if summary["total_chunks"] == 0:
                return []
            
            # Query for similar patterns with more specific searches
            duplicates = []
            duplicate_id = 1
            
            # More specific patterns for better detection
            patterns = [
                "input validation",
                "error handling", 
                "data processing",
                "utility functions",
                "configuration loading",
                "file operations",
                "logging setup",
                "database connection",
                "API client",
                "data transformation",
                "formatting functions",
                "parsing logic"
            ]
            
            for pattern in patterns:
                context = self.codebase_intelligence.query_codebase(pattern, max_results=15)
                
                if len(context.relevant_chunks) > 1:
                    # Group by similarity
                    grouped_chunks = self._group_similar_chunks(context.relevant_chunks)
                    
                    for group in grouped_chunks:
                        if len(group) > 1:
                            # Calculate similarity score
                            similarity_score = self._calculate_similarity_score(group)
                            
                            # Determine severity based on occurrence count and similarity
                            severity = self._determine_severity(len(group), similarity_score)
                            
                            # Get refactoring type
                            refactoring_type = self._determine_refactoring_type(group)
                            
                            # Estimate effort
                            estimated_effort = self._estimate_effort(len(group), similarity_score)
                            
                            # Create structured duplicate entry
                            duplicate = {
                                "id": f"dup_{duplicate_id:03d}",
                                "type": "duplicate_code",
                                "severity": severity,
                                "description": f"{pattern.title()} logic duplicated across {len(group)} locations",
                                "pattern": pattern,
                                "occurrence_count": len(group),
                                "similarity_score": similarity_score,
                                "target_files": self._create_target_files_info(group),
                                "refactoring_type": refactoring_type,
                                "suggestion": self._generate_refactoring_suggestion(pattern, len(group)),
                                "estimated_effort": estimated_effort,
                                "impact": self._assess_impact(len(group), similarity_score),
                                "code_snippets": self._extract_code_snippets(group)
                            }
                            
                            duplicates.append(duplicate)
                            duplicate_id += 1
            
            return duplicates
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "find_duplicate_code"})
            return []
    
    def _calculate_similarity_score(self, chunks) -> float:
        """Calculate similarity score between chunks (0.0 to 1.0)."""
        if len(chunks) < 2:
            return 0.0
        
        # Simple similarity based on function names and types
        # In a real implementation, you'd use embeddings comparison
        base_score = 0.7  # Base similarity for semantic matches
        
        # Boost score if function names are identical
        function_names = [chunk.function_name for chunk in chunks if chunk.function_name]
        if len(set(function_names)) == 1:
            base_score += 0.2
        
        # Boost score if chunk types are identical
        chunk_types = [chunk.chunk_type for chunk in chunks]
        if len(set(chunk_types)) == 1:
            base_score += 0.1
        
        return min(1.0, base_score)
    
    def _determine_severity(self, occurrence_count: int, similarity_score: float) -> str:
        """Determine severity level based on occurrence count and similarity."""
        if occurrence_count >= 5 or similarity_score >= 0.9:
            return "critical"
        elif occurrence_count >= 3 or similarity_score >= 0.8:
            return "high"
        elif occurrence_count >= 2 or similarity_score >= 0.7:
            return "medium"
        else:
            return "low"
    
    def _determine_refactoring_type(self, chunks) -> str:
        """Determine the best refactoring approach."""
        chunk_types = [chunk.chunk_type for chunk in chunks]
        
        if "function" in chunk_types:
            return "extract_method"
        elif "class" in chunk_types:
            return "extract_class"
        elif "import" in chunk_types:
            return "consolidate_imports"
        else:
            return "extract_utility"
    
    def _estimate_effort(self, occurrence_count: int, similarity_score: float) -> str:
        """Estimate refactoring effort."""
        if occurrence_count <= 2:
            return "1-2 hours"
        elif occurrence_count <= 4:
            return "3-5 hours"
        elif occurrence_count <= 6:
            return "6-8 hours"
        else:
            return "1-2 days"
    
    def _assess_impact(self, occurrence_count: int, similarity_score: float) -> str:
        """Assess the impact of refactoring."""
        if occurrence_count >= 5:
            return "High: Significant maintenance reduction, improved consistency"
        elif occurrence_count >= 3:
            return "Medium: Reduced duplication, easier testing"
        else:
            return "Low: Minor improvement in code organization"
    
    def _create_target_files_info(self, chunks) -> List[Dict[str, Any]]:
        """Create structured information about target files."""
        target_files = []
        
        for chunk in chunks:
            file_info = {
                "file_path": chunk.file_path,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "function_name": chunk.function_name or "unknown",
                "chunk_type": chunk.chunk_type,
                "complexity": getattr(chunk, 'complexity', 0)
            }
            target_files.append(file_info)
        
        return target_files
    
    def _extract_code_snippets(self, chunks) -> List[Dict[str, Any]]:
        """Extract code snippets for context."""
        snippets = []
        
        for chunk in chunks:
            # Get first few lines of the chunk for context
            lines = chunk.content.split('\n')
            snippet_lines = lines[:min(5, len(lines))]  # First 5 lines
            
            snippet = {
                "file_path": chunk.file_path,
                "function_name": chunk.function_name or "unknown",
                "code_preview": '\n'.join(snippet_lines),
                "total_lines": len(lines)
            }
            snippets.append(snippet)
        
        return snippets
    
    def _generate_refactoring_suggestion(self, pattern: str, occurrence_count: int) -> str:
        """Generate specific refactoring suggestions."""
        suggestions = {
            "input validation": f"Create shared validation module 'iterate/utils/validation.py' with common validation functions",
            "error handling": f"Extract error handling logic into 'iterate/utils/error_utils.py' for consistent error management",
            "data processing": f"Create data processing utilities in 'iterate/utils/data_utils.py' to eliminate duplication",
            "utility functions": f"Move common utilities to 'iterate/utils/common.py' for better reusability",
            "configuration loading": f"Create centralized configuration management in 'iterate/config/loader.py'",
            "file operations": f"Extract file operations to 'iterate/utils/file_utils.py' for consistent file handling",
            "logging setup": f"Create shared logging configuration in 'iterate/utils/logging_config.py'",
            "database connection": f"Implement connection pooling in 'iterate/database/connection.py'",
            "API client": f"Create reusable API client base class in 'iterate/api/base_client.py'",
            "data transformation": f"Extract transformation logic to 'iterate/utils/transformers.py'",
            "formatting functions": f"Create formatting utilities in 'iterate/utils/formatters.py'",
            "parsing logic": f"Extract parsing logic to 'iterate/utils/parsers.py'"
        }
        
        return suggestions.get(pattern, f"Consider extracting '{pattern}' into a shared utility module")
    
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
        print(f"🔍 Debug: intelligent_generator.get_codebase_insights called, initialized={self.initialized}")
        if not self.initialized:
            print("🔍 Debug: intelligent_generator not initialized, returning empty insights")
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
