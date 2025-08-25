#!/usr/bin/env python3
"""
Setup script for Iterate - Code Debt Fixing Tool
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        # Fallback requirements if file not found
        return [
            "watchdog>=3.0.0",
            "PyYAML>=6.0", 
            "psutil>=5.8.0",
            "requests",
            "python-dotenv>=1.0.0",
            "openai>=1.0.0",
            "sentence-transformers>=2.2.0",
            "chromadb>=0.5.0",
            "numpy>=1.21.0"
        ]

setup(
    name="iterate-code-debt",
    version="0.1.0",
    author="Usman Ayobami",
    author_email="ayobamiu@gmail.com",
    description="AI-powered code debt fixing tool with intelligent test generation",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Ayobamiu/fix-code-debt",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "iterate=iterate.simple_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "iterate": ["*.json", "*.yaml", "*.yml"],
    },
    keywords="code-debt, testing, ai, refactoring, code-quality, python",
    project_urls={
        "Bug Reports": "https://github.com/Ayobamiu/fix-code-debt/issues",
        "Source": "https://github.com/Ayobamiu/fix-code-debt",
        "Documentation": "https://github.com/Ayobamiu/fix-code-debt#readme",
    },
)
