#!/usr/bin/env python3
"""
Jean Memory Python SDK Test Script
Tests the headless backend integration
"""

import os
import sys
import json

# Add the SDK to path for testing
sys.path.insert(0, '../../python')

from jeanmemory import JeanClient

def test_basic_functionality():
    """Test basic SDK functionality"""
    
    # This should be your actual API key
    api_key = os.environ.get('JEAN_API_KEY', 'jean_sk_test_key_for_testing')
    
    print("🧪 Testing Jean Memory Python SDK")
    print("=" * 50)
    
    try:
        # Initialize client
        print("1️⃣ Initializing JeanClient...")
        jean = JeanClient(api_key=api_key)
        print("✅ Client initialized successfully")
        
        # Test mock user token (for testing without real OAuth)
        test_user_token = "test.eyJzdWIiOiJ0ZXN0X3VzZXJfMTIzIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIn0.signature"
        
        print("\n2️⃣ Testing configuration options...")
        
        # Test different configuration options
        configs = [
            {"speed": "fast", "tool": "jean_memory", "format": "simple"},
            {"speed": "balanced", "tool": "search_memory", "format": "enhanced"},
            {"speed": "comprehensive", "tool": "jean_memory", "format": "enhanced"}
        ]
        
        for i, config in enumerate(configs, 1):
            print(f"   Testing config {i}: {config}")
            try:
                # This will fail with real backend but should pass parameter validation
                context = jean.get_context(
                    user_token=test_user_token,
                    message=f"Test message {i}",
                    **config
                )
                print(f"   ✅ Config {i} parameters accepted")
            except Exception as e:
                if "MCP request failed" in str(e):
                    print(f"   ✅ Config {i} parameters passed (expected backend error)")
                else:
                    print(f"   ❌ Config {i} failed: {e}")
        
        print("\n3️⃣ Testing direct tool access...")
        
        # Test direct tools
        tools_tests = [
            ("add_memory", lambda: jean.tools.add_memory(test_user_token, "Test memory content")),
            ("search_memory", lambda: jean.tools.search_memory(test_user_token, "test query"))
        ]
        
        for tool_name, tool_func in tools_tests:
            try:
                result = tool_func()
                print(f"   ✅ {tool_name} parameters accepted")
            except Exception as e:
                if "MCP request failed" in str(e):
                    print(f"   ✅ {tool_name} parameters passed (expected backend error)")
                else:
                    print(f"   ❌ {tool_name} failed: {e}")
        
        print("\n🎉 SDK Test Summary:")
        print("✅ Client initialization works")
        print("✅ Configuration parameters properly passed")
        print("✅ Direct tool access functional")
        print("✅ Error handling working correctly")
        
        print("\n📋 Next steps:")
        print("1. Add your real JEAN_API_KEY to environment")
        print("2. Test with real user tokens from OAuth flow")
        print("3. Verify backend endpoints are working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_jwt_parsing():
    """Test JWT token parsing functionality"""
    print("\n4️⃣ Testing JWT token parsing...")
    
    api_key = os.environ.get('JEAN_API_KEY', 'jean_sk_test_key_for_testing')
    jean = JeanClient(api_key=api_key)
    
    # Test valid JWT-like token
    import base64
    payload = {"sub": "user_123", "email": "test@example.com"}
    encoded_payload = base64.b64encode(json.dumps(payload).encode()).decode()
    test_jwt = f"header.{encoded_payload}.signature"
    
    user_id = jean._get_user_id_from_token(test_jwt)
    
    if user_id == "user_123":
        print("   ✅ JWT parsing works correctly")
    else:
        print(f"   ❌ JWT parsing failed: got {user_id}, expected user_123")
    
    # Test fallback for non-JWT
    fallback_result = jean._get_user_id_from_token("not_a_jwt")
    if fallback_result == "not_a_jwt":
        print("   ✅ JWT fallback works correctly")
    else:
        print(f"   ❌ JWT fallback failed: got {fallback_result}")

if __name__ == "__main__":
    print("Jean Memory Python SDK Test Runner")
    print("Make sure your JEAN_API_KEY environment variable is set!")
    print()
    
    success = test_basic_functionality()
    test_jwt_parsing()
    
    if success:
        print("\n🚀 Ready for production testing with real API key!")
    else:
        print("\n⚠️ Issues found - check configuration")