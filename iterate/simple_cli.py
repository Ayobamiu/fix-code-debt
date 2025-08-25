#!/usr/bin/env python3
"""
Simplified CLI interface for Iterate - Code Debt Fixing Tool
Makes it easy to use with simple commands like 'iterate test file.py'
"""

import sys
import argparse
from pathlib import Path
from .cli import main as original_main


def main():
    """Simplified CLI entry point with intuitive commands."""
    if len(sys.argv) < 2:
        print("🚀 Iterate - AI-Powered Code Debt Fixing Tool")
        print("\nQuick Commands:")
        print("  iterate test <file>           # Generate tests for a file")
        print("  iterate analyze <directory>   # Analyze codebase for debt")
        print("  iterate refactor <file>       # Get refactoring suggestions")
        print("  iterate duplicates            # Find duplicate code")
        print("\nFull help: iterate --help")
        return
    
    # Check for simple commands
    command = sys.argv[1]
    
    if command == "test" and len(sys.argv) >= 3:
        # Simple test generation
        file_path = sys.argv[2]
        print(f"🧪 Generating tests for: {file_path}")
        
        # Convert to full CLI command
        sys.argv = [
            "iterate", ".", "--intelligence", "--context-aware-tests", file_path
        ]
        original_main()
        
    elif command == "analyze" and len(sys.argv) >= 3:
        # Simple codebase analysis
        directory = sys.argv[2]
        print(f"🔍 Analyzing codebase: {directory}")
        
        # Convert to full CLI command
        sys.argv = ["iterate", directory, "--intelligence", "--codebase-insights"]
        original_main()
        
    elif command == "refactor" and len(sys.argv) >= 3:
        # Simple refactoring suggestions
        file_path = sys.argv[2]
        print(f"🔧 Getting refactoring suggestions for: {file_path}")
        
        # Convert to full CLI command
        sys.argv = [
            "iterate", ".", "--intelligence", "--intelligent-refactor", file_path
        ]
        original_main()
        
    elif command == "duplicates":
        # Find duplicate code
        print("🔄 Finding duplicate code patterns...")
        
        # Convert to full CLI command
        sys.argv = ["iterate", ".", "--intelligence", "--find-duplicates"]
        original_main()
        
    elif command in ["--help", "-h", "help"]:
        print("🚀 Iterate - AI-Powered Code Debt Fixing Tool")
        print("\nSimple Commands:")
        print("  iterate test <file>           # Generate tests for a file")
        print("  iterate analyze <directory>   # Analyze codebase for debt")
        print("  iterate refactor <file>       # Get refactoring suggestions")
        print("  iterate duplicates            # Find duplicate code")
        print("\nExamples:")
        print("  iterate test src/main.py")
        print("  iterate analyze .")
        print("  iterate refactor utils/helper.py")
        print("  iterate duplicates")
        print("\nAdvanced usage: iterate --help")
        
    else:
        # Fall back to original CLI for complex commands
        original_main()


if __name__ == "__main__":
    main()
