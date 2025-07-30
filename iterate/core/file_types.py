"""
File type detection and categorization for code analysis.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from .error_handler import ErrorHandler, ErrorSeverity


class FileCategory(Enum):
    """Categories of files."""
    CODE = "code"
    CONFIG = "config"
    DOCUMENTATION = "documentation"
    BUILD = "build"
    TEST = "test"
    ASSET = "asset"
    BINARY = "binary"
    UNKNOWN = "unknown"


class Language(Enum):
    """Supported programming languages."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSX = "jsx"
    TSX = "tsx"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    XML = "xml"
    HTML = "html"
    CSS = "css"
    SCSS = "scss"
    SASS = "sass"
    LESS = "less"
    MARKDOWN = "markdown"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    C = "c"
    CPP = "cpp"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    SCALA = "scala"
    SHELL = "shell"
    BATCH = "batch"
    POWERSHELL = "powershell"
    SQL = "sql"
    UNKNOWN = "unknown"


class FileTypeDetector:
    """Detects file types and categorizes them for analysis."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        
        # File extensions mapped to languages
        self.language_extensions = {
            # Python
            ".py": Language.PYTHON,
            ".pyx": Language.PYTHON,
            ".pyi": Language.PYTHON,
            
            # JavaScript/TypeScript
            ".js": Language.JAVASCRIPT,
            ".jsx": Language.JSX,
            ".ts": Language.TYPESCRIPT,
            ".tsx": Language.TSX,
            ".mjs": Language.JAVASCRIPT,
            ".cjs": Language.JAVASCRIPT,
            
            # Web
            ".html": Language.HTML,
            ".htm": Language.HTML,
            ".css": Language.CSS,
            ".scss": Language.SCSS,
            ".sass": Language.SASS,
            ".less": Language.LESS,
            
            # Configuration
            ".json": Language.JSON,
            ".yaml": Language.YAML,
            ".yml": Language.YAML,
            ".toml": Language.TOML,
            ".xml": Language.XML,
            
            # Documentation
            ".md": Language.MARKDOWN,
            ".markdown": Language.MARKDOWN,
            ".rst": Language.MARKDOWN,
            
            # Other languages
            ".rs": Language.RUST,
            ".go": Language.GO,
            ".java": Language.JAVA,
            ".c": Language.C,
            ".cpp": Language.CPP,
            ".cc": Language.CPP,
            ".cxx": Language.CPP,
            ".h": Language.C,
            ".hpp": Language.CPP,
            ".cs": Language.CSHARP,
            ".php": Language.PHP,
            ".rb": Language.RUBY,
            ".swift": Language.SWIFT,
            ".kt": Language.KOTLIN,
            ".scala": Language.SCALA,
            ".sql": Language.SQL,
            
            # Shell scripts
            ".sh": Language.SHELL,
            ".bash": Language.SHELL,
            ".zsh": Language.SHELL,
            ".fish": Language.SHELL,
            ".bat": Language.BATCH,
            ".cmd": Language.BATCH,
            ".ps1": Language.POWERSHELL,
        }
        
        # File categories based on extensions
        self.category_extensions = {
            # Code files
            **{ext: FileCategory.CODE for ext in self.language_extensions.keys()},
            
            # Configuration files
            ".env": FileCategory.CONFIG,
            ".ini": FileCategory.CONFIG,
            ".cfg": FileCategory.CONFIG,
            ".conf": FileCategory.CONFIG,
            ".config": FileCategory.CONFIG,
            ".properties": FileCategory.CONFIG,
            ".gitignore": FileCategory.CONFIG,
            ".gitattributes": FileCategory.CONFIG,
            ".editorconfig": FileCategory.CONFIG,
            ".eslintrc": FileCategory.CONFIG,
            ".prettierrc": FileCategory.CONFIG,
            ".babelrc": FileCategory.CONFIG,
            ".browserslistrc": FileCategory.CONFIG,
            ".npmrc": FileCategory.CONFIG,
            ".yarnrc": FileCategory.CONFIG,
            ".dockerignore": FileCategory.CONFIG,
            ".dockerfile": FileCategory.CONFIG,
            "Dockerfile": FileCategory.CONFIG,
            "docker-compose.yml": FileCategory.CONFIG,
            "docker-compose.yaml": FileCategory.CONFIG,
            
            # Build files
            ".lock": FileCategory.BUILD,
            "package.json": FileCategory.BUILD,
            "package-lock.json": FileCategory.BUILD,
            "yarn.lock": FileCategory.BUILD,
            "pnpm-lock.yaml": FileCategory.BUILD,
            "requirements.txt": FileCategory.BUILD,
            "Pipfile": FileCategory.BUILD,
            "poetry.lock": FileCategory.BUILD,
            "setup.py": FileCategory.BUILD,
            "pyproject.toml": FileCategory.BUILD,
            "Cargo.toml": FileCategory.BUILD,
            "Cargo.lock": FileCategory.BUILD,
            "go.mod": FileCategory.BUILD,
            "go.sum": FileCategory.BUILD,
            "pom.xml": FileCategory.BUILD,
            "build.gradle": FileCategory.BUILD,
            "build.sbt": FileCategory.BUILD,
            "composer.json": FileCategory.BUILD,
            "composer.lock": FileCategory.BUILD,
            "Gemfile": FileCategory.BUILD,
            "Gemfile.lock": FileCategory.BUILD,
            "Podfile": FileCategory.BUILD,
            "Podfile.lock": FileCategory.BUILD,
            
            # Test files
            ".test.js": FileCategory.TEST,
            ".test.ts": FileCategory.TEST,
            ".test.jsx": FileCategory.TEST,
            ".test.tsx": FileCategory.TEST,
            ".spec.js": FileCategory.TEST,
            ".spec.ts": FileCategory.TEST,
            ".spec.jsx": FileCategory.TEST,
            ".spec.tsx": FileCategory.TEST,
            "_test.py": FileCategory.TEST,
            "test_": FileCategory.TEST,
            ".test.py": FileCategory.TEST,
            ".spec.py": FileCategory.TEST,
            
            # Documentation
            ".txt": FileCategory.DOCUMENTATION,
            ".pdf": FileCategory.DOCUMENTATION,
            ".doc": FileCategory.DOCUMENTATION,
            ".docx": FileCategory.DOCUMENTATION,
            ".rtf": FileCategory.DOCUMENTATION,
            
            # Assets
            ".png": FileCategory.ASSET,
            ".jpg": FileCategory.ASSET,
            ".jpeg": FileCategory.ASSET,
            ".gif": FileCategory.ASSET,
            ".svg": FileCategory.ASSET,
            ".ico": FileCategory.ASSET,
            ".woff": FileCategory.ASSET,
            ".woff2": FileCategory.ASSET,
            ".ttf": FileCategory.ASSET,
            ".eot": FileCategory.ASSET,
            ".mp3": FileCategory.ASSET,
            ".mp4": FileCategory.ASSET,
            ".avi": FileCategory.ASSET,
            ".mov": FileCategory.ASSET,
            ".wav": FileCategory.ASSET,
            ".flac": FileCategory.ASSET,
            ".zip": FileCategory.ASSET,
            ".tar": FileCategory.ASSET,
            ".gz": FileCategory.ASSET,
            ".rar": FileCategory.ASSET,
            ".7z": FileCategory.ASSET,
            
            # Binary files
            ".exe": FileCategory.BINARY,
            ".dll": FileCategory.BINARY,
            ".so": FileCategory.BINARY,
            ".dylib": FileCategory.BINARY,
            ".o": FileCategory.BINARY,
            ".obj": FileCategory.BINARY,
            ".class": FileCategory.BINARY,
            ".jar": FileCategory.BINARY,
            ".war": FileCategory.BINARY,
            ".ear": FileCategory.BINARY,
            ".apk": FileCategory.BINARY,
            ".ipa": FileCategory.BINARY,
            ".deb": FileCategory.BINARY,
            ".rpm": FileCategory.BINARY,
            ".msi": FileCategory.BINARY,
            ".dmg": FileCategory.BINARY,
            ".pkg": FileCategory.BINARY,
        }
        
        # Maximum file size for text analysis (10MB)
        self.max_text_file_size = 10 * 1024 * 1024
        
        # Binary file signatures (first few bytes)
        self.binary_signatures = {
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'\xff\xd8\xff': 'JPEG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'PK\x03\x04': 'ZIP',
            b'PK\x05\x06': 'ZIP',
            b'PK\x07\x08': 'ZIP',
            b'\x1f\x8b\x08': 'GZIP',
            b'%PDF': 'PDF',
            b'MZ': 'EXE',
            b'\x7fELF': 'ELF',
            b'\xfe\xed\xfa\xce': 'MACHO',
            b'\xce\xfa\xed\xfe': 'MACHO',
        }
    
    def detect_file_type(self, file_path: str) -> Tuple[Language, FileCategory]:
        """
        Detect the language and category of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (Language, FileCategory)
        """
        try:
            path = Path(file_path)
            filename = path.name.lower()
            
            # Check by extension first
            extension = path.suffix.lower()
            if extension in self.language_extensions:
                language = self.language_extensions[extension]
                category = self.category_extensions.get(extension, FileCategory.CODE)
                return language, category
            
            # Check by filename (for files without extensions)
            if filename in self.category_extensions:
                category = self.category_extensions[filename]
                return Language.UNKNOWN, category
            
            # Check for test files by pattern
            if self._is_test_file(filename):
                return Language.UNKNOWN, FileCategory.TEST
            
            # Check if it's a binary file
            if self._is_binary_file(file_path):
                return Language.UNKNOWN, FileCategory.BINARY
            
            # Default to unknown
            return Language.UNKNOWN, FileCategory.UNKNOWN
            
        except Exception as e:
            self.error_handler.handle_error(
                f"Error detecting file type for {file_path}: {str(e)}",
                ErrorSeverity.WARNING
            )
            return Language.UNKNOWN, FileCategory.UNKNOWN
    
    def _is_test_file(self, filename: str) -> bool:
        """Check if filename indicates a test file."""
        test_patterns = [
            'test_', '_test', '.test.', '.spec.',
            'test.', 'spec.', 'tests/', 'specs/'
        ]
        return any(pattern in filename for pattern in test_patterns)
    
    def _is_binary_file(self, file_path: str) -> bool:
        """Check if file is binary by examining its content."""
        try:
            # Check file size first
            if os.path.getsize(file_path) > self.max_text_file_size:
                return True
            
            # Read first 8 bytes to check for binary signatures
            with open(file_path, 'rb') as f:
                header = f.read(8)
                
                # Check for binary signatures
                for signature, _ in self.binary_signatures.items():
                    if header.startswith(signature):
                        return True
                
                # Check for null bytes (common in binary files)
                if b'\x00' in header:
                    return True
                    
                return False
                
        except Exception as e:
            self.error_handler.handle_error(
                f"Error checking if file is binary {file_path}: {str(e)}",
                ErrorSeverity.WARNING
            )
            return False
    
    def is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file suitable for analysis."""
        language, category = self.detect_file_type(file_path)
        return category == FileCategory.CODE
    
    def is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        language, category = self.detect_file_type(file_path)
        return category == FileCategory.CONFIG
    
    def is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        language, category = self.detect_file_type(file_path)
        return category == FileCategory.TEST
    
    def get_supported_languages(self) -> Set[Language]:
        """Get set of supported programming languages."""
        return set(self.language_extensions.values())
    
    def get_language_by_extension(self, extension: str) -> Optional[Language]:
        """Get language by file extension."""
        return self.language_extensions.get(extension.lower())
    
    def get_extensions_by_language(self, language: Language) -> List[str]:
        """Get all extensions for a specific language."""
        return [ext for ext, lang in self.language_extensions.items() if lang == language]
    
    def filter_code_files(self, file_paths: List[str]) -> List[str]:
        """Filter list of files to only include code files."""
        return [path for path in file_paths if self.is_code_file(path)]
    
    def categorize_files(self, file_paths: List[str]) -> Dict[FileCategory, List[str]]:
        """Categorize files by their type."""
        categories = {}
        for path in file_paths:
            _, category = self.detect_file_type(path)
            if category not in categories:
                categories[category] = []
            categories[category].append(path)
        return categories
    
    def get_file_stats(self, file_paths: List[str]) -> Dict:
        """Get statistics about file types in a list."""
        stats = {
            'total_files': len(file_paths),
            'by_language': {},
            'by_category': {},
            'code_files': [],
            'config_files': [],
            'test_files': [],
            'other_files': []
        }
        
        for path in file_paths:
            language, category = self.detect_file_type(path)
            
            # Count by language
            lang_name = language.value
            if lang_name not in stats['by_language']:
                stats['by_language'][lang_name] = 0
            stats['by_language'][lang_name] += 1
            
            # Count by category
            cat_name = category.value
            if cat_name not in stats['by_category']:
                stats['by_category'][cat_name] = 0
            stats['by_category'][cat_name] += 1
            
            # Categorize files
            if category == FileCategory.CODE:
                stats['code_files'].append(path)
            elif category == FileCategory.CONFIG:
                stats['config_files'].append(path)
            elif category == FileCategory.TEST:
                stats['test_files'].append(path)
            else:
                stats['other_files'].append(path)
        
        return stats 