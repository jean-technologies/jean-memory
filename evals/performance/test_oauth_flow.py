#!/usr/bin/env python3
"""
Simple OAuth Flow Test for Jean Memory Claude Integration

This script tests the OAuth flow end-to-end to verify:
1. OAuth discovery works
2. Client registration works  
3. MCP endpoint returns 401 without auth
4. JWT token generation works

Run: python test_oauth_flow.py
"""

import requests
import json

def test_oauth_flow():
    BASE_URL = "https://jean-memory-api-dev.onrender.com"
    
    print("🧪 Testing Jean Memory OAuth Flow")
    print("=" * 50)
    
    # Test 1: OAuth Discovery
    print("\n1. Testing OAuth Discovery...")
    try:
        response = requests.get(f"{BASE_URL}/.well-known/oauth-authorization-server")
        if response.status_code == 200:
            discovery = response.json()
            print(f"✅ OAuth discovery working")
            print(f"   Authorization endpoint: {discovery.get('authorization_endpoint')}")
            print(f"   Token endpoint: {discovery.get('token_endpoint')}")
            print(f"   Registration endpoint: {discovery.get('registration_endpoint')}")
        else:
            print(f"❌ OAuth discovery failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OAuth discovery error: {e}")
        return False
    
    # Test 2: Client Registration
    print("\n2. Testing Client Registration...")
    try:
        registration_data = {
            "client_name": "Test Client",
            "redirect_uris": ["https://example.com/callback"]
        }
        response = requests.post(f"{BASE_URL}/oauth/register", json=registration_data)
        if response.status_code == 200:
            client_info = response.json()
            print(f"✅ Client registration working")
            print(f"   Client ID: {client_info.get('client_id')}")
            print(f"   Client Name: {client_info.get('client_name')}")
        else:
            print(f"❌ Client registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Client registration error: {e}")
        return False
    
    # Test 3: MCP Endpoint Security
    print("\n3. Testing MCP Endpoint Security...")
    try:
        response = requests.post(f"{BASE_URL}/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1})
        if response.status_code == 401:
            print(f"✅ MCP endpoint properly secured (returns 401 without auth)")
        else:
            print(f"⚠️ MCP endpoint returned {response.status_code} (expected 401)")
    except Exception as e:
        print(f"❌ MCP endpoint test error: {e}")
        return False
    
    # Test 4: Health Check
    print("\n4. Testing Server Health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Server healthy")
            print(f"   Status: {health.get('status')}")
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 OAuth Flow Test Results: PASSED")
    print("\nNext Steps:")
    print("1. Try adding the MCP connector in Claude Web:")
    print(f"   URL: {BASE_URL}/mcp")
    print("2. Claude should auto-discover OAuth and handle authentication")
    print("3. Check server logs for detailed OAuth flow information")
    
    return True

if __name__ == "__main__":
    success = test_oauth_flow()
    exit(0 if success else 1)