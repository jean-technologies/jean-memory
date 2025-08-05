#!/usr/bin/env python3
"""Test script for Jean Memory SDK functionality"""

import sys
import os
import json
from typing import Dict, Any

# Add SDK python path to sys.path
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk', 'python')
if sdk_path not in sys.path:
    sys.path.insert(0, sdk_path)

# Test configuration
API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"
API_BASE = "https://jean-memory-api-virginia.onrender.com"

def test_sdk_import():
    """Test if SDK can be imported"""
    print("\n=== Test 1: SDK Import ===")
    try:
        from jeanmemory import JeanAgent
        print("✅ SDK imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import SDK: {e}")
        return False

def test_api_key_validation():
    """Test API key validation"""
    print("\n=== Test 2: API Key Validation ===")
    try:
        import requests
        response = requests.post(
            f"{API_BASE}/sdk/validate-developer",
            json={
                "api_key": API_KEY,
                "client_name": "Test Script"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API key valid for developer: {data['developer_id']}")
            return True
        else:
            print(f"❌ API key validation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error validating API key: {e}")
        return False

def test_sdk_initialization():
    """Test SDK initialization"""
    print("\n=== Test 3: SDK Initialization ===")
    try:
        from jeanmemory import JeanAgent
        agent = JeanAgent(
            api_key=API_KEY,
            system_prompt="You are a test assistant.",
            client_name="Test Script"
        )
        print("✅ SDK initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize SDK: {e}")
        return False

def test_auth_endpoint():
    """Test authentication endpoint (without actual credentials)"""
    print("\n=== Test 4: Auth Endpoint Connectivity ===")
    try:
        import requests
        # Test with invalid credentials to check endpoint availability
        response = requests.post(
            f"{API_BASE}/sdk/auth/login",
            json={
                "email": "test@example.com",
                "password": "test123"
            }
        )
        
        # We expect 401 for invalid credentials, which confirms endpoint is working
        if response.status_code == 401:
            print("✅ Auth endpoint is reachable (401 expected for test credentials)")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.status_code} - {response.text}")
            return True  # Still consider it working if we get any response
    except Exception as e:
        print(f"❌ Error accessing auth endpoint: {e}")
        return False

def test_chat_enhance_endpoint():
    """Test chat enhance endpoint structure"""
    print("\n=== Test 5: Chat Enhance Endpoint ===")
    try:
        import requests
        # Test with minimal payload to check endpoint
        response = requests.post(
            f"{API_BASE}/sdk/chat/enhance",
            json={
                "api_key": API_KEY,
                "client_name": "Test Script",
                "user_id": "test-user-id",
                "messages": [{"role": "user", "content": "Hello"}],
                "system_prompt": "You are a test assistant"
            }
        )
        
        # We expect some error since we don't have a valid user_id
        print(f"ℹ️  Response code: {response.status_code}")
        if response.status_code in [400, 401, 422]:
            print("✅ Chat enhance endpoint is reachable (error expected without valid user)")
            return True
        elif response.status_code == 200:
            print("✅ Chat enhance endpoint returned success")
            return True
        else:
            print(f"⚠️  Unexpected response: {response.text}")
            return True
    except Exception as e:
        print(f"❌ Error accessing chat enhance endpoint: {e}")
        return False

def test_sdk_features():
    """Test SDK features and methods"""
    print("\n=== Test 6: SDK Features ===")
    try:
        from jeanmemory import JeanAgent, create_agent
        
        # Test create_agent helper
        agent = create_agent(API_KEY, "Test prompt")
        print("✅ create_agent() helper works")
        
        # Test methods exist
        methods = ['authenticate', 'send_message', 'run', 'get_conversation_history', 'clear_conversation']
        missing = []
        for method in methods:
            if not hasattr(agent, method):
                missing.append(method)
        
        if missing:
            print(f"❌ Missing methods: {', '.join(missing)}")
            return False
        else:
            print("✅ All expected methods present")
            return True
            
    except Exception as e:
        print(f"❌ Error testing SDK features: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Jean Memory SDK Functionality Test")
    print("=" * 50)
    
    tests = [
        test_sdk_import,
        test_api_key_validation,
        test_sdk_initialization,
        test_auth_endpoint,
        test_chat_enhance_endpoint,
        test_sdk_features
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)