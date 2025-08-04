#!/usr/bin/env python3
"""Test the chat enhance endpoint after fix"""

import requests
import json

API_BASE = "https://jean-memory-api-virginia.onrender.com"
API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"

def test_chat_enhance():
    print("🧪 Testing Chat Enhance Endpoint After Fix")
    print("=" * 50)
    
    # Test with a user who has been authenticated
    url = f"{API_BASE}/sdk/chat/enhance"
    
    payload = {
        "api_key": API_KEY,
        "client_name": "SDK Test",
        "user_id": "fa97efb5-410d-4806-b137-8cf13b6cb464",  # Your user ID from auth
        "messages": [
            {"role": "user", "content": "Hello, I need help with algebra"}
        ],
        "system_prompt": "You are a helpful math tutor"
    }
    
    print("Sending request...")
    print(f"User ID: {payload['user_id']}")
    print(f"Message: {payload['messages'][0]['content']}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success! Response:")
            print(f"Context retrieved: {data.get('context_retrieved')}")
            if data.get('user_context'):
                print(f"User context length: {len(data['user_context'])} chars")
                print(f"Context preview: {data['user_context'][:200]}...")
            else:
                print("❌ No user context returned")
            
            print(f"\nEnhanced messages: {len(data.get('enhanced_messages', []))}")
            for i, msg in enumerate(data.get('enhanced_messages', [])):
                print(f"  {i+1}. {msg['role']}: {msg['content'][:100]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_chat_enhance()