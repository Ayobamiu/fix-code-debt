# Iterate

Intelligent file discovery and analysis tool for software engineers.

## Features

- **Fast Scanning**: Uses `scandir` for optimal performance
- **Smart Caching**: Incremental updates - only scan changed files
- **Ignore Patterns**: Automatically filters out irrelevant files (node_modules, .git, etc.)
- **Real-time Monitoring**: Watch directories for changes with `watchdog`
- **Large Directory Support**: Handle massive codebases efficiently
- **Depth Control**: Limit scanning depth for performance

## Quick Start

```bash
# Basic scan
python3 iterate_cli.py /path/to/project

# With options
python3 iterate_cli.py /path/to/project --max-depth 3 --no-cache

# Monitor for changes
python3 iterate_cli.py /path/to/project --monitor --duration 60
```

## Project Structure

```
iterate/
├── __init__.py          # Package initialization
├── cli.py              # Command line interface
├── core/               # Core functionality
│   ├── __init__.py
│   ├── file_finder.py  # Main file discovery logic
│   ├── cache_manager.py # Caching with incremental updates
│   └── ignore_patterns.py # File filtering
└── utils/              # Utilities
    ├── __init__.py
    ├── display.py      # Output formatting
    └── monitoring.py   # Real-time file monitoring
```

## Performance

- **Fresh scan**: ~0.2s for 1,000 files
- **Cached (no changes)**: ~0.002s
- **Incremental updates**: ~0.003s for small changes

## Dependencies

- `watchdog` (optional): For real-time monitoring
- Standard library: `os`, `pathlib`, `json`, `hashlib`, `fnmatch`

## Installation

```bash
# Install watchdog for monitoring (optional)
python3 -m pip install watchdog
```

## Usage Examples

```bash
# Scan a TypeScript project
python3 iterate_cli.py ./my-ts-project

# Scan with custom ignore patterns
python3 iterate_cli.py ./project --ignore "*.test.ts" "coverage"

# Monitor for changes during development
python3 iterate_cli.py ./project --monitor --duration 300

# Quick top-level scan
python3 iterate_cli.py ./project --no-recursive
```
# fix-code-debt
