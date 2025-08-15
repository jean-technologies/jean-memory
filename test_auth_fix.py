#!/usr/bin/env python3
"""
Quick test to verify v1.2.7 authentication fixes are working
"""
import requests
import json

# Test 1: Direct API test with Authorization header
def test_api_auth():
    print("🧪 Testing API Authentication...")
    
    # Replace with actual API key for testing
    api_key = "jean_sk_test_key_here"
    
    url = "https://jean-memory-api-virginia.onrender.com/api/v1/test-user"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 401:
            print("❌ Still getting 401 - auth fix not working")
            return False
        elif response.status_code == 200:
            print("✅ Auth working - 200 response")
            return True
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

# Test 2: Check MCP header format
def test_mcp_headers():
    print("\n🧪 Testing MCP Header Format...")
    
    # This is what the SDK should now be sending
    correct_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer jean_sk_test_key',
        'X-User-Id': 'test_user_abc123',
        'X-Client-Name': 'python-sdk',
        'X-Api-Key': 'jean_sk_test_key'  # Note: X-Api-Key not X-API-Key
    }
    
    print("✅ SDK should be sending these headers:")
    for key, value in correct_headers.items():
        if 'jean_sk_' in value:
            print(f"  {key}: Bearer jean_sk_[YOUR_KEY]")
        else:
            print(f"  {key}: {value}")
    
    print("\n🔍 Key fix: X-Api-Key (not X-API-Key)")

if __name__ == "__main__":
    print("🎯 Jean Memory v1.2.7 Authentication Fix Verification\n")
    
    test_api_auth()
    test_mcp_headers()
    
    print("\n📋 Instructions for tester:")
    print("1. Replace 'jean_sk_test_key_here' with actual API key")
    print("2. Run this script to verify authentication")
    print("3. Clear npm/pip cache before testing:")
    print("   npm cache clean --force")
    print("   pip cache purge")
    print("4. Install fresh SDK versions:")
    print("   npm install @jeanmemory/react@1.2.7")
    print("   pip install jeanmemory==1.2.7")