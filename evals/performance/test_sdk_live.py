#!/usr/bin/env python3
"""Live test of Jean Memory SDK with real API key"""

import sys
import os

# Add SDK python path
sdk_path = os.path.join(os.path.dirname(__file__), 'sdk', 'python')
sys.path.insert(0, sdk_path)

from jeanmemory import JeanAgent

# Your actual API key
API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"

def test_sdk_basic():
    print("🧪 Testing Jean Memory SDK Basic Functionality")
    print("=" * 60)
    
    try:
        # Initialize agent
        print("\n1. Initializing JeanAgent...")
        agent = JeanAgent(
            api_key=API_KEY,
            system_prompt="You are a helpful math tutor",
            client_name="SDK Test"
        )
        print("✅ Agent initialized successfully!")
        
        # Print agent info
        print(f"\n2. Agent Configuration:")
        print(f"   - System Prompt: {agent.system_prompt}")
        print(f"   - Client Name: {agent.client_name}")
        print(f"   - Modality: {agent.modality}")
        print(f"   - User Authenticated: {agent.user is not None}")
        
        print("\n3. To test authentication:")
        print("   Run: agent.authenticate()")
        print("   You'll be prompted for your Jean Memory email and password")
        
        print("\n4. To start interactive chat:")
        print("   Run: agent.run()")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    agent = test_sdk_basic()
    
    if agent:
        print("\n" + "=" * 60)
        print("📝 Next Steps:")
        print("1. Run this in Python interactive mode: python -i test_sdk_live.py")
        print("2. Then run: agent.authenticate()")
        print("3. Use your Jean Memory credentials when prompted")
        print("4. If auth succeeds, run: agent.run() to start chatting")