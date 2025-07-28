"""
Test performance of session coordination tools
"""
import asyncio
import httpx
import time
from typing import Dict, List

async def test_tool_performance(tool_name: str, args: Dict, target_ms: int = 200) -> Dict:
    """Test individual tool performance"""
    endpoint = "http://localhost:8765/mcp/claude%20code/messages/test_user/session/dev_session/agent1"
    
    request_body = {
        "jsonrpc": "2.0",
        "id": f"perf_test_{tool_name}",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args
        }
    }
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=request_body,
                headers={"x-user-id": "test_user__session__dev_session__agent1", "x-client-name": "claude code"},
                timeout=10.0
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return {
                "tool": tool_name,
                "response_time_ms": round(elapsed_ms, 2),
                "status": response.status_code,
                "target_ms": target_ms,
                "meets_target": elapsed_ms <= target_ms,
                "success": response.status_code in [200, 204]
            }
            
    except Exception as e:
        return {
            "tool": tool_name,
            "response_time_ms": (time.time() - start_time) * 1000,
            "status": "error",
            "target_ms": target_ms, 
            "meets_target": False,
            "success": False,
            "error": str(e)
        }

async def run_performance_tests() -> List[Dict]:
    """Run performance tests for all coordination tools"""
    
    tools_to_test = [
        ("claim_files", {"file_paths": ["test.py"], "operation": "write"}, 100),
        ("release_files", {"file_paths": ["test.py"], "changes_summary": "test"}, 100),
        ("sync_codebase", {"since_minutes": 30}, 200),
        ("broadcast_message", {"message": "test"}, 50),
        ("get_agent_messages", {"limit": 10}, 50)
    ]
    
    results = []
    
    print("⚡ Running performance tests...")
    
    for tool_name, args, target_ms in tools_to_test:
        print(f"  Testing {tool_name}...")
        result = await test_tool_performance(tool_name, args, target_ms)
        results.append(result)
        
        status = "✅" if result["meets_target"] and result["success"] else "❌"
        print(f"    {status} {result['response_time_ms']}ms (target: {target_ms}ms)")
    
    return results

async def main():
    results = await run_performance_tests()
    
    print("\n📊 Performance Summary:")
    total_tools = len(results)
    passing_tools = len([r for r in results if r["meets_target"] and r["success"]])
    
    print(f"Tools passing performance targets: {passing_tools}/{total_tools}")
    
    if passing_tools < total_tools:
        print("\n⚠️  Performance Issues:")
        for result in results:
            if not (result["meets_target"] and result["success"]):
                issue = f"slow ({result['response_time_ms']}ms > {result['target_ms']}ms)" if not result["meets_target"] else "failed"
                print(f"  - {result['tool']}: {issue}")
    
    print(f"\nOverall Status: {'✅ PASS' if passing_tools == total_tools else '❌ FAIL'}")

if __name__ == "__main__":
    asyncio.run(main())