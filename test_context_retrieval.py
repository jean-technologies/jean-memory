#!/usr/bin/env python3
"""
Test context retrieval after backend fix
"""
from jeanmemory import JeanClient

print("🧪 Testing Context Retrieval After Fix")
print("="*40)

try:
    # Initialize client
    print("1. Initializing client...")
    client = JeanClient(api_key="jean_sk_test123")
    
    # Test context retrieval (this should work now)
    print("2. Testing context retrieval...")
    response = client.get_context(message="What do you remember about me?")
    print(f"✅ Context retrieved successfully!")
    print(f"📄 Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"🔍 Error type: {type(e).__name__}")

print("\n" + "="*40)
print("🔧 Note: Backend needs to be deployed for this fix to take effect")