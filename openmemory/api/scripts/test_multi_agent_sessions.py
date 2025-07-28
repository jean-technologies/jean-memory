"""
Test multi-agent session coordination locally
"""
import asyncio
import httpx
import json
from typing import Dict, List

class LocalMCPTester:
    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.test_user_id = "test_user"
        self.session_name = "dev_session"
        
    async def test_session_endpoints(self) -> Dict:
        """Test that session endpoints are accessible"""
        results = {}
        
        agents = ["agent1", "agent2"]
        for agent_id in agents:
            endpoint = f"{self.base_url}/mcp/claude%20code/sse/{self.test_user_id}/session/{self.session_name}/{agent_id}"
            
            try:
                async with httpx.AsyncClient() as client:
                    # Test SSE endpoint accessibility
                    response = await client.get(endpoint, timeout=5.0)
                    results[agent_id] = {
                        "sse_endpoint": "accessible" if response.status_code == 200 else f"error_{response.status_code}",
                        "endpoint_url": endpoint
                    }
            except Exception as e:
                results[agent_id] = {
                    "sse_endpoint": f"error: {str(e)}",
                    "endpoint_url": endpoint
                }
        
        return results
    
    async def test_session_tools(self) -> Dict:
        """Test session coordination tools"""
        tools_to_test = [
            "claim_files",
            "release_files", 
            "sync_codebase",
            "broadcast_message",
            "get_agent_messages"
        ]
        
        results = {}
        
        for tool in tools_to_test:
            message_endpoint = f"{self.base_url}/mcp/claude%20code/messages/{self.test_user_id}/session/{self.session_name}/agent1"
            
            # Create test tool call
            tool_call = {
                "jsonrpc": "2.0",
                "id": f"test_{tool}",
                "method": "tools/call",
                "params": {
                    "name": tool,
                    "arguments": self._get_test_args(tool)
                }
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        message_endpoint,
                        json=tool_call,
                        headers={"x-user-id": f"{self.test_user_id}__session__{self.session_name}__agent1", "x-client-name": "claude code"},
                        timeout=10.0
                    )
                    
                    results[tool] = {
                        "status": response.status_code,
                        "accessible": response.status_code in [200, 204],
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                    
            except Exception as e:
                results[tool] = {
                    "status": "error",
                    "accessible": False,
                    "error": str(e)
                }
        
        return results
    
    def _get_test_args(self, tool: str) -> Dict:
        """Get test arguments for each tool"""
        args_map = {
            "claim_files": {
                "file_paths": ["test_file.py"],
                "operation": "write",
                "duration_minutes": 5
            },
            "release_files": {
                "file_paths": ["test_file.py"],
                "changes_summary": "Test changes"
            },
            "sync_codebase": {
                "since_minutes": 30
            },
            "broadcast_message": {
                "message": "Test coordination message",
                "message_type": "info"
            },
            "get_agent_messages": {
                "limit": 5
            }
        }
        return args_map.get(tool, {})
    
    async def run_full_test(self) -> Dict:
        """Run complete test suite"""
        print("🧪 Testing multi-agent session setup...")
        
        results = {
            "endpoints": await self.test_session_endpoints(),
            "tools": await self.test_session_tools(),
            "summary": {}
        }
        
        # Generate summary
        endpoint_count = len([r for r in results["endpoints"].values() if r.get("sse_endpoint") == "accessible"])
        tool_count = len([r for r in results["tools"].values() if r.get("accessible")])
        
        results["summary"] = {
            "accessible_endpoints": f"{endpoint_count}/2",
            "working_tools": f"{tool_count}/5",
            "overall_status": "✅ PASS" if endpoint_count == 2 and tool_count == 5 else "❌ FAIL"
        }
        
        return results

async def main():
    tester = LocalMCPTester()
    results = await tester.run_full_test()
    
    print("\n📊 Test Results:")
    print(f"Endpoints: {results['summary']['accessible_endpoints']}")
    print(f"Tools: {results['summary']['working_tools']}")
    print(f"Status: {results['summary']['overall_status']}")
    
    if results['summary']['overall_status'] == "❌ FAIL":
        print("\n🔍 Issues Found:")
        for agent, result in results["endpoints"].items():
            if result.get("sse_endpoint") != "accessible":
                print(f"  - {agent} endpoint: {result['sse_endpoint']}")
        
        for tool, result in results["tools"].items():
            if not result.get("accessible"):
                print(f"  - {tool} tool: {result.get('error', 'Not accessible')}")

if __name__ == "__main__":
    asyncio.run(main())