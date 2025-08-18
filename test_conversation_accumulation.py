#!/usr/bin/env python3
"""
Test conversation accumulation effect on memory retrieval
"""

import requests
import json

JEAN_API_BASE = "https://jean-memory-api-virginia.onrender.com"
API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"
TEST_USER_ID = "fa97efb5-410d-4806-b137-8cf13b6cb464"

def test_single_vs_accumulated_messages():
    print("🔍 TESTING: Single message vs accumulated conversation")
    print("=" * 60)
    
    # Test 1: Single message (like React SDK and our first diagnostic)
    print("1️⃣ Testing single message...")
    single_payload = {
        "api_key": API_KEY,
        "client_name": "Single Message Test",
        "user_id": TEST_USER_ID,
        "messages": [
            {"role": "user", "content": "Help me solve 2x + 5 = 13"}
        ],
        "system_prompt": "You are a helpful math tutor"
    }
    
    try:
        response = requests.post(f"{JEAN_API_BASE}/sdk/chat/enhance", json=single_payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Single message - Context: {len(data.get('user_context', '')) if data.get('user_context') else 0} chars")
        
    except Exception as e:
        print(f"❌ Single message test failed: {e}")
    
    print("\n" + "-" * 40 + "\n")
    
    # Test 2: Accumulated conversation (like Python SDK after multiple messages)
    print("2️⃣ Testing accumulated conversation...")
    accumulated_payload = {
        "api_key": API_KEY,
        "client_name": "Accumulated Test",
        "user_id": TEST_USER_ID,
        "messages": [
            {"role": "user", "content": "Hello, I need help with math"},
            {"role": "assistant", "content": "I'd be happy to help you with math! What specific problem are you working on?"},
            {"role": "user", "content": "Can you help me with algebra?"},
            {"role": "assistant", "content": "Absolutely! I can help with various algebra topics. What would you like to work on?"},
            {"role": "user", "content": "Help me solve 2x + 5 = 13"}
        ],
        "system_prompt": "You are a helpful math tutor"
    }
    
    try:
        response = requests.post(f"{JEAN_API_BASE}/sdk/chat/enhance", json=accumulated_payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Accumulated messages - Context: {len(data.get('user_context', '')) if data.get('user_context') else 0} chars")
        
        if data.get('user_context'):
            print(f"📄 Context preview: {data['user_context'][:100]}...")
        else:
            print("❗ No context retrieved!")
            
    except Exception as e:
        print(f"❌ Accumulated test failed: {e}")
    
    print("=" * 60)
    print("🏁 Conversation accumulation test complete")

if __name__ == "__main__":
    test_single_vs_accumulated_messages()