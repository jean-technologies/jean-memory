#!/usr/bin/env python3
"""
Test script to verify that all endpoints are correctly routing users to the appropriate memory systems.
"""

import os
import sys
import logging

# Add the parent directory to the path so we can import from openmemory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openmemory.api.app.utils.memory import get_memory_client_for_user
from openmemory.api.app.utils.unified_memory import should_use_unified_memory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_user_routing():
    """Test that users are correctly routed to the appropriate memory systems"""
    
    print("🧪 Testing Memory Client Routing")
    print("=" * 50)
    
    # Test user ID (from environment or default)
    test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID", "5a4cc4ed-d8f1-4128-af09-18ec96963ecc")
    random_user_id = "12345678-1234-1234-1234-123456789012"
    
    print(f"Test User ID: {test_user_id}")
    print(f"Random User ID: {random_user_id}")
    print()
    
    # Test routing function
    print("🔍 Testing routing function:")
    test_should_use_unified = should_use_unified_memory(test_user_id)
    random_should_use_unified = should_use_unified_memory(random_user_id)
    
    print(f"   Test User should use unified: {test_should_use_unified}")
    print(f"   Random User should use unified: {random_should_use_unified}")
    print()
    
    # Test memory client creation
    print("🔧 Testing memory client creation:")
    try:
        test_client = get_memory_client_for_user(test_user_id)
        print(f"   Test User client type: {type(test_client).__name__}")
        print(f"   Test User client module: {test_client.__class__.__module__}")
    except Exception as e:
        print(f"   Test User client creation failed: {e}")
    
    try:
        random_client = get_memory_client_for_user(random_user_id)
        print(f"   Random User client type: {type(random_client).__name__}")
        print(f"   Random User client module: {random_client.__class__.__module__}")
    except Exception as e:
        print(f"   Random User client creation failed: {e}")
    
    print()
    
    # Test environment variables
    print("🌐 Environment Variables:")
    print(f"   ENABLE_UNIFIED_MEMORY_TEST_USER: {os.getenv('ENABLE_UNIFIED_MEMORY_TEST_USER', 'not set')}")
    print(f"   UNIFIED_MEMORY_TEST_USER_ID: {os.getenv('UNIFIED_MEMORY_TEST_USER_ID', 'not set')[:8]}...")
    print(f"   USE_UNIFIED_MEMORY: {os.getenv('USE_UNIFIED_MEMORY', 'not set')}")
    print()
    
    # Summary
    print("📊 Summary:")
    if test_should_use_unified and not random_should_use_unified:
        print("   ✅ Routing is working correctly!")
        print("   ✅ Test user routes to NEW system")
        print("   ✅ Regular users route to OLD system")
    elif test_should_use_unified and random_should_use_unified:
        print("   ⚠️  Both users route to NEW system - check environment variables")
    elif not test_should_use_unified and not random_should_use_unified:
        print("   ⚠️  Both users route to OLD system - test user routing may be disabled")
    else:
        print("   ❌ Unexpected routing configuration")


if __name__ == "__main__":
    test_user_routing() 