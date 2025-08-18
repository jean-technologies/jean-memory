#!/usr/bin/env python3
"""
Jean Memory SDK Memory Retrieval Diagnostic
Direct test of /sdk/chat/enhance endpoint to understand retrieval differences
"""

import requests
import json

JEAN_API_BASE = "https://jean-memory-api-virginia.onrender.com"
API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"

def test_memory_retrieval():
    print("🔍 DIAGNOSTIC: Testing /sdk/chat/enhance endpoint directly")
    print("=" * 60)
    
    # Test user ID from previous testing (replace with actual user ID if known)
    test_user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"  # From API key validation
    
    # Test Python SDK style (continuing conversation)
    print("🐍 Testing Python SDK style (continuing conversation)...")
    python_payload = {
        "api_key": API_KEY,
        "client_name": "Python Diagnostic",
        "user_id": test_user_id,
        "messages": [
            {"role": "user", "content": "Help me solve 2x + 5 = 13"}
        ],
        "system_prompt": "You are a helpful math tutor who explains step by step"
    }
    
    try:
        response = requests.post(f"{JEAN_API_BASE}/sdk/chat/enhance", json=python_payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Python style response received")
        print(f"🧠 Context retrieved: {data.get('context_retrieved', False)}")
        print(f"📝 User context length: {len(data.get('user_context', '')) if data.get('user_context') else 0} chars")
        print(f"💬 Enhanced messages count: {len(data.get('enhanced_messages', []))}")
        
        if data.get('user_context'):
            print(f"📄 Context preview: {data['user_context'][:100]}...")
        
    except Exception as e:
        print(f"❌ Python style test failed: {e}")
    
    print("\n" + "-" * 40 + "\n")
    
    # Test React SDK style (new conversation) 
    print("⚛️ Testing React SDK style (new conversation)...")
    react_payload = {
        "api_key": API_KEY,
        "client_name": "React Diagnostic", 
        "user_id": test_user_id,
        "messages": [
            {"role": "user", "content": "Help me solve 2x + 5 = 13"}
        ],
        "system_prompt": "You are a helpful math tutor who explains step by step"
    }
    
    try:
        response = requests.post(f"{JEAN_API_BASE}/sdk/chat/enhance", json=react_payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ React style response received")
        print(f"🧠 Context retrieved: {data.get('context_retrieved', False)}")
        print(f"📝 User context length: {len(data.get('user_context', '')) if data.get('user_context') else 0} chars")
        print(f"💬 Enhanced messages count: {len(data.get('enhanced_messages', []))}")
        
        if data.get('user_context'):
            print(f"📄 Context preview: {data['user_context'][:100]}...")
            
    except Exception as e:
        print(f"❌ React style test failed: {e}")
    
    print("=" * 60)
    print("🏁 Memory retrieval diagnostic complete")

if __name__ == "__main__":
    test_memory_retrieval()