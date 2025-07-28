"""
Validate MCP tool schemas and responses
"""
import asyncio
import httpx
import json

async def validate_tools_schema():
    """Validate that Claude Code gets session tools in session mode"""
    
    # Test 1: Standard Claude Code connection (should NOT have session tools)
    standard_endpoint = "http://localhost:8765/mcp/claude%20code/messages/test_user"
    standard_request = {
        "jsonrpc": "2.0",
        "id": "test_standard",
        "method": "tools/list",
        "params": {}
    }
    
    # Test 2: Session Claude Code connection (should HAVE session tools)
    session_endpoint = "http://localhost:8765/mcp/claude%20code/messages/test_user/session/dev_session/agent1"
    session_request = {
        "jsonrpc": "2.0", 
        "id": "test_session",
        "method": "tools/list",
        "params": {}
    }
    
    results = {}
    
    # Test standard connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                standard_endpoint,
                json=standard_request,
                headers={"x-user-id": "test_user", "x-client-name": "claude code"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("result", {}).get("tools", [])
                tool_names = [t["name"] for t in tools]
                
                session_tools = ["claim_files", "release_files", "sync_codebase", "broadcast_message", "get_agent_messages"]
                has_session_tools = any(tool in tool_names for tool in session_tools)
                
                results["standard_connection"] = {
                    "status": "✅ PASS" if not has_session_tools else "❌ FAIL",
                    "tool_count": len(tools),
                    "has_session_tools": has_session_tools,
                    "issue": "Session tools present in standard mode" if has_session_tools else None
                }
            else:
                results["standard_connection"] = {
                    "status": "❌ FAIL",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        results["standard_connection"] = {
            "status": "❌ FAIL", 
            "error": str(e)
        }
    
    # Test session connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                session_endpoint,
                json=session_request,
                headers={"x-user-id": "test_user__session__dev_session__agent1", "x-client-name": "claude code"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("result", {}).get("tools", [])
                tool_names = [t["name"] for t in tools]
                
                session_tools = ["claim_files", "release_files", "sync_codebase", "broadcast_message", "get_agent_messages"]
                session_tool_count = len([tool for tool in session_tools if tool in tool_names])
                
                results["session_connection"] = {
                    "status": "✅ PASS" if session_tool_count == 5 else "❌ FAIL",
                    "tool_count": len(tools),
                    "session_tool_count": f"{session_tool_count}/5",
                    "missing_tools": [tool for tool in session_tools if tool not in tool_names] if session_tool_count < 5 else []
                }
            else:
                results["session_connection"] = {
                    "status": "❌ FAIL",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        results["session_connection"] = {
            "status": "❌ FAIL",
            "error": str(e)
        }
    
    return results

async def main():
    print("🔍 Validating MCP tool schemas...")
    results = await validate_tools_schema()
    
    print("\n📊 Validation Results:")
    for connection_type, result in results.items():
        print(f"\n{connection_type.replace('_', ' ').title()}:")
        print(f"  Status: {result['status']}")
        if 'tool_count' in result:
            print(f"  Tools: {result['tool_count']}")
        if 'session_tool_count' in result:
            print(f"  Session Tools: {result['session_tool_count']}")
        if result.get('error'):
            print(f"  Error: {result['error']}")
        if result.get('issue'):
            print(f"  Issue: {result['issue']}")
        if result.get('missing_tools'):
            print(f"  Missing: {', '.join(result['missing_tools'])}")

if __name__ == "__main__":
    asyncio.run(main())