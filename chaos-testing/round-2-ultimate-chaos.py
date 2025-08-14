#!/usr/bin/env python3
"""
ROUND 2: ULTIMATE CHAOS TESTING SUITE
====================================

This is the nuclear option. We're going to absolutely pummel the Jean Memory ecosystem
with every conceivable edge case, stress test, race condition, and chaos scenario.

NO MERCY. NO SURVIVORS. ONLY TESTING.
"""

import asyncio
import concurrent.futures
import json
import random
import time
import threading
import subprocess
import requests
import sys
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Import our SDK for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "sdk" / "python"))
from jeanmemory import JeanClient

API_KEY = "jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk"

@dataclass
class ChaosResult:
    """Track results from chaos testing"""
    test_name: str
    success: bool
    duration: float
    error: Optional[str] = None
    response_size: int = 0
    extra_data: Dict[str, Any] = None

class UltimateChaosEngine:
    """The most aggressive testing engine ever created"""
    
    def __init__(self):
        self.results: List[ChaosResult] = []
        self.client = JeanClient(API_KEY)
        self.concurrent_limit = 50  # Go HARD
        self.chaos_start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        """Aggressive logging"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        emoji = "🔥" if level == "CHAOS" else "💀" if level == "ERROR" else "⚡"
        print(f"[{timestamp}] {emoji} {message}")
        
    def record_result(self, result: ChaosResult):
        """Record a test result"""
        self.results.append(result)
        status = "✅" if result.success else "❌"
        size_info = f" ({result.response_size} chars)" if result.response_size else ""
        self.log(f"{status} {result.test_name} ({result.duration:.3f}s){size_info}", "CHAOS")
        
    def generate_chaos_messages(self, count: int = 1000) -> List[str]:
        """Generate absolute chaos messages"""
        messages = []
        
        # Real user scenarios
        real_messages = [
            "What's my favorite color?",
            "Tell me about my work projects",
            "What did I do last week?",
            "Remember that I like pizza",
            "What are my hobbies?",
            "Store this: I went to the gym today",
            "What's my name?",
            "Tell me about my preferences",
        ]
        
        # Edge cases
        edge_cases = [
            "",  # Empty
            " ",  # Just space
            "a" * 10000,  # Massive message
            "🔥" * 100,  # Emoji spam
            "\n\n\n\n",  # Newlines
            "NULL",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS
            "'; DROP TABLE users; --",  # SQL injection
            json.dumps({"nested": {"data": "test"}}),  # JSON
            "What's 2+2?" * 100,  # Repetitive
        ]
        
        # Random chaos
        for _ in range(count - len(real_messages) - len(edge_cases)):
            if random.random() < 0.3:
                # Random words
                words = ["test", "chaos", "memory", "jean", "api", "data", "user", "context"]
                msg = " ".join(random.choices(words, k=random.randint(1, 10)))
            elif random.random() < 0.6:
                # Random characters
                msg = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()", 
                                           k=random.randint(1, 1000)))
            else:
                # Unicode chaos
                msg = ''.join(chr(random.randint(32, 126)) for _ in range(random.randint(1, 100)))
            messages.append(msg)
            
        return real_messages + edge_cases + messages
        
    async def test_concurrent_requests(self, num_threads: int = 50, requests_per_thread: int = 10):
        """Flood the API with concurrent requests"""
        self.log(f"LAUNCHING {num_threads * requests_per_thread} CONCURRENT REQUESTS", "CHAOS")
        
        messages = self.generate_chaos_messages(num_threads * requests_per_thread)
        
        def make_request(message: str, thread_id: int, request_id: int) -> ChaosResult:
            test_name = f"concurrent_{thread_id}_{request_id}"
            start_time = time.time()
            
            try:
                response = self.client.get_context(
                    user_token="mock_jwt_token",
                    message=message,
                    is_new_conversation=random.choice([True, False])
                )
                
                duration = time.time() - start_time
                return ChaosResult(
                    test_name=test_name,
                    success=True,
                    duration=duration,
                    response_size=len(response.text),
                    extra_data={"thread": thread_id, "request": request_id}
                )
                
            except Exception as e:
                duration = time.time() - start_time
                return ChaosResult(
                    test_name=test_name,
                    success=False,
                    duration=duration,
                    error=str(e),
                    extra_data={"thread": thread_id, "request": request_id}
                )
        
        # Launch concurrent chaos
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            
            for thread_id in range(num_threads):
                for request_id in range(requests_per_thread):
                    message_idx = thread_id * requests_per_thread + request_id
                    message = messages[message_idx % len(messages)]
                    future = executor.submit(make_request, message, thread_id, request_id)
                    futures.append(future)
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                self.record_result(result)
    
    def test_sdk_parameter_edge_cases(self):
        """Test every possible parameter combination"""
        self.log("TESTING PARAMETER EDGE CASES", "CHAOS")
        
        edge_cases = [
            # Valid cases
            {"user_token": "valid_token", "message": "test", "is_new_conversation": True},
            {"user_token": "valid_token", "message": "test", "is_new_conversation": False},
            
            # Edge cases
            {"user_token": "", "message": "test"},  # Empty token
            {"user_token": "invalid", "message": ""},  # Empty message
            {"user_token": None, "message": "test"},  # None token
            {"user_token": "a" * 10000, "message": "test"},  # Huge token
        ]
        
        for i, params in enumerate(edge_cases):
            test_name = f"param_edge_case_{i}"
            start_time = time.time()
            
            try:
                response = self.client.get_context(**params)
                duration = time.time() - start_time
                self.record_result(ChaosResult(
                    test_name=test_name,
                    success=True,
                    duration=duration,
                    response_size=len(response.text)
                ))
            except Exception as e:
                duration = time.time() - start_time
                self.record_result(ChaosResult(
                    test_name=test_name,
                    success=False,
                    duration=duration,
                    error=str(e)
                ))
    
    def test_memory_persistence(self):
        """Test that memories actually persist across requests"""
        self.log("TESTING MEMORY PERSISTENCE", "CHAOS")
        
        # Store a unique memory
        unique_id = str(uuid.uuid4())
        secret_memory = f"CHAOS_TEST_SECRET_{unique_id}_REMEMBER_THIS"
        
        start_time = time.time()
        
        try:
            # Store the memory
            store_result = self.client.tools.add_memory("mock_jwt_token", secret_memory)
            
            # Wait a bit
            time.sleep(2)
            
            # Try to retrieve it
            response = self.client.get_context(
                user_token="mock_jwt_token",
                message=f"Do you remember anything about CHAOS_TEST_SECRET_{unique_id}?",
                is_new_conversation=False
            )
            
            duration = time.time() - start_time
            
            # Check if the memory was retrieved
            success = unique_id in response.text
            
            self.record_result(ChaosResult(
                test_name="memory_persistence",
                success=success,
                duration=duration,
                response_size=len(response.text),
                extra_data={"memory_found": success, "unique_id": unique_id}
            ))
            
        except Exception as e:
            duration = time.time() - start_time
            self.record_result(ChaosResult(
                test_name="memory_persistence",
                success=False,
                duration=duration,
                error=str(e)
            ))
    
    def test_rate_limiting(self):
        """Hammer the API to test rate limiting"""
        self.log("TESTING RATE LIMITING WITH RAPID FIRE", "CHAOS")
        
        for i in range(100):  # 100 rapid requests
            start_time = time.time()
            
            try:
                response = self.client.get_context(
                    user_token="mock_jwt_token",
                    message=f"Rate limit test #{i}",
                    is_new_conversation=False
                )
                
                duration = time.time() - start_time
                self.record_result(ChaosResult(
                    test_name=f"rate_limit_{i}",
                    success=True,
                    duration=duration,
                    response_size=len(response.text)
                ))
                
                # No delay - MAXIMUM CHAOS
                
            except Exception as e:
                duration = time.time() - start_time
                self.record_result(ChaosResult(
                    test_name=f"rate_limit_{i}",
                    success=False,
                    duration=duration,
                    error=str(e)
                ))
                
                # Continue even on errors
                continue
    
    def test_conversation_state_logic(self):
        """Test the is_new_conversation logic extensively"""
        self.log("TESTING CONVERSATION STATE LOGIC", "CHAOS")
        
        scenarios = [
            # Start new conversation
            (True, "Hello, I'm starting a new conversation"),
            
            # Continue conversation
            (False, "This should continue the previous conversation"),
            (False, "What did I just say?"),
            
            # New conversation again
            (True, "Now I'm starting fresh again"),
            (False, "Do you remember what I said before I started fresh?"),
            
            # Edge cases
            (None, "What happens with None?"),  # Should default to False
        ]
        
        for i, (is_new, message) in enumerate(scenarios):
            test_name = f"conversation_state_{i}"
            start_time = time.time()
            
            try:
                if is_new is None:
                    response = self.client.get_context(
                        user_token="mock_jwt_token",
                        message=message
                        # Don't pass is_new_conversation to test default
                    )
                else:
                    response = self.client.get_context(
                        user_token="mock_jwt_token",
                        message=message,
                        is_new_conversation=is_new
                    )
                
                duration = time.time() - start_time
                self.record_result(ChaosResult(
                    test_name=test_name,
                    success=True,
                    duration=duration,
                    response_size=len(response.text),
                    extra_data={"is_new_conversation": is_new}
                ))
                
                # Small delay to let the backend process
                time.sleep(0.5)
                
            except Exception as e:
                duration = time.time() - start_time
                self.record_result(ChaosResult(
                    test_name=test_name,
                    success=False,
                    duration=duration,
                    error=str(e),
                    extra_data={"is_new_conversation": is_new}
                ))
    
    def test_nodejs_sdk_interop(self):
        """Test Node.js SDK to ensure cross-SDK consistency"""
        self.log("TESTING NODE.JS SDK INTEROP", "CHAOS")
        
        node_test_script = '''
        const { JeanClient } = require('../sdk/node/dist/index.js');
        const client = new JeanClient({ apiKey: 'jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk' });
        
        async function runTest() {
            try {
                const response = await client.getContext({
                    user_token: 'mock_jwt_token',
                    message: 'Node.js SDK chaos test - what do you know about me?',
                    is_new_conversation: false
                });
                
                console.log(JSON.stringify({
                    success: true,
                    response_size: response.text.length,
                    has_content: response.text.length > 0
                }));
            } catch (error) {
                console.log(JSON.stringify({
                    success: false,
                    error: error.message
                }));
            }
        }
        
        runTest();
        '''
        
        start_time = time.time()
        
        try:
            # Write temporary test script
            script_path = Path(__file__).parent / "temp_node_test.js"
            with open(script_path, 'w') as f:
                f.write(node_test_script)
            
            # Run Node.js test
            result = subprocess.run(
                ['node', str(script_path)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(Path(__file__).parent.parent)
            )
            
            # Clean up
            script_path.unlink()
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                output = json.loads(result.stdout.strip())
                self.record_result(ChaosResult(
                    test_name="nodejs_sdk_interop",
                    success=output.get("success", False),
                    duration=duration,
                    response_size=output.get("response_size", 0),
                    extra_data=output
                ))
            else:
                self.record_result(ChaosResult(
                    test_name="nodejs_sdk_interop",
                    success=False,
                    duration=duration,
                    error=f"Node process failed: {result.stderr}"
                ))
                
        except Exception as e:
            duration = time.time() - start_time
            self.record_result(ChaosResult(
                test_name="nodejs_sdk_interop",
                success=False,
                duration=duration,
                error=str(e)
            ))
    
    def generate_chaos_report(self):
        """Generate comprehensive chaos testing report"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        
        total_duration = time.time() - self.chaos_start_time
        avg_response_time = sum(r.duration for r in self.results) / total_tests if total_tests > 0 else 0
        
        response_sizes = [r.response_size for r in self.results if r.response_size > 0]
        avg_response_size = sum(response_sizes) / len(response_sizes) if response_sizes else 0
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🔥 ULTIMATE CHAOS REPORT 🔥                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏱️  TOTAL CHAOS DURATION: {total_duration:.2f} seconds
🎯 TOTAL TESTS: {total_tests}
✅ SUCCESSFUL TESTS: {successful_tests} ({(successful_tests/total_tests*100):.1f}%)
❌ FAILED TESTS: {failed_tests} ({(failed_tests/total_tests*100):.1f}%)

📊 PERFORMANCE METRICS:
   • Average Response Time: {avg_response_time:.3f}s
   • Average Response Size: {avg_response_size:.0f} characters
   • Requests Per Second: {total_tests/total_duration:.1f} RPS

🔥 FAILURE ANALYSIS:
"""
        
        # Group failures by error type
        error_counts = {}
        for result in self.results:
            if not result.success and result.error:
                error_type = result.error.split(':')[0] if ':' in result.error else result.error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / failed_tests * 100) if failed_tests > 0 else 0
            report += f"   • {error_type}: {count} failures ({percentage:.1f}%)\n"
        
        report += f"\n💀 CHAOS CONCLUSION: "
        if successful_tests / total_tests > 0.9:
            report += "SYSTEM SURVIVED THE CHAOS! 🎉"
        elif successful_tests / total_tests > 0.7:
            report += "SYSTEM MOSTLY STABLE WITH MINOR ISSUES 😐"
        else:
            report += "SYSTEM NEEDS MAJOR IMPROVEMENTS! 🚨"
            
        print(report)
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(__file__).parent / f"chaos_report_round2_{timestamp}.json"
        
        detailed_report = {
            "metadata": {
                "timestamp": timestamp,
                "total_duration": total_duration,
                "total_tests": total_tests,
                "success_rate": successful_tests / total_tests,
                "avg_response_time": avg_response_time,
                "avg_response_size": avg_response_size
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "duration": r.duration,
                    "error": r.error,
                    "response_size": r.response_size,
                    "extra_data": r.extra_data
                }
                for r in self.results
            ]
        }
        
        with open(report_path, 'w') as f:
            json.dump(detailed_report, f, indent=2)
        
        self.log(f"Detailed report saved: {report_path}", "CHAOS")

async def main():
    """Launch the ultimate chaos testing assault"""
    print("""
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║  🔥🔥🔥 ROUND 2: ULTIMATE CHAOS TESTING BEGINS 🔥🔥🔥                    ║
    ║                                                                           ║
    ║  WARNING: This test will absolutely DESTROY your API with requests       ║
    ║  We're going to test EVERYTHING. No mercy. Pure chaos.                   ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
    """)
    
    engine = UltimateChaosEngine()
    
    try:
        # Test 1: Parameter edge cases
        engine.test_sdk_parameter_edge_cases()
        
        # Test 2: Memory persistence
        engine.test_memory_persistence()
        
        # Test 3: Conversation state logic
        engine.test_conversation_state_logic()
        
        # Test 4: Node.js SDK interop
        engine.test_nodejs_sdk_interop()
        
        # Test 5: Rate limiting (rapid fire)
        engine.test_rate_limiting()
        
        # Test 6: THE NUCLEAR OPTION - Massive concurrent requests
        await engine.test_concurrent_requests(num_threads=20, requests_per_thread=5)
        
    except KeyboardInterrupt:
        engine.log("CHAOS TESTING INTERRUPTED BY USER", "ERROR")
    except Exception as e:
        engine.log(f"CHAOS ENGINE FAILURE: {e}", "ERROR")
    finally:
        # Always generate report
        engine.generate_chaos_report()

if __name__ == "__main__":
    asyncio.run(main())