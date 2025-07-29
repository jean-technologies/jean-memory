#!/usr/bin/env python3
"""
Production Jean Memory MCP Protocol Test Script

Tests the jean_memory tool directly against the production URL using the MCP protocol.
Tests both short queries (needs_context=false) and deep context queries (needs_context=true).

Production URL: https://jean-memory-api-virginia.onrender.com/mcp/v2/cursor/66d3d5d1-fc48-44a7-bbc0-1efa2e164fad
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JeanMemoryMCPTester:
    def __init__(self, base_url: str, user_id: str, client_name: str = "cursor"):
        """
        Initialize the MCP tester
        
        Args:
            base_url: The production API base URL
            user_id: The user ID for the test session
            client_name: The client name (default: cursor)
        """
        self.base_url = base_url
        self.user_id = user_id
        self.client_name = client_name
        self.endpoint_url = f"{base_url}/mcp/v2/{client_name}/{user_id}"
        self.session = requests.Session()
        
        # Set headers for MCP protocol
        self.session.headers.update({
            'Content-Type': 'application/json',
            'x-user-id': user_id,
            'x-client-name': client_name
        })
        
        logger.info(f"🔧 Initialized MCP tester for endpoint: {self.endpoint_url}")
    
    def create_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a JSON-RPC 2.0 request following MCP protocol
        
        Args:
            method: The MCP method name
            params: Optional parameters for the method
            
        Returns:
            JSON-RPC 2.0 formatted request
        """
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }
        
        if params:
            request["params"] = params
            
        return request
    
    def send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send an MCP request to the production endpoint
        
        Args:
            request: The JSON-RPC 2.0 request
            
        Returns:
            The response data and timing information
        """
        start_time = time.time()
        
        try:
            logger.info(f"📤 Sending MCP request: {request['method']}")
            logger.debug(f"📤 Request payload: {json.dumps(request, indent=2)}")
            
            response = self.session.post(self.endpoint_url, json=request, timeout=60)
            response_time = time.time() - start_time
            
            logger.info(f"📥 Response status: {response.status_code}, Time: {response_time:.3f}s")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"📥 Response payload: {json.dumps(response_data, indent=2)}")
                
                return {
                    "success": True,
                    "response": response_data,
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            else:
                logger.error(f"❌ HTTP Error {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time": response_time,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            logger.error(f"⏰ Request timeout after {response_time:.3f}s")
            return {
                "success": False,
                "error": "Request timeout",
                "response_time": response_time,
                "status_code": None
            }
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"❌ Request failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_time": response_time,
                "status_code": None
            }
    
    def test_initialize(self) -> Dict[str, Any]:
        """Test MCP initialize handshake"""
        logger.info("🔄 Testing MCP initialize...")
        
        request = self.create_mcp_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "jean-memory-test",
                "version": "1.0.0"
            }
        })
        
        return self.send_mcp_request(request)
    
    def test_tools_list(self) -> Dict[str, Any]:
        """Test MCP tools/list to see available tools"""
        logger.info("🔧 Testing tools/list...")
        
        request = self.create_mcp_request("tools/list")
        return self.send_mcp_request(request)
    
    def test_jean_memory_short_query(self) -> Dict[str, Any]:
        """Test jean_memory tool with a short query that doesn't need context"""
        logger.info("📝 Testing jean_memory - Short query (needs_context=false)...")
        
        request = self.create_mcp_request("tools/call", {
            "name": "jean_memory",
            "arguments": {
                "user_message": "What's 2+2?",
                "is_new_conversation": False,
                "needs_context": False
            }
        })
        
        return self.send_mcp_request(request)
    
    def test_jean_memory_new_conversation(self) -> Dict[str, Any]:
        """Test jean_memory tool for new conversation with context"""
        logger.info("🆕 Testing jean_memory - New conversation (is_new_conversation=true, needs_context=true)...")
        
        request = self.create_mcp_request("tools/call", {
            "name": "jean_memory",
            "arguments": {
                "user_message": "Help me plan my career transition",
                "is_new_conversation": True,
                "needs_context": True
            }
        })
        
        return self.send_mcp_request(request)
    
    def test_jean_memory_deep_context(self) -> Dict[str, Any]:
        """Test jean_memory tool with deep context query"""
        logger.info("🧠 Testing jean_memory - Deep context query (needs_context=true)...")
        
        request = self.create_mcp_request("tools/call", {
            "name": "jean_memory",
            "arguments": {
                "user_message": "Continue working on the Python API we discussed",
                "is_new_conversation": False,
                "needs_context": True
            }
        })
        
        return self.send_mcp_request(request)
    
    def analyze_response(self, result: Dict[str, Any], test_name: str) -> None:
        """
        Analyze and document the MCP response
        
        Args:
            result: The response result from send_mcp_request
            test_name: Name of the test for logging
        """
        print(f"\n{'='*60}")
        print(f"📊 Analysis: {test_name}")
        print('='*60)
        
        if result["success"]:
            print(f"✅ Status: SUCCESS")
            print(f"⏱️  Response Time: {result['response_time']:.3f}s")
            print(f"🌐 HTTP Status: {result['status_code']}")
            
            response = result["response"]
            
            # Analyze JSON-RPC structure
            if "jsonrpc" in response:
                print(f"📋 JSON-RPC Version: {response.get('jsonrpc')}")
                print(f"🆔 Request ID: {response.get('id')}")
                
                if "result" in response:
                    print(f"✅ Result Type: {type(response['result'])}")
                    
                    # For tools/list, show available tools
                    if isinstance(response['result'], dict) and 'tools' in response['result']:
                        tools = response['result']['tools']
                        print(f"🔧 Available Tools: {len(tools)}")
                        for tool in tools:
                            print(f"   - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:50]}...")
                    
                    # For tool responses, analyze the content
                    elif isinstance(response['result'], dict) and 'content' in response['result']:
                        content = response['result']['content']
                        if isinstance(content, list) and len(content) > 0:
                            first_content = content[0]
                            if 'text' in first_content:
                                text_length = len(first_content['text'])
                                print(f"📄 Response Text Length: {text_length} characters")
                                print(f"📝 Response Preview: {first_content['text'][:200]}...")
                    
                    # For initialize response
                    elif isinstance(response['result'], dict) and 'protocolVersion' in response['result']:
                        print(f"🔗 Protocol Version: {response['result']['protocolVersion']}")
                        print(f"⚙️  Server Capabilities: {response['result'].get('capabilities', {})}")
                        server_info = response['result'].get('serverInfo', {})
                        print(f"🖥️  Server: {server_info.get('name')} v{server_info.get('version')}")
                
                if "error" in response:
                    error = response["error"]
                    print(f"❌ Error Code: {error.get('code')}")
                    print(f"❌ Error Message: {error.get('message')}")
        else:
            print(f"❌ Status: FAILED")
            print(f"⏱️  Response Time: {result['response_time']:.3f}s")
            print(f"🌐 HTTP Status: {result.get('status_code', 'N/A')}")
            print(f"❌ Error: {result['error']}")
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results"""
        logger.info("🚀 Starting comprehensive jean_memory MCP production test...")
        
        results = {}
        total_start_time = time.time()
        
        # Test sequence following MCP protocol flow
        tests = [
            ("initialize", self.test_initialize),
            ("tools_list", self.test_tools_list),
            ("short_query", self.test_jean_memory_short_query),
            ("new_conversation", self.test_jean_memory_new_conversation),
            ("deep_context", self.test_jean_memory_deep_context),
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 Running Test: {test_name.upper()}")
            print('='*60)
            
            result = test_func()
            results[test_name] = result
            
            self.analyze_response(result, test_name)
            
            # Short delay between tests
            if test_name != tests[-1][0]:  # Don't wait after last test
                time.sleep(1)
        
        total_time = time.time() - total_start_time
        
        # Final summary
        print(f"\n{'='*60}")
        print("📈 COMPREHENSIVE TEST SUMMARY")
        print('='*60)
        
        successful_tests = sum(1 for result in results.values() if result["success"])
        total_tests = len(results)
        
        print(f"✅ Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"⏱️  Total Test Time: {total_time:.3f}s")
        
        for test_name, result in results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            time_info = f"{result['response_time']:.3f}s"
            print(f"{status} {test_name.ljust(15)} ({time_info})")
        
        # Document the MCP flow
        print(f"\n{'='*60}")
        print("📋 MCP PROTOCOL FLOW DOCUMENTATION")
        print('='*60)
        print("1. INITIALIZE: Establishes protocol version and capabilities")
        print("2. TOOLS/LIST: Retrieves available tools and their schemas")
        print("3. TOOLS/CALL: Invokes jean_memory tool with different parameter combinations")
        print("   - Short Query: needs_context=false for generic knowledge")
        print("   - New Conversation: is_new_conversation=true, needs_context=true")
        print("   - Deep Context: needs_context=true for contextual queries")
        print("\nMessage Flow:")
        print("- Client sends JSON-RPC 2.0 request to /mcp/v2/{client}/{user_id}")
        print("- Server processes request through MCP orchestration layer")
        print("- jean_memory tool retrieves context, processes query, saves new information")
        print("- Server returns JSON-RPC 2.0 response with structured content")
        
        return results

def main():
    """Main test execution"""
    # Production configuration
    BASE_URL = "https://jean-memory-api-virginia.onrender.com"
    USER_ID = "66d3d5d1-fc48-44a7-bbc0-1efa2e164fad"
    CLIENT_NAME = "cursor"
    
    print("=" * 80)
    print("🧪 JEAN MEMORY MCP PRODUCTION TEST SUITE")
    print("=" * 80)
    print(f"🌐 Production URL: {BASE_URL}")
    print(f"👤 User ID: {USER_ID}")
    print(f"💻 Client: {CLIENT_NAME}")
    print(f"🎯 Endpoint: {BASE_URL}/mcp/v2/{CLIENT_NAME}/{USER_ID}")
    
    # Initialize tester
    tester = JeanMemoryMCPTester(BASE_URL, USER_ID, CLIENT_NAME)
    
    # Run comprehensive test
    results = tester.run_comprehensive_test()
    
    # Final analysis
    print(f"\n{'='*80}")
    print("🎯 PRODUCTION READINESS ASSESSMENT")
    print('='*80)
    
    all_successful = all(result["success"] for result in results.values())
    
    if all_successful:
        print("🚀 PRODUCTION READY!")
        print("✅ All MCP protocol tests passed")
        print("✅ jean_memory tool is functioning correctly")
        print("✅ Both short and deep context queries work")
        print("✅ Protocol flow is properly implemented")
    else:
        print("⚠️  ISSUES DETECTED!")
        failed_tests = [name for name, result in results.items() if not result["success"]]
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        print("🔧 Review the errors above and fix before production use")
    
    return all_successful

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)