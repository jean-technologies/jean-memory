#!/usr/bin/env python3
"""
Test script for Claude MCP OAuth integration

This script simulates what Claude does:
1. Discovers OAuth endpoints
2. Dynamically registers as a client
3. Goes through OAuth flow
4. Connects to MCP server with Bearer token
"""

import requests
import json
import sys
from urllib.parse import urlencode, parse_qs, urlparse

# Test against dev server
BASE_URL = "https://jean-memory-api-dev.onrender.com"

def test_oauth_discovery():
    """Test OAuth discovery endpoint"""
    print("🔍 Testing OAuth discovery...")
    
    url = f"{BASE_URL}/.well-known/oauth-authorization-server"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ OAuth discovery successful")
        print(f"   Authorization endpoint: {data.get('authorization_endpoint')}")
        print(f"   Token endpoint: {data.get('token_endpoint')}")
        return data
    else:
        print(f"❌ OAuth discovery failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_dynamic_client_registration():
    """Test dynamic client registration"""
    print("\n📝 Testing dynamic client registration...")
    
    url = f"{BASE_URL}/oauth/register"
    
    # Simulate Claude's registration request
    registration_data = {
        "client_name": "Claude",
        "redirect_uris": [
            "https://claude.ai/api/mcp/auth_callback"
        ],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "scope": "read write",
        "token_endpoint_auth_method": "none"
    }
    
    response = requests.post(url, json=registration_data)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Client registration successful")
        print(f"   Client ID: {data.get('client_id')}")
        print(f"   Client Name: {data.get('client_name')}")
        print(f"   Redirect URIs: {data.get('redirect_uris')}")
        return data
    else:
        print(f"❌ Client registration failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_mcp_server_without_auth():
    """Test MCP server endpoint without authentication (should fail)"""
    print("\n🚫 Testing MCP server without authentication...")
    
    url = f"{BASE_URL}/mcp"
    
    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    
    response = requests.post(url, json=mcp_request)
    
    if response.status_code == 401:
        print("✅ MCP server correctly rejects unauthenticated requests")
    else:
        print(f"⚠️  Expected 401, got {response.status_code}")
        print(f"   Response: {response.text}")

def test_mcp_server_with_fake_token():
    """Test MCP server with fake Bearer token (should fail)"""
    print("\n🔒 Testing MCP server with invalid token...")
    
    url = f"{BASE_URL}/mcp"
    headers = {"Authorization": "Bearer fake-token-123"}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "method": "tools/list", 
        "id": 1
    }
    
    response = requests.post(url, json=mcp_request, headers=headers)
    
    if response.status_code == 401:
        print("✅ MCP server correctly rejects invalid tokens")
    else:
        print(f"⚠️  Expected 401, got {response.status_code}")
        print(f"   Response: {response.text}")

def test_mcp_health_endpoint():
    """Test MCP health endpoint"""
    print("\n❤️  Testing MCP health endpoint...")
    
    url = f"{BASE_URL}/mcp/health"
    headers = {"Authorization": "Bearer fake-token-123"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 401:
        print("✅ MCP health endpoint correctly requires authentication")
    else:
        print(f"⚠️  Expected 401, got {response.status_code}")
        print(f"   Response: {response.text}")

def main():
    """Run all tests"""
    print("🧪 Testing Claude MCP OAuth Integration")
    print("=" * 50)
    
    # Test OAuth discovery
    discovery_data = test_oauth_discovery()
    if not discovery_data:
        print("❌ OAuth discovery failed, stopping tests")
        sys.exit(1)
    
    # Test dynamic client registration
    client_data = test_dynamic_client_registration()
    if not client_data:
        print("❌ Client registration failed, stopping tests")
        sys.exit(1)
    
    # Test MCP server security
    test_mcp_server_without_auth()
    test_mcp_server_with_fake_token()
    test_mcp_health_endpoint()
    
    print("\n🎉 Basic OAuth infrastructure tests completed!")
    print("\n📋 Next steps for full testing:")
    print("1. Use MCP Inspector to complete OAuth flow:")
    print(f"   npx @modelcontextprotocol/inspector {BASE_URL}/mcp")
    print("2. Or manually complete OAuth flow in browser:")
    print(f"   {discovery_data.get('authorization_endpoint')}?client_id=claude-ai&redirect_uri=https://claude.ai/api/mcp/auth_callback&response_type=code&state=test")

if __name__ == "__main__":
    main()