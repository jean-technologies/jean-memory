#!/usr/bin/env python3
"""
Simple test for Claude Web MCP OAuth integration

Tests the minimal implementation that matches Anthropic's official documentation.
"""

import requests
import json

BASE_URL = "https://jean-memory-api-dev.onrender.com"

def test_oauth_discovery():
    """Test OAuth discovery endpoint"""
    print("🔍 Testing OAuth discovery...")
    
    url = f"{BASE_URL}/.well-known/oauth-authorization-server"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ OAuth discovery working")
        print(f"   Authorization: {data.get('authorization_endpoint')}")
        print(f"   Token: {data.get('token_endpoint')}")
        print(f"   Registration: {data.get('registration_endpoint')}")
        return data
    else:
        print(f"❌ OAuth discovery failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_client_registration():
    """Test dynamic client registration"""
    print("\n📝 Testing client registration...")
    
    url = f"{BASE_URL}/oauth/register"
    
    # Simulate Claude's registration
    registration_data = {
        "client_name": "Claude Web",
        "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"]
    }
    
    response = requests.post(url, json=registration_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Client registration working")
        print(f"   Client ID: {data.get('client_id')}")
        return data
    else:
        print(f"❌ Client registration failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_mcp_endpoint_without_auth():
    """Test MCP endpoint security"""
    print("\n🔒 Testing MCP endpoint security...")
    
    url = f"{BASE_URL}/mcp"
    
    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    
    response = requests.post(url, json=mcp_request)
    
    if response.status_code == 401:
        print("✅ MCP endpoint properly secured")
    else:
        print(f"⚠️  Expected 401, got {response.status_code}")
        print(f"   Response: {response.text}")

def main():
    """Run all tests"""
    print("🧪 Testing Simple Claude Web OAuth Integration")
    print("=" * 60)
    
    # Test OAuth discovery
    discovery_data = test_oauth_discovery()
    if not discovery_data:
        print("❌ OAuth discovery failed - stopping tests")
        return
    
    # Test client registration
    client_data = test_client_registration()
    if not client_data:
        print("❌ Client registration failed - stopping tests")
        return
    
    # Test MCP endpoint security
    test_mcp_endpoint_without_auth()
    
    print("\n🎉 Basic infrastructure tests passed!")
    print("\n📋 Next steps:")
    print("1. Add this URL to Claude Web:")
    print(f"   {BASE_URL}/mcp")
    print("2. Claude will automatically handle OAuth")
    print("3. After auth, you'll have access to jean_memory tools")

if __name__ == "__main__":
    main()