#!/usr/bin/env python3
"""
Debug script to test environment variable loading.
"""

import os
from dotenv import load_dotenv

print("🔍 Debugging environment variable loading...")
print(f"Current working directory: {os.getcwd()}")
print(f"Environment before loading: OPENAI_API_KEY = {os.getenv('OPENAI_API_KEY')}")

# Try to load from current directory
load_dotenv()
print(f"After load_dotenv(): OPENAI_API_KEY = {os.getenv('OPENAI_API_KEY')}")

# Try to load from project directory
load_dotenv(".")
print(f"After load_dotenv('.'): OPENAI_API_KEY = {os.getenv('OPENAI_API_KEY')}")

# Check if the key is accessible
if os.getenv('OPENAI_API_KEY'):
    key = os.getenv('OPENAI_API_KEY')
    print(f"✅ API key found: {key[:20]}...")
else:
    print("❌ No API key found")
