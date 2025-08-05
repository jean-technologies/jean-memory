#!/usr/bin/env python3
"""
Simple test to check MCP initialize response format
"""

import requests
import json

# Test with a mock Bearer token to see the response format
mock_token = "Bearer mock-jwt-token-for-testing"

initialize_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {
            "resources": {},
            "tools": {},
            "prompts": {}
        },
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    }
}

headers = {
    "Content-Type": "application/json",
    "Authorization": mock_token,
    "Origin": "https://claude.ai"
}

print("🧪 Testing MCP initialize response format...")
print("=" * 50)

try:
    response = requests.post(
        "https://jean-memory-api-virginia.onrender.com/mcp",
        json=initialize_request,
        headers=headers,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("\nResponse Body:")
    
    if response.status_code == 401:
        print("❌ Authentication failed (expected with mock token)")
        print(f"Response: {response.text}")
    else:
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            # Check if response has required MCP initialize fields
            if "result" in response_json:
                result = response_json["result"]
                required_fields = ["protocolVersion", "capabilities", "serverInfo"]
                
                print(f"\n📋 MCP Initialize Response Analysis:")
                for field in required_fields:
                    if field in result:
                        print(f"✅ {field}: present")
                    else:
                        print(f"❌ {field}: MISSING")
                
                if "serverInfo" in result:
                    server_info = result["serverInfo"]
                    if "name" in server_info and "version" in server_info:
                        print(f"✅ serverInfo complete: {server_info}")
                    else:
                        print(f"⚠️  serverInfo incomplete: {server_info}")
            else:
                print("❌ Response missing 'result' field")
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {response.text}")
            
except Exception as e:
    print(f"❌ Request failed: {e}")