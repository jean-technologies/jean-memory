#!/usr/bin/env python3
"""
Detailed MCP Flow Test - Shows complete request/response cycle
"""

import requests
import json
import time
import uuid
from typing import Dict, Any

def test_detailed_flow():
    """Run a detailed test showing the complete MCP flow"""
    
    BASE_URL = "https://jean-memory-api-virginia.onrender.com"
    USER_ID = "66d3d5d1-fc48-44a7-bbc0-1efa2e164fad"
    CLIENT_NAME = "cursor"
    endpoint_url = f"{BASE_URL}/mcp/v2/{CLIENT_NAME}/{USER_ID}"
    
    session = requests.Session()
    session.headers.update({
        'Content-Type': 'application/json',
        'x-user-id': USER_ID,
        'x-client-name': CLIENT_NAME
    })
    
    print("=" * 80)
    print("🔍 DETAILED MCP PROTOCOL FLOW ANALYSIS")
    print("=" * 80)
    print(f"🎯 Endpoint: {endpoint_url}")
    print(f"📋 Headers: {dict(session.headers)}")
    
    # Test 1: Short query (no context needed)
    print(f"\n{'='*60}")
    print("📝 TEST 1: SHORT QUERY (needs_context=false)")
    print('='*60)
    
    request1 = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": str(uuid.uuid4()),
        "params": {
            "name": "jean_memory",
            "arguments": {
                "user_message": "What's 2+2?",
                "is_new_conversation": False,
                "needs_context": False
            }
        }
    }
    
    print("📤 REQUEST:")
    print(json.dumps(request1, indent=2))
    
    start_time = time.time()
    response1 = session.post(endpoint_url, json=request1)
    response_time = time.time() - start_time
    
    print(f"\n📥 RESPONSE (Status: {response1.status_code}, Time: {response_time:.3f}s):")
    if response1.status_code == 200:
        response_data = response1.json()
        print(json.dumps(response_data, indent=2))
        
        # Analyze the response structure
        if "result" in response_data and "content" in response_data["result"]:
            content = response_data["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                print(f"\n📄 EXTRACTED TEXT ({len(text_content)} chars):")
                print("-" * 40)
                print(text_content)
                print("-" * 40)
    else:
        print(response1.text)
    
    # Test 2: Context query (new conversation)
    print(f"\n{'='*60}")
    print("🆕 TEST 2: NEW CONVERSATION (is_new_conversation=true, needs_context=true)")
    print('='*60)
    
    request2 = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": str(uuid.uuid4()),
        "params": {
            "name": "jean_memory",
            "arguments": {
                "user_message": "Help me plan my career transition",
                "is_new_conversation": True,
                "needs_context": True
            }
        }
    }
    
    print("📤 REQUEST:")
    print(json.dumps(request2, indent=2))
    
    start_time = time.time()
    response2 = session.post(endpoint_url, json=request2)
    response_time = time.time() - start_time
    
    print(f"\n📥 RESPONSE (Status: {response2.status_code}, Time: {response_time:.3f}s):")
    if response2.status_code == 200:
        response_data = response2.json()
        print(json.dumps(response_data, indent=2)[:2000] + "..." if len(json.dumps(response_data, indent=2)) > 2000 else json.dumps(response_data, indent=2))
        
        # Analyze the response structure
        if "result" in response_data and "content" in response_data["result"]:
            content = response_data["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                print(f"\n📄 EXTRACTED TEXT ({len(text_content)} chars):")
                print("-" * 40)
                print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
                print("-" * 40)
    else:
        print(response2.text)
    
    # Test 3: Deep context query
    print(f"\n{'='*60}")
    print("🧠 TEST 3: DEEP CONTEXT QUERY (needs_context=true)")
    print('='*60)
    
    request3 = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "id": str(uuid.uuid4()),
        "params": {
            "name": "jean_memory",
            "arguments": {
                "user_message": "Continue working on the Python API we discussed",
                "is_new_conversation": False,
                "needs_context": True
            }
        }
    }
    
    print("📤 REQUEST:")
    print(json.dumps(request3, indent=2))
    
    start_time = time.time()
    response3 = session.post(endpoint_url, json=request3)
    response_time = time.time() - start_time
    
    print(f"\n📥 RESPONSE (Status: {response3.status_code}, Time: {response_time:.3f}s):")
    if response3.status_code == 200:
        response_data = response3.json()
        print(json.dumps(response_data, indent=2)[:2000] + "..." if len(json.dumps(response_data, indent=2)) > 2000 else json.dumps(response_data, indent=2))
        
        # Analyze the response structure
        if "result" in response_data and "content" in response_data["result"]:
            content = response_data["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                print(f"\n📄 EXTRACTED TEXT ({len(text_content)} chars):")
                print("-" * 40)
                print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
                print("-" * 40)
    else:
        print(response3.text)
    
    # Summary
    print(f"\n{'='*80}")
    print("📋 MCP PROTOCOL FLOW SUMMARY")
    print('='*80)
    print("1. 🏗️  REQUEST STRUCTURE:")
    print("   - JSON-RPC 2.0 format with method='tools/call'")
    print("   - Parameters include tool name and arguments")
    print("   - Headers include x-user-id and x-client-name")
    print("")
    print("2. 🔄 PROCESSING FLOW:")
    print("   - HTTP POST to /mcp/v2/{client}/{user_id}")
    print("   - Server validates headers and request format") 
    print("   - jean_memory tool processes the request:")
    print("     * needs_context=false: Quick response, minimal processing")
    print("     * needs_context=true: Context retrieval, memory analysis")
    print("     * is_new_conversation=true: Comprehensive context synthesis")
    print("")
    print("3. 📤 RESPONSE STRUCTURE:")
    print("   - JSON-RPC 2.0 format with result field")
    print("   - Content array with text objects")
    print("   - Includes request ID for correlation")
    print("")
    print("4. ⏱️  PERFORMANCE CHARACTERISTICS:")
    print("   - Short queries: ~100-200ms (fast, no context needed)")
    print("   - New conversations: ~130-150ms (context synthesis)")
    print("   - Deep context: ~13-15s (comprehensive memory search)")

if __name__ == "__main__":
    test_detailed_flow()