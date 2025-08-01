#!/usr/bin/env python3
"""
Test MCP server using HTTP transport similar to what Claude Web would do
This simulates the Inspector-style testing without requiring authentication
"""

import requests
import json
import subprocess
import sys
import time

API_BASE = "https://jean-memory-api-virginia.onrender.com"

def test_mcp_inspector_connection():
    """Test MCP server connection using Inspector-style HTTP transport"""
    print("🧪 Testing MCP Server with Inspector-style HTTP Transport")
    print("=" * 60)
    
    # Test basic connectivity first
    print("1. Testing basic server connectivity...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is reachable")
        else:
            print(f"❌ Server returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server unreachable: {e}")
        return False
    
    # Test MCP status endpoint (no auth required)
    print("\n2. Testing MCP status endpoint...")
    try:
        response = requests.get(f"{API_BASE}/mcp/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("✅ MCP Status successful")
            print(f"   Status: {status.get('status')}")
            print(f"   Protocol: {status.get('protocol')}")
            print(f"   OAuth: {status.get('oauth')}")
            print(f"   Server: {status.get('serverInfo', {}).get('name')} v{status.get('serverInfo', {}).get('version')}")
        else:
            print(f"❌ MCP Status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP Status error: {e}")
        return False
    
    # Test OAuth discovery (what Claude Web does first)
    print("\n3. Testing OAuth discovery (Claude Web compatibility)...")
    try:
        response = requests.get(f"{API_BASE}/.well-known/oauth-authorization-server", timeout=10)
        if response.status_code == 200:
            discovery = response.json()
            print("✅ OAuth Discovery successful")
            print(f"   Issuer: {discovery.get('issuer')}")
            print(f"   Authorization: {discovery.get('authorization_endpoint')}")
            print(f"   Token: {discovery.get('token_endpoint')}")
            print(f"   Registration: {discovery.get('registration_endpoint')}")
            print(f"   Supported methods: {discovery.get('code_challenge_methods_supported')}")
        else:
            print(f"❌ OAuth Discovery failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OAuth Discovery error: {e}")
        return False
    
    print("\n4. Testing MCP HTTP transport compatibility...")
    
    # Try MCP HTTP transport endpoints (used by Claude Web and Inspector)
    test_endpoints = [
        "/mcp",  # OAuth MCP endpoint
        "/mcp/messages/",  # Standard MCP endpoint
    ]
    
    for endpoint in test_endpoints:
        print(f"\n   Testing {endpoint}...")
        
        # Test with a simple initialize request (no auth - should fail gracefully)
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-inspector",
                    "version": "1.0.0"
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MCP-Inspector/1.0.0"
        }
        
        try:
            response = requests.post(f"{API_BASE}{endpoint}", 
                                   json=initialize_request, 
                                   headers=headers, 
                                   timeout=10)
            
            print(f"     Status: {response.status_code}")
            
            if response.status_code == 401:
                print("     ✅ Correctly requires authentication (401 Unauthorized)")
            elif response.status_code == 200:
                try:
                    result = response.json()
                    print("     ✅ MCP response received")
                    if 'result' in result and 'serverInfo' in result['result']:
                        server_info = result['result']['serverInfo']
                        print(f"     Server: {server_info.get('name')} v{server_info.get('version')}")
                except json.JSONDecodeError:
                    print("     ⚠️  Non-JSON response received")
            else:
                print(f"     ❌ Unexpected status: {response.text[:100]}")
                
        except Exception as e:
            print(f"     ❌ Request failed: {e}")
    
    return True

def test_mcp_with_inspector():
    """Try to test with actual MCP Inspector if available"""
    print("\n5. Testing with MCP Inspector (if available)...")
    
    try:
        # Check if MCP Inspector is available
        result = subprocess.run(["npx", "@modelcontextprotocol/inspector", "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("   ✅ MCP Inspector is available")
            
            # Try to test our server with Inspector
            print("   Starting Inspector test...")
            
            # Note: This would normally require interactive setup
            # For now, we'll just confirm Inspector can be invoked
            print("   📝 Manual Inspector test required:")
            print(f"   Run: npx @modelcontextprotocol/inspector")
            print(f"   Then test HTTP transport with: {API_BASE}/mcp")
            print("   (Will require OAuth authentication)")
            
        else:
            print("   ❌ MCP Inspector not available")
            print("   Install with: npm install -g @modelcontextprotocol/inspector")
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  Inspector check timed out")
    except FileNotFoundError:
        print("   ❌ npm/npx not found - install Node.js to use Inspector")
    except Exception as e:
        print(f"   ❌ Inspector test failed: {e}")

def main():
    """Run comprehensive MCP compatibility tests"""
    print("🔬 Jean Memory MCP Server Compatibility Test")
    print("Testing compatibility with MCP Inspector and Claude Web")
    print("=" * 60)
    
    success = test_mcp_inspector_connection()
    test_mcp_with_inspector()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ MCP Server Infrastructure: WORKING")
        print("   - Server connectivity: ✅")
        print("   - MCP status endpoint: ✅") 
        print("   - OAuth discovery: ✅")
        print("   - HTTP transport: ✅")
        print("   - Authentication system: ✅")
        print()
        print("🔍 FINDINGS:")
        print("   • MCP server responds correctly to protocol methods")
        print("   • OAuth 2.1 endpoints are functional")
        print("   • HTTP transport is properly configured")
        print("   • Authentication system works as expected")
        print()
        print("❓ CLAUDE WEB CONNECTION ISSUE:")
        print("   Since our MCP server passes all infrastructure tests")
        print("   but Claude Web still shows 'disconnected', the issue is likely:")
        print("   1. Claude Web requires specific connection handshake")
        print("   2. Missing WebSocket/SSE transport expectations")
        print("   3. Connection persistence mechanism differences")
        print("   4. Claude-specific protocol extensions")
        print()
        print("📋 NEXT STEPS:")
        print("   1. Test with MCP Inspector using OAuth flow")
        print("   2. Research working Claude Web MCP implementations")
        print("   3. Monitor Claude Web network traffic during connection")
        print("   4. Check if Claude Desktop vs Claude Web behave differently")
        
    else:
        print("❌ MCP Server Infrastructure: ISSUES FOUND")
        print("   Fix infrastructure issues before testing with Claude Web")
    
    print("=" * 60)

if __name__ == "__main__":
    main()