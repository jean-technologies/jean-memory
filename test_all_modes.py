#!/usr/bin/env python3
"""
Comprehensive test suite for all Jean Memory modes
Tests both SDK and direct API calls to verify functionality
"""

import os
import time
import json
import asyncio
import statistics
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
from jeanmemory import JeanMemoryClient
import aiohttp

# Load environment variables
load_dotenv()

class JeanMemoryTester:
    def __init__(self):
        self.api_key = os.getenv("JEAN_MEMORY_API_KEY")
        if not self.api_key:
            raise ValueError("JEAN_MEMORY_API_KEY not found in environment")
        
        self.client = JeanMemoryClient(api_key=self.api_key)
        self.results = []
        
    async def test_direct_api(self, query: str, mode: str) -> Dict[str, Any]:
        """Test direct API call to verify server-side functionality"""
        url = "https://openmemory.ai/api/v1/tools/jean_memory"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "user_message": query,
            "is_new_conversation": False,
            "needs_context": True,
            "speed": mode,
            "format": "enhanced"
        }
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    latency = time.time() - start_time
                    result = await response.json()
                    
                    return {
                        "mode": mode,
                        "method": "direct_api",
                        "status": response.status,
                        "latency": latency,
                        "response_size": len(json.dumps(result)),
                        "has_content": bool(result.get("result") or result.get("content")),
                        "error": result.get("error"),
                        "preview": str(result)[:200] + "..." if result else None
                    }
            except Exception as e:
                return {
                    "mode": mode,
                    "method": "direct_api",
                    "status": "error",
                    "latency": time.time() - start_time,
                    "error": str(e)
                }
    
    def test_sdk(self, query: str, mode: str) -> Dict[str, Any]:
        """Test through SDK to verify client-side functionality"""
        start_time = time.time()
        
        try:
            result = self.client.get_context(query=query, speed=mode)
            latency = time.time() - start_time
            
            # Check if result is empty
            is_empty = False
            content = ""
            
            if isinstance(result, dict):
                content = result.get("result") or result.get("content") or ""
            elif isinstance(result, str):
                content = result
            
            is_empty = not content or content.strip() == ""
            
            return {
                "mode": mode,
                "method": "sdk",
                "status": "success",
                "latency": latency,
                "response_size": len(str(result)),
                "has_content": not is_empty,
                "is_empty": is_empty,
                "preview": str(result)[:200] + "..." if result else None
            }
        except Exception as e:
            return {
                "mode": mode,
                "method": "sdk",
                "status": "error",
                "latency": time.time() - start_time,
                "error": str(e)
            }
    
    async def run_comprehensive_test(self):
        """Run comprehensive tests on all modes"""
        
        test_queries = [
            "What have I been working on recently?",
            "What are my goals?",
            "Tell me about myself"
        ]
        
        modes = ["fast", "balanced", "autonomous", "comprehensive"]
        
        print("=" * 80)
        print(f"Jean Memory Comprehensive Mode Testing")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"API Key: {self.api_key[:20]}...")
        print("=" * 80)
        
        all_results = []
        
        for query in test_queries:
            print(f"\n📝 Testing Query: '{query}'")
            print("-" * 60)
            
            for mode in modes:
                print(f"\n🔄 Testing {mode.upper()} mode...")
                
                # Test SDK
                sdk_result = self.test_sdk(query, mode)
                self._print_result(sdk_result)
                all_results.append(sdk_result)
                
                # Test Direct API
                api_result = await self.test_direct_api(query, mode)
                self._print_result(api_result)
                all_results.append(api_result)
                
                # Small delay between tests
                await asyncio.sleep(0.5)
        
        # Print summary
        self._print_summary(all_results)
        
        # Save results to file
        self._save_results(all_results)
        
        return all_results
    
    def _print_result(self, result: Dict[str, Any]):
        """Pretty print a single result"""
        status_emoji = "✅" if result["status"] == "success" or result["status"] == 200 else "❌"
        content_emoji = "📄" if result.get("has_content") else "⚠️"
        
        print(f"  {status_emoji} [{result['method']}] Status: {result['status']}")
        print(f"  ⏱️  Latency: {result['latency']:.2f}s")
        print(f"  {content_emoji} Has Content: {result.get('has_content', 'Unknown')}")
        
        if result.get("is_empty"):
            print(f"  ⚠️  WARNING: Empty response detected!")
        
        if result.get("error"):
            print(f"  ❌ Error: {result['error']}")
        
        if result.get("preview"):
            print(f"  📝 Preview: {result['preview']}")
    
    def _print_summary(self, results: List[Dict[str, Any]]):
        """Print summary statistics"""
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        
        # Group by mode
        by_mode = {}
        for r in results:
            mode = r["mode"]
            if mode not in by_mode:
                by_mode[mode] = []
            by_mode[mode].append(r)
        
        for mode, mode_results in by_mode.items():
            print(f"\n📊 {mode.upper()} Mode:")
            
            # Success rate
            successes = [r for r in mode_results if r["status"] in ["success", 200]]
            success_rate = len(successes) / len(mode_results) * 100 if mode_results else 0
            print(f"  Success Rate: {success_rate:.1f}% ({len(successes)}/{len(mode_results)})")
            
            # Empty response rate
            empties = [r for r in mode_results if r.get("is_empty") or not r.get("has_content")]
            empty_rate = len(empties) / len(mode_results) * 100 if mode_results else 0
            print(f"  Empty Response Rate: {empty_rate:.1f}% ({len(empties)}/{len(mode_results)})")
            
            # Latency stats
            latencies = [r["latency"] for r in mode_results if "latency" in r]
            if latencies:
                print(f"  Latency - Mean: {statistics.mean(latencies):.2f}s")
                print(f"  Latency - Median: {statistics.median(latencies):.2f}s")
                print(f"  Latency - Min: {min(latencies):.2f}s")
                print(f"  Latency - Max: {max(latencies):.2f}s")
            
            # Response sizes
            sizes = [r["response_size"] for r in mode_results if "response_size" in r]
            if sizes:
                print(f"  Avg Response Size: {statistics.mean(sizes):.0f} bytes")
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """Save results to JSON file"""
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "api_key_prefix": self.api_key[:20] if self.api_key else None,
                "results": results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")

async def test_specific_mode(mode: str, query: str = "What have I been working on?"):
    """Quick test of a specific mode"""
    tester = JeanMemoryTester()
    
    print(f"\n🧪 Quick Test: {mode} mode")
    print(f"Query: {query}")
    print("-" * 40)
    
    # Test SDK
    sdk_result = tester.test_sdk(query, mode)
    tester._print_result(sdk_result)
    
    # Test API
    api_result = await tester.test_direct_api(query, mode)
    tester._print_result(api_result)
    
    return sdk_result, api_result

async def main():
    """Main test runner"""
    import sys
    
    if len(sys.argv) > 1:
        # Test specific mode
        mode = sys.argv[1]
        query = sys.argv[2] if len(sys.argv) > 2 else "What have I been working on?"
        await test_specific_mode(mode, query)
    else:
        # Run comprehensive test
        tester = JeanMemoryTester()
        await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())