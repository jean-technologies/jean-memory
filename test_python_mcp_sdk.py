#!/usr/bin/env python3
"""
Test the MCP-integrated Python SDK
Uses jean_memory and store_document tools directly like Claude Desktop/Cursor
"""

from sdk.python.jeanmemory_mcp import JeanAgentMCP

def test_mcp_sdk():
    print("🧪 Testing Jean Memory MCP Python SDK...")
    print("=" * 60)
    
    # Create agent with math tutor system prompt
    agent = JeanAgentMCP(
        api_key='jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA',
        system_prompt='You are a helpful math tutor who explains step by step'
    )
    
    print("✅ MCP Python SDK initialized successfully")
    print("🚀 Starting interactive chat...")
    print("   This uses the same jean_memory tool as Claude Desktop/Cursor!")
    print("   Try asking: 'Help me solve 2x + 5 = 13'")
    print("   Type 'quit' to exit")
    print("=" * 60)
    
    # Start interactive session
    agent.run()

if __name__ == "__main__":
    test_mcp_sdk()