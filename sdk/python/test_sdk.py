#!/usr/bin/env python3
"""
Test script for Jean Memory Python SDK
Run this to verify the SDK works with your API key
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from jeanmemory import JeanAgent

def test_api_key_validation():
    """Test that API key validation works"""
    print("🧪 Testing API key validation...")
    
    try:
        agent = JeanAgent(
            api_key="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
            system_prompt="You are a test assistant.",
            client_name="SDK Test"
        )
        print("✅ API key validation passed!")
        return agent
    except Exception as e:
        print(f"❌ API key validation failed: {e}")
        return None

def test_authentication():
    """Test user authentication"""
    print("\n🧪 Testing user authentication...")
    
    agent = test_api_key_validation()
    if not agent:
        return False
    
    # Test with provided credentials
    success = agent.authenticate(
        email="rohankatakam@yahoo.com",
        password="Sportnut2!"
    )
    
    if success:
        print("✅ User authentication passed!")
        return agent
    else:
        print("❌ User authentication failed")
        return None

def test_message_sending():
    """Test sending a message"""
    print("\n🧪 Testing message sending...")
    
    agent = test_authentication()
    if not agent:
        return False
    
    try:
        response = agent.send_message("Hello! This is a test message.")
        print(f"✅ Message sent successfully!")
        print(f"📝 Response: {response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Message sending failed: {e}")
        return False

def run_full_test():
    """Run all tests"""
    print("🚀 Jean Memory Python SDK Test Suite")
    print("=" * 50)
    
    if test_message_sending():
        print("\n🎉 All tests passed! SDK is working correctly.")
        
        print("\n📋 You can now use the SDK in your projects:")
        print("""
from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
    system_prompt="You are a helpful assistant."
)
agent.run()
        """)
    else:
        print("\n❌ Some tests failed. Please check your configuration.")

if __name__ == "__main__":
    run_full_test()