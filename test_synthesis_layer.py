#!/usr/bin/env python3
"""
Test script for the new synthesis layer implementation
Tests natural conversational responses vs meta-commentary
"""

from sdk.python.jeanmemory_mcp import JeanAgentMCP

def test_synthesis_layer():
    """Test the synthesis layer implementation"""
    print("🧪 Testing Jean Memory MCP SDK with Synthesis Layer")
    print("=" * 60)
    
    # Create agent with test credentials
    agent = JeanAgentMCP(
        api_key="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
        system_prompt="You are a patient math tutor who explains concepts step by step",
        client_name="Python MCP Test"
    )
    
    # Authenticate (you'll need to enter credentials)
    print("🔐 Please authenticate with your Jean Memory account...")
    if not agent.authenticate():
        print("❌ Authentication failed. Cannot continue test.")
        return
    
    print("\n✅ Authentication successful!")
    print("\n🧠 Testing synthesis layer with math tutor scenario...")
    print("=" * 60)
    
    # Test message that should trigger context retrieval
    test_message = "I'm struggling with calculus derivatives"
    
    print(f"👤 User: {test_message}")
    print("🤔 Processing... (calling jean_memory + synthesis)")
    
    try:
        # Send message and get synthesized response
        response = agent.send_message(test_message)
        
        print(f"🤖 Assistant: {response}")
        print("\n" + "=" * 60)
        
        # Analyze response quality
        if "retrieved" in response.lower() or "characters" in response.lower():
            print("❌ ISSUE: Response contains meta-commentary about retrieval")
            print("   Expected: Natural conversational response as math tutor")
        elif "calculus" in response.lower() or "derivative" in response.lower() or "math" in response.lower():
            print("✅ SUCCESS: Response appears natural and contextually relevant")
        else:
            print("⚠️  UNCLEAR: Response doesn't contain retrieval meta-commentary")
            print("   But also doesn't clearly address the math question")
        
        print(f"\n📊 Response length: {len(response)} characters")
        print(f"📝 Response type: {'Natural conversation' if 'retrieved' not in response.lower() else 'Meta-commentary'}")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    print("\n🏁 Test completed. Check the response quality above.")

if __name__ == "__main__":
    test_synthesis_layer()