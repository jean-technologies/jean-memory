#!/usr/bin/env python3
"""
Debug the initialize response to see why tools/list isn't called
"""

import requests
import json

def debug_initialize_response():
    """Debug what our initialize response looks like"""
    
    # Test V2 endpoint first (working)
    print("🔍 Testing V2 endpoint initialize...")
    v2_response = requests.post(
        "https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/test-user-id",
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
            "id": 1
        }
    )
    
    print(f"V2 Status: {v2_response.status_code}")
    if v2_response.status_code == 200:
        v2_data = v2_response.json()
        print("V2 Initialize Response:")
        print(json.dumps(v2_data, indent=2))
        
        # Check capabilities
        capabilities = v2_data.get('result', {}).get('capabilities', {})
        tools_capability = capabilities.get('tools', {})
        print(f"\nV2 Tools Capability: {tools_capability}")
    
    print("\n" + "="*50)
    
    # Test tools/list on V2
    print("\n🔍 Testing V2 tools/list...")
    v2_tools = requests.post(
        "https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/test-user-id",
        json={
            "jsonrpc": "2.0", 
            "method": "tools/list",
            "id": 2
        }
    )
    
    print(f"V2 Tools/List Status: {v2_tools.status_code}")
    if v2_tools.status_code == 200:
        tools_data = v2_tools.json()
        tools = tools_data.get('result', {}).get('tools', [])
        print(f"V2 Tools Count: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.get('name')}: {tool.get('description', '')[:50]}...")
    
    print("\n" + "="*50)
    
    # Test OAuth proxy (without auth - will fail but show format)
    print("\n🔍 Testing OAuth proxy initialize (will fail auth)...")
    oauth_response = requests.post(
        "https://jean-memory-api-virginia.onrender.com/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "initialize", 
            "params": {"protocolVersion": "2024-11-05"},
            "id": 1
        }
    )
    
    print(f"OAuth Status: {oauth_response.status_code}")
    print(f"OAuth Response: {oauth_response.text}")
    
    return True

if __name__ == "__main__":
    debug_initialize_response()