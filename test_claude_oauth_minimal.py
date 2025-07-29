#!/usr/bin/env python3
"""
Test script for minimal Claude OAuth implementation
"""

import requests
import json

BASE_URL = "http://localhost:8765"

print("🔍 Testing Minimal Claude OAuth Implementation")
print(f"📍 Base URL: {BASE_URL}")
print("=" * 50)

def test_oauth_discovery():
    """Test OAuth discovery endpoint"""
    print("\n1️⃣ Testing OAuth Discovery...")
    
    try:
        response = requests.get(f"{BASE_URL}/.well-known/oauth-authorization-server")
        
        if response.status_code == 200:
            metadata = response.json()
            print("✅ OAuth discovery endpoint works!")
            print(f"   Issuer: {metadata.get('issuer')}")
            print(f"   Auth endpoint: {metadata.get('authorization_endpoint')}")
            print(f"   Token endpoint: {metadata.get('token_endpoint')}")
            print(f"   Registration endpoint: {metadata.get('registration_endpoint')}")
            return True
        else:
            print(f"❌ Discovery failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
        return False

def test_dynamic_client_registration():
    """Test Dynamic Client Registration"""
    print("\n2️⃣ Testing Dynamic Client Registration...")
    
    try:
        registration_data = {
            "client_name": "Test Claude Client",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
            "grant_types": ["authorization_code", "refresh_token"]
        }
        
        response = requests.post(
            f"{BASE_URL}/oauth/register",
            json=registration_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            client_data = response.json()
            print("✅ Client registration successful!")
            print(f"   Client ID: {client_data.get('client_id')}")
            print(f"   Client Name: {client_data.get('client_name')}")
            return True, client_data.get('client_id')
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Registration test failed: {e}")
        return False, None

def test_authorization_page(client_id):
    """Test authorization page loads"""
    print("\n3️⃣ Testing Authorization Page...")
    
    try:
        params = {
            "client_id": client_id,
            "redirect_uri": "https://claude.ai/api/mcp/auth_callback",
            "response_type": "code",
            "state": "test_state_123",
            "code_challenge": "test_challenge",
            "code_challenge_method": "S256"
        }
        
        response = requests.get(f"{BASE_URL}/oauth/authorize", params=params)
        
        if response.status_code == 200 and "Connect Claude to Jean Memory" in response.text:
            print("✅ Authorization page loads correctly!")
            print("   Page contains authorization form")
            return True
        else:
            print(f"❌ Authorization page failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authorization page test failed: {e}")
        return False

def test_mcp_endpoint_requires_auth():
    """Test MCP endpoint requires authentication"""
    print("\n4️⃣ Testing MCP Endpoint (should require auth)...")
    
    try:
        # Try without auth
        response = requests.post(
            f"{BASE_URL}/mcp/oauth/test-user",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1
            }
        )
        
        if response.status_code == 401:
            print("✅ MCP endpoint correctly requires authentication!")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ MCP endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting OAuth tests...\n")
    
    results = []
    
    # Test 1: Discovery
    results.append(test_oauth_discovery())
    
    # Test 2: Client Registration
    reg_success, client_id = test_dynamic_client_registration()
    results.append(reg_success)
    
    # Test 3: Authorization Page (only if registration succeeded)
    if client_id:
        results.append(test_authorization_page(client_id))
    else:
        print("\n⚠️  Skipping authorization page test (no client ID)")
        results.append(False)
    
    # Test 4: MCP Endpoint Auth
    results.append(test_mcp_endpoint_requires_auth())
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed ({passed}/{total})!")
        print("\n✅ OAuth implementation is working correctly!")
        print("\nNext steps:")
        print("1. Deploy to staging/production")
        print("2. Test with real Claude client")
        print("3. Add Redis for token persistence")
        print(f"4. Claude URL: {BASE_URL}/mcp/oauth/{{user_id}}")
    else:
        print(f"❌ {total - passed} tests failed ({passed}/{total} passed)")
        print("\nPlease check the implementation and try again.")

if __name__ == "__main__":
    main() 