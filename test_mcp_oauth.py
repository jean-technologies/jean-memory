#!/usr/bin/env python3
"""
Test script to simulate Claude Web's MCP OAuth flow
This will help us verify if our implementation works correctly
"""

import requests
import json
import hashlib
import base64
import secrets
from urllib.parse import parse_qs, urlparse

API_BASE = "https://jean-memory-api-virginia.onrender.com"

def generate_pkce():
    """Generate PKCE code verifier and challenge"""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

def test_oauth_discovery():
    """Test OAuth discovery endpoint"""
    print("1. Testing OAuth Discovery...")
    response = requests.get(f"{API_BASE}/.well-known/oauth-authorization-server")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        discovery = response.json()
        print("✅ OAuth Discovery successful")
        return discovery
    else:
        print("❌ OAuth Discovery failed")
        return None

def test_client_registration():
    """Test dynamic client registration"""
    print("\n2. Testing Client Registration...")
    
    registration_data = {
        "client_name": "Test MCP Client",
        "redirect_uris": ["https://test.example.com/callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "scope": "read write"
    }
    
    response = requests.post(f"{API_BASE}/oauth/register", json=registration_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        client_info = response.json()
        print("✅ Client Registration successful")
        print(f"Client ID: {client_info['client_id']}")
        return client_info
    else:
        print("❌ Client Registration failed")
        print(f"Error: {response.text}")
        return None

def test_authorization_flow(client_info):
    """Test authorization flow (will require manual intervention)"""
    print("\n3. Testing Authorization Flow...")
    
    code_verifier, code_challenge = generate_pkce()
    
    auth_params = {
        "client_id": client_info["client_id"],
        "redirect_uri": client_info["redirect_uris"][0],
        "response_type": "code",
        "state": "test-state-123",
        "scope": "read write",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"{API_BASE}/oauth/authorize?" + "&".join([f"{k}={v}" for k, v in auth_params.items()])
    print(f"Authorization URL: {auth_url}")
    print("⚠️  Manual step required: Visit the URL above to complete authorization")
    print("   After authorization, you'll get a code in the redirect URL")
    
    return code_verifier, auth_params

def test_token_exchange(client_info, auth_code, code_verifier):
    """Test token exchange"""
    print("\n4. Testing Token Exchange...")
    
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "client_id": client_info["client_id"],
        "redirect_uri": client_info["redirect_uris"][0],
        "code_verifier": code_verifier
    }
    
    response = requests.post(f"{API_BASE}/oauth/token", data=token_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        token_info = response.json()
        print("✅ Token Exchange successful")
        print(f"Access Token: {token_info['access_token'][:20]}...")
        return token_info
    else:
        print("❌ Token Exchange failed")
        print(f"Error: {response.text}")
        return None

def test_mcp_requests(access_token):
    """Test MCP requests with Bearer token"""
    print("\n5. Testing MCP Requests...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test initialize method
    initialize_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": True
                }
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    print("Testing initialize method...")
    response = requests.post(f"{API_BASE}/mcp", json=initialize_request, headers=headers)
    print(f"Initialize Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ MCP Initialize successful")
        print(f"Server Info: {result.get('result', {}).get('serverInfo', {})}")
        
        # Test tools/list method
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("\nTesting tools/list method...")
        response = requests.post(f"{API_BASE}/mcp", json=tools_request, headers=headers)
        print(f"Tools/List Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ MCP Tools/List successful")
            tools = result.get('result', {}).get('tools', [])
            print(f"Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}")
            return True
        else:
            print("❌ MCP Tools/List failed")
            print(f"Error: {response.text}")
            return False
    else:
        print("❌ MCP Initialize failed")
        print(f"Error: {response.text}")
        return False

def main():
    """Run the full OAuth + MCP test"""
    print("🧪 Testing Jean Memory MCP OAuth Implementation")
    print("=" * 50)
    
    # Step 1: OAuth Discovery
    discovery = test_oauth_discovery()
    if not discovery:
        return
    
    # Step 2: Client Registration
    client_info = test_client_registration()
    if not client_info:
        return
    
    # Step 3: Authorization Flow (manual step)
    code_verifier, auth_params = test_authorization_flow(client_info)
    
    print("\n" + "=" * 50)
    print("⚠️  MANUAL STEP REQUIRED")
    print("1. Visit the authorization URL above")
    print("2. Complete the OAuth login flow")
    print("3. Copy the 'code' parameter from the final redirect URL")
    print("4. Run this script again with the code as an argument")
    print("=" * 50)
    
    # For now, we'll stop here and let the user complete the manual step
    # In a real test, you would continue with token exchange and MCP requests

if __name__ == "__main__":
    main()