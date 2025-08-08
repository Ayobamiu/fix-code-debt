# 🧠 Codebase Intelligence System

A **RAG-based code analysis tool** that understands your codebase and provides intelligent suggestions for improvement.

## 🎯 What This Project Does

This tool uses **Retrieval-Augmented Generation (RAG)** to analyze codebases and provide intelligent insights:

- **🔍 Code Parsing**: Parses Python, JavaScript, TypeScript files with AST analysis
- **🧠 Vector Database**: Stores code embeddings for semantic search
- **📊 Code Insights**: Analyzes functions, classes, complexity, and dependencies
- **🔄 Duplicate Detection**: Finds similar code patterns across files
- **🎯 Refactoring Suggestions**: Identifies cross-file refactoring opportunities
- **🧪 Test Generation**: Creates context-aware tests based on your codebase
- **🤖 AI Integration**: Provides intelligent code improvement suggestions

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd fix-code-debt

# Install dependencies
pip install sentence-transformers chromadb numpy
```

### Basic Usage

```bash
# Initialize intelligence system
python3 -m iterate.cli . --intelligence

# Get codebase insights
python3 -m iterate.cli . --codebase-insights

# Find duplicate code patterns
python3 -m iterate.cli . --find-duplicates

# Analyze cross-file refactoring opportunities
python3 -m iterate.cli . --cross-file-refactor
```

## 📋 Available Commands

### Core Features

```bash
# Initialize the intelligence system
python3 -m iterate.cli <directory> --intelligence

# Get comprehensive codebase insights
python3 -m iterate.cli <directory> --codebase-insights

# Find duplicate code patterns
python3 -m iterate.cli <directory> --find-duplicates

# Suggest cross-file refactoring opportunities
python3 -m iterate.cli <directory> --cross-file-refactor

# Generate intelligent refactoring suggestions for a specific file
python3 -m iterate.cli <directory> --intelligent-refactor <file_path>

# Generate context-aware tests for a file
python3 -m iterate.cli <directory> --context-aware-tests <file_path>

# Update context when a file changes
python3 -m iterate.cli <directory> --update-context <file_path>
```

### Traditional File Scanning

```bash
# Basic directory scan
python3 -m iterate.cli <directory>

# Non-recursive scan
python3 -m iterate.cli <directory> --no-recursive

# Limit scan depth
python3 -m iterate.cli <directory> --max-depth 3

# Monitor directory for changes
python3 -m iterate.cli <directory> --monitor

# Verbose output
python3 -m iterate.cli <directory> -v
```

## 📊 What You'll See

### Intelligence Initialization

```
🧠 Initializing Intelligent Codebase Features...
🔍 Initializing codebase intelligence system...
📊 Loading embedding model...
🗄️  Setting up vector database...
✅ Codebase Intelligence initialized successfully!
```

### Codebase Insights

```
📊 Getting codebase insights...
📁 Total chunks: 45
📄 Unique files: 12
🔧 Functions: 23
🏗️  Classes: 8
📦 Imports: 14
📊 Average complexity: 3.2
⚠️  High complexity functions: 3
🔄 Duplicates found: 2
🎯 Cross-file opportunities: 5
```

### Duplicate Detection

```
🔍 Finding duplicate code patterns...
🎯 Found 2 duplicate patterns:
📁 Function: validate_input
   Occurrences: 3
   Files: utils.py, helpers.py, main.py
   Suggestion: Consider extracting 'validate_input' into a shared utility function
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG System Architecture                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   File Parser   │  │  AST Analyzer   │  │  Chunking   │ │
│  │                 │  │                 │  │             │ │
│  │ • Python AST    │  │ • Functions     │  │ • Functions │ │
│  │ • JS Regex      │  │ • Classes       │  │ • Classes   │ │
│  │ • Multi-lang    │  │ • Imports       │  │ • Modules   │ │
│  └─────────────────┘  │ • Complexity    │  │ • Imports   │ │
│                       └─────────────────┘  └─────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Embeddings    │  │  Vector DB      │  │  Query      │ │
│  │                 │  │                 │  │             │ │
│  │ • Sentence      │  │ • ChromaDB      │  │ • Semantic  │ │
│  │   Transformers  │  │ • Persistent    │  │ • Similarity│ │
│  │ • all-MiniLM    │  │ • Collections   │  │ • Context   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
fix-code-debt/
├── iterate/
│   ├── cli.py                          # Main CLI interface
│   ├── core/
│   │   ├── codebase_intelligence.py    # RAG system core
│   │   ├── intelligent_ai_generator.py # AI integration
│   │   ├── ai_code_generator.py        # AI code generation
│   │   ├── dependency_mapper.py        # Dependency analysis
│   │   ├── test_generator.py           # Test generation
│   │   └── ... (other core modules)
│   ├── utils/                          # Utility functions
│   └── integrations/                   # External integrations
├── tests/                              # Test files
└── README.md                           # This file
```

## 🎯 Use Cases

### For Developers

- **Code Review**: Quickly identify complex functions and potential issues
- **Refactoring**: Find duplicate code and cross-file refactoring opportunities
- **Testing**: Generate context-aware tests for your functions
- **Documentation**: Understand codebase structure and dependencies

### For Teams

- **Code Quality**: Monitor complexity and maintainability metrics
- **Knowledge Sharing**: Understand how different parts of the codebase relate
- **Onboarding**: Help new developers understand the codebase structure

### For Projects

- **Technical Debt**: Identify areas that need refactoring
- **Architecture**: Analyze dependencies and coupling between modules
- **Maintenance**: Track code changes and their impact across files

## 🔧 Dependencies

- **sentence-transformers**: For code embeddings
- **chromadb**: For vector database storage
- **numpy**: For numerical operations
- **ast**: For Python code parsing
- **re**: For regex-based parsing

## 🚀 Future Features

- **Real-time Updates**: File watchers for live code analysis
- **Enhanced AI**: Context-aware code generation and refactoring
- **Multi-language Support**: More programming languages
- **IDE Integration**: Plugin for popular IDEs
- **Team Analytics**: Code quality metrics and trends

## 📝 Examples

### Analyze a Python Project

```bash
python3 -m iterate.cli /path/to/python/project --intelligence --codebase-insights
```

### Find Duplicates in JavaScript Project

```bash
python3 -m iterate.cli /path/to/js/project --find-duplicates
```

### Generate Tests for Specific File

```bash
python3 -m iterate.cli . --context-aware-tests src/main.py
```

### Monitor Changes

```bash
python3 -m iterate.cli . --monitor --duration 300
```

## 🤝 Contributing

This project is designed to be a **smart code analysis tool** that helps developers understand and improve their codebases. Contributions are welcome!

## 📄 License

[Add your license information here]
