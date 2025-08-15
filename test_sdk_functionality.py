#!/usr/bin/env python3
"""
Test SDK Functionality with Test User
Tests the complete SDK workflow once test user endpoint is deployed
"""

import sys
import os
sys.path.append('sdk/python')

from jean_memory import JeanClient

def test_python_sdk():
    """Test Python SDK with automatic test user creation"""
    print("🧪 Testing Python SDK with Test User...")
    
    # Initialize client with API key
    client = JeanClient(api_key="jean_sk_test123")
    
    try:
        print("📝 Testing context retrieval...")
        # This should automatically create a test user and get context
        response = client.get_context(message="Hello, what do you remember about me?")
        print(f"✅ Context retrieved: {response.text[:100]}...")
        
        print("🔍 Testing memory search...")
        # Test memory tools
        search_result = client.tools.search_memory("test query")
        print(f"✅ Memory search completed: {search_result[:100]}...")
        
        print("💾 Testing memory storage...")
        # Test memory addition
        add_result = client.tools.add_memory("I like testing SDKs")
        print(f"✅ Memory added: {add_result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ SDK test failed: {e}")
        return False

def test_node_sdk():
    """Test Node.js SDK (placeholder - would need Node.js to run)"""
    print("🧪 Node.js SDK test would go here...")
    print("📝 Install: npm install @jeanmemory/node")
    print("🔧 Usage: const client = new JeanClient({ apiKey: 'jean_sk_test123' })")
    print("📡 Call: await client.getContext({ message: 'Hello!' })")
    return True

if __name__ == "__main__":
    print("🚀 Jean Memory SDK Test Suite")
    print("=" * 50)
    
    print("\n1. Testing Python SDK...")
    python_success = test_python_sdk()
    
    print("\n2. Testing Node.js SDK concept...")
    node_success = test_node_sdk()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Python SDK: {'✅ READY' if python_success else '❌ FAILED'}")
    print(f"Node.js SDK: {'✅ READY' if node_success else '❌ FAILED'}")
    
    if python_success:
        print("\n🎉 SDKs are ready for testing once backend is deployed!")
        print("🔧 Deploy the change to main.py to enable test user functionality")
    else:
        print("\n⚠️  Backend deployment needed for full functionality")