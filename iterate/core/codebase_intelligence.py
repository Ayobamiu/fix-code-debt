"""
Real Codebase Intelligence system using ChromaDB and embeddings.
Provides semantic search and code understanding capabilities.
"""

import os
import ast
import re
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

# Fix tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from .error_handler import ErrorHandler
from .file_finder import FileFinder
from .dependency_mapper import DependencyMapper
from .progress_reporter import ProgressReporter


@dataclass
class CodeChunk:
    """A chunk of code with metadata."""
    id: str
    content: str
    file_path: str
    chunk_type: str  # 'function', 'class', 'module', 'import'
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    complexity: int = 0
    dependencies: List[str] = None


@dataclass
class CodebaseContext:
    """Context for code analysis."""
    relevant_chunks: List[CodeChunk]
    related_files: List[str]
    dependencies: Dict[str, Any]
    patterns: List[str]
    suggestions: List[str]


class CodebaseIntelligence:
    """Real codebase intelligence system using ChromaDB and embeddings."""
    
    def __init__(self, error_handler=None):
        self.error_handler = error_handler or ErrorHandler()
        self.initialized = False
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.file_finder = None
        self.dependency_mapper = None
        self.directory = None
        self.chunks = []
        
    def initialize(self, directory: str) -> bool:
        """Initialize the codebase intelligence system."""
        try:
            print("🧠 Initializing Codebase Intelligence...")
            self.directory = directory
            
            # Initialize components
            progress_reporter = ProgressReporter()
            self.file_finder = FileFinder(error_handler=self.error_handler, progress_reporter=progress_reporter)
            self.dependency_mapper = DependencyMapper(error_handler=self.error_handler, progress_reporter=progress_reporter)
            
            # Load embedding model
            print("📊 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize ChromaDB
            print("🗄️  Setting up vector database...")
            self.chroma_client = chromadb.PersistentClient(path="./.iterate_cache/chromadb")
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection("code_chunks")
                print("✅ Using existing code chunks collection")
            except:
                self.collection = self.chroma_client.create_collection("code_chunks")
                print("✅ Created new code chunks collection")
            
            # Process codebase
            print("🔍 Processing codebase for intelligence...")
            success = self._process_codebase()
            
            if success:
                self.initialized = True
                print("✅ Codebase Intelligence initialized successfully!")
                return True
            else:
                print("❌ Failed to process codebase")
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "initialize", "directory": directory})
            return False
    
    def _process_codebase(self) -> bool:
        """Process the entire codebase into searchable chunks."""
        try:
            # Find all code files
            files = self.file_finder.find_files_and_folders(
                self.directory, 
                max_depth=10
            )
            
            if not files or 'files' not in files:
                print("⚠️  No code files found")
                return False
            
            # Filter for code files
            all_files = files.get('files', [])
            code_files = [f for f in all_files if self._should_process_file(f)]
            
            if not code_files:
                print("⚠️  No code files found")
                return False
            
            print(f"📁 Found {len(code_files)} code files")
            
            # Process each file
            for file_path in code_files:
                self._process_file(file_path)
            
            print(f"✅ Processed {len(self.chunks)} code chunks")
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "process_codebase", "directory": self.directory})
            return False
    
    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        # Skip binary files, large files, and non-code files
        if not os.path.isfile(file_path):
            return False
        
        # Check file size (skip files larger than 1MB)
        if os.path.getsize(file_path) > 1024 * 1024:
            return False
        
        # Check if it's a code file
        ext = Path(file_path).suffix.lower()
        return ext in ['.py', '.js', '.jsx', '.ts', '.tsx']
    
    def _process_file(self, file_path: str):
        """Process a single file into chunks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ext = Path(file_path).suffix.lower()
            
            if ext == '.py':
                chunks = self._parse_python_file(file_path, content)
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                chunks = self._parse_js_ts_file(file_path, content)
            else:
                return
            
            # Store chunks in vector database
            self._store_chunks(chunks)
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "process_file", "file_path": file_path})
    
    def _parse_python_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Parse Python file into chunks."""
        chunks = []
        
        try:
            tree = ast.parse(content)
            
            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    chunk = self._create_function_chunk(file_path, content, node)
                    chunks.append(chunk)
                
                elif isinstance(node, ast.ClassDef):
                    chunk = self._create_class_chunk(file_path, content, node)
                    chunks.append(chunk)
            
            # Extract imports
            import_chunk = self._create_import_chunk(file_path, content, tree)
            if import_chunk:
                chunks.append(import_chunk)
            
            # Extract module-level code
            module_chunk = self._create_module_chunk(file_path, content, tree)
            if module_chunk:
                chunks.append(module_chunk)
                
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "parse_python_file", "file_path": file_path})
        
        return chunks
    
    def _parse_js_ts_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Parse JavaScript/TypeScript file into chunks."""
        chunks = []
        
        try:
            # Extract functions using regex
            function_pattern = r'(?:function\s+(\w+)\s*\([^)]*\)\s*\{[^}]*\}|const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{[^}]*\})'
            functions = re.finditer(function_pattern, content, re.DOTALL)
            
            for match in functions:
                function_name = match.group(1) or match.group(2)
                function_code = match.group(0)
                
                # Create unique ID with position
                chunk_id = f"{file_path}:{function_name}:{match.start()}-{match.end()}"
                
                chunk = CodeChunk(
                    id=chunk_id,
                    content=function_code,
                    file_path=file_path,
                    chunk_type="function",
                    function_name=function_name,
                    line_start=content[:match.start()].count('\n') + 1,
                    line_end=content[:match.end()].count('\n') + 1
                )
                chunks.append(chunk)
            
            # Extract classes
            class_pattern = r'class\s+(\w+)\s*\{[^}]*\}'
            classes = re.finditer(class_pattern, content, re.DOTALL)
            
            for match in classes:
                class_name = match.group(1)
                class_code = match.group(0)
                
                # Create unique ID with position
                chunk_id = f"{file_path}:{class_name}:{match.start()}-{match.end()}"
                
                chunk = CodeChunk(
                    id=chunk_id,
                    content=class_code,
                    file_path=file_path,
                    chunk_type="class",
                    class_name=class_name,
                    line_start=content[:match.start()].count('\n') + 1,
                    line_end=content[:match.end()].count('\n') + 1
                )
                chunks.append(chunk)
                
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "parse_js_ts_file", "file_path": file_path})
        
        return chunks
    
    def _create_function_chunk(self, file_path: str, content: str, node: ast.FunctionDef) -> CodeChunk:
        """Create a chunk for a Python function."""
        # Get function code
        lines = content.split('\n')
        function_lines = lines[node.lineno - 1:node.end_lineno]
        function_code = '\n'.join(function_lines)
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Create unique ID with line numbers
        chunk_id = f"{file_path}:{node.name}:{node.lineno}-{node.end_lineno}"
        
        return CodeChunk(
            id=chunk_id,
            content=function_code,
            file_path=file_path,
            chunk_type="function",
            function_name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno,
            complexity=complexity
        )
    
    def _create_class_chunk(self, file_path: str, content: str, node: ast.ClassDef) -> CodeChunk:
        """Create a chunk for a Python class."""
        lines = content.split('\n')
        class_lines = lines[node.lineno - 1:node.end_lineno]
        class_code = '\n'.join(class_lines)
        
        # Create unique ID with line numbers
        chunk_id = f"{file_path}:{node.name}:{node.lineno}-{node.end_lineno}"
        
        return CodeChunk(
            id=chunk_id,
            content=class_code,
            file_path=file_path,
            chunk_type="class",
            class_name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno
        )
    
    def _create_import_chunk(self, file_path: str, content: str, tree: ast.AST) -> Optional[CodeChunk]:
        """Create a chunk for imports."""
        import_lines = []
        lines = content.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                import_lines.extend(lines[node.lineno - 1:node.end_lineno])
        
        if import_lines:
            # Create unique ID for imports
            chunk_id = f"{file_path}:imports:{hash(''.join(import_lines)) % 10000}"
            
            return CodeChunk(
                id=chunk_id,
                content='\n'.join(import_lines),
                file_path=file_path,
                chunk_type="import"
            )
        
        return None
    
    def _create_module_chunk(self, file_path: str, content: str, tree: ast.AST) -> Optional[CodeChunk]:
        """Create a chunk for module-level code."""
        # Find module-level code (not in functions or classes)
        lines = content.split('\n')
        module_lines = []
        
        for i, line in enumerate(lines, 1):
            # Check if this line is at module level
            try:
                # Create a simple AST for this line
                line_tree = ast.parse(line)
                if line_tree.body and not any(isinstance(node, (ast.FunctionDef, ast.ClassDef)) for node in ast.walk(line_tree)):
                    module_lines.append(line)
            except:
                # If line can't be parsed, skip it
                pass
        
        if module_lines:
            # Create unique ID for module code
            chunk_id = f"{file_path}:module:{hash(''.join(module_lines)) % 10000}"
            
            return CodeChunk(
                id=chunk_id,
                content='\n'.join(module_lines),
                file_path=file_path,
                chunk_type="module"
            )
        
        return None
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _store_chunks(self, chunks: List[CodeChunk]):
        """Store chunks in ChromaDB."""
        if not chunks:
            return
        
        try:
            # Prepare data for ChromaDB
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [
                {
                    "file_path": chunk.file_path,
                    "chunk_type": chunk.chunk_type,
                    "function_name": chunk.function_name or "",
                    "class_name": chunk.class_name or "",
                    "line_start": chunk.line_start,
                    "line_end": chunk.line_end,
                    "complexity": chunk.complexity
                }
                for chunk in chunks
            ]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            # Store chunks in memory for quick access
            self.chunks.extend(chunks)
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "store_chunks", "chunk_count": len(chunks)})
    
    def query_codebase(self, query: str, max_results: int = 10) -> CodebaseContext:
        """Query the codebase for relevant code chunks."""
        if not self.initialized:
            return CodebaseContext([], [], {}, [], [])
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=max_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to CodeChunk objects
            relevant_chunks = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                
                chunk = CodeChunk(
                    id=results['ids'][0][i],
                    content=doc,
                    file_path=metadata['file_path'],
                    chunk_type=metadata['chunk_type'],
                    function_name=metadata['function_name'] or None,
                    class_name=metadata['class_name'] or None,
                    line_start=metadata['line_start'],
                    line_end=metadata['line_end'],
                    complexity=metadata['complexity']
                )
                relevant_chunks.append(chunk)
            
            # Get related files
            related_files = list(set(chunk.file_path for chunk in relevant_chunks))
            
            # Get dependencies
            dependencies = self._get_dependencies_for_files(related_files)
            
            # Generate patterns and suggestions
            patterns = self._extract_patterns(relevant_chunks)
            suggestions = self._generate_suggestions(relevant_chunks, query)
            
            return CodebaseContext(
                relevant_chunks=relevant_chunks,
                related_files=related_files,
                dependencies=dependencies,
                patterns=patterns,
                suggestions=suggestions
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "query_codebase", "query": query})
            return CodebaseContext([], [], {}, [], [])
    
    def _get_dependencies_for_files(self, files: List[str]) -> Dict[str, Any]:
        """Get dependencies for the given files."""
        try:
            dependencies = {}
            for file_path in files:
                if os.path.exists(file_path):
                    file_deps = self.dependency_mapper.analyze_file(file_path)
                    dependencies[file_path] = file_deps
            return dependencies
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "get_dependencies", "files": files})
            return {}
    
    def _extract_patterns(self, chunks: List[CodeChunk]) -> List[str]:
        """Extract common patterns from chunks."""
        patterns = []
        
        # Look for common function names
        function_names = [chunk.function_name for chunk in chunks if chunk.function_name]
        if len(function_names) > 1:
            patterns.append(f"Multiple functions: {', '.join(function_names)}")
        
        # Look for common file patterns
        file_paths = [chunk.file_path for chunk in chunks]
        if len(set(file_paths)) > 1:
            patterns.append(f"Cross-file references: {len(set(file_paths))} files")
        
        # Look for complexity patterns
        high_complexity = [chunk for chunk in chunks if chunk.complexity > 5]
        if high_complexity:
            patterns.append(f"High complexity functions: {len(high_complexity)} found")
        
        return patterns
    
    def _generate_suggestions(self, chunks: List[CodeChunk], query: str) -> List[str]:
        """Generate suggestions based on chunks and query."""
        suggestions = []
        
        # Suggest refactoring for high complexity functions
        high_complexity = [chunk for chunk in chunks if chunk.complexity > 5]
        if high_complexity:
            suggestions.append(f"Consider refactoring {len(high_complexity)} high complexity functions")
        
        # Suggest consolidation for similar functions
        function_names = [chunk.function_name for chunk in chunks if chunk.function_name]
        if len(set(function_names)) < len(function_names):
            suggestions.append("Consider consolidating similar functions")
        
        # Suggest documentation for functions without docstrings
        functions_without_docs = [chunk for chunk in chunks if chunk.chunk_type == "function" and '"""' not in chunk.content and "'''" not in chunk.content]
        if functions_without_docs:
            suggestions.append(f"Add documentation to {len(functions_without_docs)} functions")
        
        return suggestions
    
    def update_context(self, file_path: str) -> bool:
        """Update context when a file changes."""
        try:
            # Remove old chunks for this file
            self._remove_file_chunks(file_path)
            
            # Process the updated file
            if self._should_process_file(file_path):
                self._process_file(file_path)
            
            return True
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "update_context", "file_path": file_path})
            return False
    
    def _remove_file_chunks(self, file_path: str):
        """Remove chunks for a specific file."""
        try:
            # Get all chunks for this file
            results = self.collection.get(
                where={"file_path": file_path}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
            
            # Remove from memory
            self.chunks = [chunk for chunk in self.chunks if chunk.file_path != file_path]
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "remove_file_chunks", "file_path": file_path})
    
    def get_codebase_summary(self) -> Dict[str, Any]:
        """Get a summary of the codebase."""
        if not self.initialized:
            return {"total_chunks": 0, "unique_files": 0, "functions": 0, "classes": 0, "imports": 0, "average_complexity": 0.0, "high_complexity_functions": 0}
        
        try:
            # Get all chunks
            results = self.collection.get()
            
            if not results['ids']:
                return {"total_chunks": 0, "unique_files": 0, "functions": 0, "classes": 0, "imports": 0, "average_complexity": 0.0, "high_complexity_functions": 0}
            
            total_chunks = len(results['ids'])
            unique_files = len(set(metadata['file_path'] for metadata in results['metadatas']))
            
            functions = len([m for m in results['metadatas'] if m['chunk_type'] == 'function'])
            classes = len([m for m in results['metadatas'] if m['chunk_type'] == 'class'])
            imports = len([m for m in results['metadatas'] if m['chunk_type'] == 'import'])
            
            complexities = [m['complexity'] for m in results['metadatas'] if m['complexity'] > 0]
            average_complexity = sum(complexities) / len(complexities) if complexities else 0.0
            high_complexity_functions = len([c for c in complexities if c > 5])
            
            return {
                "total_chunks": total_chunks,
                "unique_files": unique_files,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "average_complexity": round(average_complexity, 2),
                "high_complexity_functions": high_complexity_functions
            }
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "get_codebase_summary"})
            return {"total_chunks": 0, "unique_files": 0, "functions": 0, "classes": 0, "imports": 0, "average_complexity": 0.0, "high_complexity_functions": 0}
