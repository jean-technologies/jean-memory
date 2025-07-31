#!/usr/bin/env python3
"""
Test tools/list specifically on the OAuth proxy endpoint
"""

import requests
import json
import os

def test_oauth_tools():
    """Test tools/list on OAuth proxy (will fail without proper auth)"""
    base_url = "https://jean-memory-api-virginia.onrender.com"
    
    print("🧪 Testing OAuth Proxy Tools/List")
    print("=" * 50)
    
    # This will fail with 401, but we can see if the method is routed correctly
    test_methods = [
        "initialize",
        "notifications/initialized", 
        "tools/list",
        "resources/list",
        "prompts/list"
    ]
    
    for method in test_methods:
        print(f"\n🔍 Testing {method}...")
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "id": 1
            }
            
            if method == "initialize":
                payload["params"] = {"protocolVersion": "2024-11-05"}
            
            response = requests.post(f"{base_url}/mcp", 
                                   json=payload,
                                   headers={"Content-Type": "application/json"})
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Auth required (expected)")
            elif response.status_code == 200:
                data = response.json()
                if method == "tools/list":
                    tools = data.get('result', {}).get('tools', [])
                    print(f"   ✅ Found {len(tools)} tools!")
                    for tool in tools:
                        print(f"      - {tool.get('name')}")
                else:
                    print(f"   ✅ Success: {str(data)[:100]}...")
            else:
                print(f"   ❌ Unexpected: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n💡 Key Insight:")
    print(f"   If tools/list returns 401 like other methods, routing works")
    print(f"   If tools/list returns different status, there's a routing issue")
    
    return True

if __name__ == "__main__":
    test_oauth_tools()