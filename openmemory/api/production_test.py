#!/usr/bin/env python3
"""
Test script to simulate production import behavior
This simulates what happens when uvicorn runs from the api directory
"""

import sys
import os

# Simulate production: working directory is openmemory/api
# This is where 'uvicorn main:app' runs from according to Render config

print("Current working directory:", os.getcwd())
print("Python path:", sys.path[:3])  # Show first 3 entries

try:
    # This is the key import that needs to work in production
    print("\n--- Testing key production imports ---")
    
    # Test 1: The import used in app/utils/memory.py line 20
    from jean_memory.mem0_adapter_optimized import get_memory_client_v2_optimized
    print("✓ Successfully imported get_memory_client_v2_optimized")
    
    # Test 2: The import used in app/utils/memory.py line 79  
    from jean_memory.mem0_adapter_optimized import get_async_memory_client_v2_optimized
    print("✓ Successfully imported get_async_memory_client_v2_optimized")
    
    # Test 3: The import used in app/utils/memory.py line 110
    from jean_memory.config import JeanMemoryConfig
    print("✓ Successfully imported JeanMemoryConfig")
    
    print("\n✅ ALL PRODUCTION IMPORTS SUCCESSFUL!")
    print("This confirms the jean_memory integration will work in production.")
    
except ImportError as e:
    print(f"\n❌ PRODUCTION IMPORT FAILED: {e}")
    print("\nThis indicates the deployment will fail.")
    print("The jean_memory module is not being found in the expected location.")
    
except Exception as e:
    print(f"\n❌ UNEXPECTED ERROR: {e}")
    print("This might indicate a dependency issue.")

print(f"\nModule search path for 'jean_memory':")
for i, path in enumerate(sys.path):
    jean_memory_path = os.path.join(path, 'jean_memory')
    if os.path.exists(jean_memory_path):
        print(f"  {i}: {path} ✓ (jean_memory found here)")
    else:
        print(f"  {i}: {path}")