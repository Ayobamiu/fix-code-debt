# Iterate - Intelligent File Discovery Tool

A robust Python-based file discovery tool with comprehensive error handling, progress reporting, and intelligent caching for analyzing codebases.

## Features

### 🔍 **Efficient File Discovery**

- **Optimized scanning** using `os.scandir` for performance
- **Recursive directory traversal** with configurable depth limits
- **Large directory handling** with memory-efficient processing

### 🛡️ **Error Handling & Recovery**

- **Graceful error recovery** for permission issues, corrupted files, and network problems
- **Comprehensive logging** with different severity levels
- **Safe operations** that continue scanning even when individual files fail
- **Error summaries** with detailed breakdowns

### 📊 **Progress Reporting**

- **Real-time progress bars** with ETA calculations
- **Multiple progress modes**: silent, simple, detailed, verbose
- **Cancellation support** with Ctrl+C handling
- **Progress callbacks** for integration with other tools

### ⚡ **Intelligent Caching**

- **Incremental updates** - only scan changed files
- **File timestamp tracking** for efficient change detection
- **Cache invalidation** and management
- **Performance metrics** and cache statistics

### 🚫 **Smart Ignore Patterns**

- **Comprehensive defaults** for common build artifacts, version control, and IDE files
- **Custom patterns** support with wildcard matching
- **Language-specific ignores** for different project types
- **Recursive pattern matching** for nested directories

### 👀 **Real-time Monitoring**

- **File system watching** with `watchdog` integration
- **Change detection** for files and directories
- **Event logging** with timestamps and change counts
- **Graceful fallback** when watchdog is not available

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd fix-code-debt

# Install dependencies
pip install -r requirements.txt

# Optional: Install for development
pip install -e .
```

## Quick Start

### Basic Usage

```bash
# Scan a directory
python iterate_cli.py /path/to/your/project

# Non-recursive scan
python iterate_cli.py /path/to/your/project --no-recursive

# Limit scan depth
python iterate_cli.py /path/to/your/project --max-depth 3
```

### Progress Reporting

```bash
# Simple progress bar (default)
python iterate_cli.py /path/to/your/project --progress simple

# Detailed progress information
python iterate_cli.py /path/to/your/project --progress detailed

# Verbose output with current file/directory
python iterate_cli.py /path/to/your/project --progress verbose

# Silent mode (no progress output)
python iterate_cli.py /path/to/your/project --progress silent
```

### Error Handling

```bash
# Show error information (default)
python iterate_cli.py /path/to/your/project --show-errors

# Hide error information
python iterate_cli.py /path/to/your/project --hide-errors

# Verbose error output
python iterate_cli.py /path/to/your/project --verbose
```

### Caching

```bash
# Use caching (default)
python iterate_cli.py /path/to/your/project

# Disable caching
python iterate_cli.py /path/to/your/project --no-cache
```

### Ignore Patterns

```bash
# Use default ignore patterns (default)
python iterate_cli.py /path/to/your/project

# Disable ignore patterns
python iterate_cli.py /path/to/your/project --no-ignore

# Add custom ignore patterns
python iterate_cli.py /path/to/your/project --ignore "*.log" --ignore "temp/*"
```

### Real-time Monitoring

```bash
# Monitor directory for changes
python iterate_cli.py /path/to/your/project --monitor

# Monitor for specific duration
python iterate_cli.py /path/to/your/project --monitor --duration 60
```

## Advanced Usage

### Programmatic Usage

```python
from iterate.core import FileFinder
from iterate.core.progress_reporter import ProgressType

# Create file finder with custom options
finder = FileFinder(
    use_cache=True,
    progress_type=ProgressType.DETAILED
)

# Scan directory
result = finder.find_files_and_folders(
    directory_path="/path/to/project",
    recursive=True,
    max_depth=5,
    ignore_patterns=["*.tmp", "build/*"]
)

# Access results
print(f"Found {result['total_files']} files and {result['total_folders']} directories")
print(f"Scan time: {result['scan_time']:.2f} seconds")

# Check for errors
if result['errors']['total_errors'] > 0:
    print(f"Encountered {result['errors']['total_errors']} errors")
```

### Error Handling

```python
from iterate.core import ErrorHandler, ErrorSeverity

# Create error handler
error_handler = ErrorHandler(verbose=True)

# Handle errors programmatically
def safe_operation():
    try:
        # Your operation here
        pass
    except Exception as e:
        handled = error_handler.handle_error(
            e,
            {"operation": "my_operation", "context": "additional_info"},
            ErrorSeverity.WARNING
        )
        if not handled:
            raise  # Re-raise if not handled

# Get error summary
summary = error_handler.get_error_summary()
print(f"Total errors: {summary['total_errors']}")
```

## Project Structure

```
fix-code-debt/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── iterate_cli.py               # Main CLI entry point
├── .iterate_cache/              # Cache directory (auto-created)
└── iterate/                     # Main package
    ├── __init__.py              # Package initialization
    ├── cli.py                   # Command-line interface
    ├── core/                    # Core functionality
    │   ├── __init__.py
    │   ├── file_finder.py       # Main file discovery logic
    │   ├── cache_manager.py     # Caching and incremental updates
    │   ├── ignore_patterns.py   # Ignore pattern handling
    │   ├── error_handler.py     # Error handling and recovery
    │   └── progress_reporter.py # Progress reporting
    └── utils/                   # Utility functions
        ├── __init__.py
        ├── display.py           # Result display utilities
        └── monitoring.py        # File system monitoring
```

## Error Handling Features

### Automatic Recovery

- **Permission errors**: Skip inaccessible files/directories
- **Corrupted files**: Continue scanning, log the issue
- **Network issues**: Graceful handling of network drive problems
- **Memory errors**: Automatic garbage collection and limits

### Error Classification

- **INFO**: Non-critical issues (e.g., file not found)
- **WARNING**: Issues that don't stop scanning (e.g., permission denied)
- **ERROR**: Serious issues that may affect results
- **CRITICAL**: Fatal errors that stop the operation

### Error Reporting

- **Detailed logs** with timestamps and context
- **Error summaries** with counts by type
- **Recovery attempts** tracking
- **Configurable verbosity** levels

## Progress Reporting Features

### Progress Types

- **SILENT**: No progress output
- **SIMPLE**: Basic progress bar with percentage
- **DETAILED**: File/directory counts and timing
- **VERBOSE**: Current file/directory being processed

### Progress Information

- **Real-time updates** with configurable intervals
- **ETA calculations** based on processing rate
- **Cancellation support** with graceful shutdown
- **Progress callbacks** for integration

## Performance Features

### Caching Strategy

- **MD5-based cache keys** for parameter changes
- **File timestamp tracking** for change detection
- **Incremental updates** for modified files only
- **Cache invalidation** and cleanup

### Memory Management

- **Streaming processing** for large directories
- **Memory usage monitoring** and limits
- **Garbage collection** during long operations
- **Efficient data structures** for file lists

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Roadmap

- [ ] **Dependency Mapping** - Parse code for function/variable relationships
- [ ] **Language-specific Parsing** - Different strategies for JS/TS vs Python
- [ ] **Memory Management** - Streaming/iterator-based processing
- [ ] **Configuration Management** - Configurable ignore patterns per project
- [ ] **Performance Benchmarking** - Scan time metrics and optimization
- [ ] **Cross-platform Compatibility** - Windows path handling improvements

Goal: this tool will be used by developers because they have a lot of bad codes, or code that needs improvement. They have not done fixed them because;

1. it takes time [time-consuming]
2. it may break other things that are already working [testing-problem]
3. they don't know the quality of their code because there is no measure [the only measure in the industry now is test-coverage] [code-quality-measure]

So, this tool will learn about the dev's code [code-access] and business [integrations], work without much supervision [agents], measure code quality[fix-code-quality-measure], write best-quality code to replace what the dev has, present it to the dev with some quality tests [fix-testing-problem] written to assure the dev that the new best-quality code will not break what is already working. And we will do so with the best experience ever. Eventually, the code quality will improve drastically.
