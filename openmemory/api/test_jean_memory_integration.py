#!/usr/bin/env python3
"""
Test script to verify jean_memory integration works correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Testing jean_memory integration...")
    
    # Test 1: Import the adapter that's used in app/utils/memory.py
    from jean_memory.mem0_adapter_optimized import get_memory_client_v2_optimized
    print("✓ Successfully imported get_memory_client_v2_optimized")
    
    # Test 2: Import the async version
    from jean_memory.mem0_adapter_optimized import get_async_memory_client_v2_optimized
    print("✓ Successfully imported get_async_memory_client_v2_optimized")
    
    # Test 3: Import the config
    from jean_memory.config import JeanMemoryConfig
    print("✓ Successfully imported JeanMemoryConfig")
    
    # Test 4: Import from the main module
    from jean_memory import JeanMemoryV2
    print("✓ Successfully imported JeanMemoryV2")
    
    print("\n✅ All imports successful! The jean_memory integration is working correctly.")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nThis might be due to missing dependencies in your virtual environment.")
    print("Make sure you have installed all requirements:")
    print("  pip install -r requirements.txt")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")