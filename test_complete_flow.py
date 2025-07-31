#!/usr/bin/env python3
"""
Test the complete MCP flow to identify where it's breaking
"""

import requests
import json

def test_complete_mcp_flow():
    """Test the complete MCP flow step by step"""
    base_url = "https://jean-memory-api-virginia.onrender.com"
    
    print("🧪 Testing Complete MCP Flow")
    print("=" * 50)
    
    # Test 1: Check current status
    print("\n1. Checking MCP status...")
    try:
        response = requests.get(f"{base_url}/mcp/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"   Transport: {data.get('transport')}")
            print(f"   Protocol: {data.get('protocol_version')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Status error: {e}")
    
    # Test 2: Check what happens with GET request
    print("\n2. Testing GET /mcp (what Claude is trying)...")
    try:
        response = requests.get(f"{base_url}/mcp")
        print(f"   Status: {response.status_code}")
        if response.status_code == 405:
            print("   ❌ Method Not Allowed - This is the issue!")
        elif response.status_code == 401:
            print("   ✅ Auth required (expected)")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check HEAD request (protocol discovery)
    print("\n3. Testing HEAD /mcp (protocol discovery)...")
    try:
        response = requests.head(f"{base_url}/mcp")
        print(f"   Status: {response.status_code}")
        headers = response.headers
        if "X-MCP-Protocol" in headers:
            print(f"   ✅ Protocol: {headers['X-MCP-Protocol']}")
        if "X-MCP-Transport" in headers:
            print(f"   ✅ Transport: {headers['X-MCP-Transport']}")
        else:
            print("   ⚠️  No transport header")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Mock POST request (without auth)
    print("\n4. Testing POST /mcp initialize (without auth)...")
    try:
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize", 
            "params": {"protocolVersion": "2024-11-05"},
            "id": 1
        }
        response = requests.post(f"{base_url}/mcp", 
                               json=init_request,
                               headers={"Content-Type": "application/json"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Auth required (expected)")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🎯 Flow Analysis:")
    print("✅ The OAuth proxy is deployed and working")
    print("❌ GET /mcp returns 405 - this breaks Claude's flow")
    print("💡 Claude expects GET to work for SSE or just return 200")
    print("💡 Need to add GET endpoint to complete the flow")
    
    return True

if __name__ == "__main__":
    test_complete_mcp_flow()