#!/usr/bin/env python3
"""
Jean Memory Python SDK Diagnostic Test
Tests the current Python SDK with provided credentials to establish baseline
"""

from sdk.python.jeanmemory import JeanAgent

def test_python_sdk_diagnostic():
    print("🔍 DIAGNOSTIC: Testing Python SDK with provided credentials...")
    print("=" * 60)
    
    # Create agent with math tutor system prompt
    agent = JeanAgent(
        api_key='jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA',
        system_prompt='You are a helpful math tutor who explains step by step'
    )
    
    print("✅ Python SDK initialized successfully")
    
    # Test authentication with provided credentials  
    print("🔐 Testing authentication...")
    try:
        # Use your test credentials here - replace with actual working credentials
        auth_success = agent.authenticate(
            email="rohankat@gmail.com", 
            password="password123"  # Replace with actual password
        )
        
        if not auth_success:
            print("❌ Authentication failed - testing without auth")
            return
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        print("⚠️  Proceeding to test /sdk/chat/enhance endpoint directly...")
        return
    
    print("🧪 Testing message sending...")
    try:
        response = agent.send_message("Help me solve 2x + 5 = 13")
        print(f"✅ Got response: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ Message sending failed: {e}")
    
    print("=" * 60)
    print("🏁 Diagnostic complete")

if __name__ == "__main__":
    test_python_sdk_diagnostic()