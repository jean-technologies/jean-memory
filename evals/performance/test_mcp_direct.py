#!/usr/bin/env python3
"""
Direct MCP protocol test using API key authentication
This bypasses OAuth to test MCP protocol compliance directly
"""

import requests
import json
import os

API_BASE = "https://jean-memory-api-virginia.onrender.com"

# You'll need to set this environment variable with a valid API key
API_KEY = os.getenv("JEAN_MEMORY_API_KEY")
TEST_USER_ID = os.getenv("JEAN_MEMORY_TEST_USER_ID")  # Optional - will use default if not set

def test_mcp_direct():
    """Test MCP protocol directly using API key authentication"""
    print("🧪 Testing MCP Protocol Compliance (Direct)")
    print("=" * 50)
    
    if not API_KEY:
        print("❌ Error: JEAN_MEMORY_API_KEY environment variable not set")
        print("Please set your API key: export JEAN_MEMORY_API_KEY='your-key-here'")
        return False
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "x-client-name": "test-mcp-client"
    }
    
    if TEST_USER_ID:
        headers["x-user-id"] = TEST_USER_ID
    
    print(f"Using API Key: {API_KEY[:10]}...")
    print(f"Testing endpoint: {API_BASE}/mcp/messages/")
    
    # Test 1: Initialize method
    print("\n1. Testing MCP Initialize Method...")
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
                "name": "test-mcp-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = requests.post(f"{API_BASE}/mcp/messages/", json=initialize_request, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print("✅ MCP Initialize successful")
            server_info = result.get('result', {}).get('serverInfo', {})
            capabilities = result.get('result', {}).get('capabilities', {})
            protocol_version = result.get('result', {}).get('protocolVersion', 'unknown')
            
            print(f"  Protocol Version: {protocol_version}")
            print(f"  Server Name: {server_info.get('name', 'unknown')}")
            print(f"  Server Version: {server_info.get('version', 'unknown')}")
            print(f"  Capabilities: {list(capabilities.keys())}")
            
            # Test 2: Tools/List method
            print("\n2. Testing Tools/List Method...")
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            response = requests.post(f"{API_BASE}/mcp/messages/", json=tools_request, headers=headers)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print("✅ Tools/List successful")
                    tools = result.get('result', {}).get('tools', [])
                    print(f"  Available tools: {len(tools)}")
                    
                    for i, tool in enumerate(tools[:5]):  # Show first 5 tools
                        name = tool.get('name', 'unknown')
                        description = tool.get('description', 'No description')
                        print(f"    {i+1}. {name}: {description}")
                    
                    if len(tools) > 5:
                        print(f"    ... and {len(tools) - 5} more tools")
                    
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"Raw response: {response.text}")
                    return False
            else:
                print(f"❌ Tools/List failed: {response.text}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"Raw response: {response.text}")
            return False
    else:
        print(f"❌ MCP Initialize failed: {response.text}")
        return False

def test_health_endpoints():
    """Test various health endpoints"""
    print("\n3. Testing Health Endpoints...")
    
    endpoints = [
        "/health",
        "/mcp/status"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        response = requests.get(f"{API_BASE}{endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"✅ {endpoint} successful")
                print(f"   Response: {json.dumps(result, indent=2)}")
            except json.JSONDecodeError:
                print(f"✅ {endpoint} successful (non-JSON response)")
                print(f"   Response: {response.text}")
        else:
            print(f"❌ {endpoint} failed: {response.text}")

def main():
    """Run the MCP protocol compliance test"""
    success = test_mcp_direct()
    test_health_endpoints()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ MCP Protocol Compliance Test: PASSED")
        print("The MCP server is responding correctly to protocol methods.")
        print("If Claude Web still shows disconnected, the issue is likely:")
        print("  1. Claude Web-specific connection requirements")
        print("  2. Transport protocol expectations")
        print("  3. Connection persistence mechanisms")
    else:
        print("❌ MCP Protocol Compliance Test: FAILED")
        print("There are issues with the MCP protocol implementation.")
    print("=" * 50)

if __name__ == "__main__":
    main()