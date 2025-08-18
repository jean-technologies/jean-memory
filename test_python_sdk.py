#!/usr/bin/env python3
"""
Jean Memory Python SDK Test Script
Tests the working Python CLI to establish baseline functionality
"""

from sdk.python.jeanmemory import JeanAgent

def test_python_sdk():
    print("🧪 Testing Jean Memory Python SDK...")
    print("=" * 50)
    
    # Create agent with math tutor system prompt
    agent = JeanAgent(
        api_key='jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA',
        system_prompt='You are a helpful math tutor who explains step by step'
    )
    
    print("✅ Python SDK initialized successfully")
    print("🚀 Starting interactive chat...")
    print("   Try asking: 'Help me solve 2x + 5 = 13'")
    print("   Type 'quit' to exit")
    print("=" * 50)
    
    # Start interactive session
    agent.run()

if __name__ == "__main__":
    test_python_sdk()