#!/usr/bin/env python3
import requests
import concurrent.futures
import time
import json
import random
from datetime import datetime

API_BASE = "https://jean-memory-api-virginia.onrender.com"
API_KEY = "jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk"

def make_mcp_request(user_id, tool_name, arguments, request_id):
    """Direct MCP request to backend"""
    start_time = time.time()
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/mcp/python-sdk/messages/{user_id}",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY,
                "X-User-Id": user_id
            },
            json=mcp_request,
            timeout=30
        )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data:
                result_text = data.get('result', {}).get('content', [{}])[0].get('text', '')
                return {
                    'success': True,
                    'duration': duration,
                    'status_code': response.status_code,
                    'response_size': len(result_text),
                    'request_id': request_id
                }
        
        return {
            'success': False,
            'duration': duration,
            'status_code': response.status_code,
            'error': response.text[:200],
            'request_id': request_id
        }
        
    except Exception as e:
        return {
            'success': False,
            'duration': time.time() - start_time,
            'status_code': 0,
            'error': str(e),
            'request_id': request_id
        }

def run_backend_hammer():
    print("🔨 Backend API Hammer v2.0 Starting...")
    
    results = []
    start_time = time.time()
    
    # Chaos messages
    messages = [
        "Backend hammer test message",
        "Direct MCP call chaos test",
        "API stress test in progress", 
        "Remember this hammer test",
        "What do you know about me?",
        "Store this memory: Backend chaos active",
        "Test message " + str(random.randint(1000, 9999)),
        "Chaos test: " + "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=20))
    ]
    
    # Generate test arguments
    test_cases = []
    for i in range(200):  # 200 total requests
        message = messages[i % len(messages)]
        test_cases.append({
            'user_id': 'chaos_test_user',
            'tool_name': 'jean_memory',
            'arguments': {
                'user_message': message,
                'is_new_conversation': random.choice([True, False]),
                'needs_context': True
            },
            'request_id': i + 1
        })
    
    print(f"🚀 Launching {len(test_cases)} concurrent requests...")
    
    # Execute with high concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = [
            executor.submit(
                make_mcp_request,
                case['user_id'],
                case['tool_name'],
                case['arguments'],
                case['request_id']
            )
            for case in test_cases
        ]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            
            status = "✅" if result['success'] else "❌"
            print(f"{status} Request {result['request_id']}: {result['duration']:.3f}s")
    
    # Generate report
    total_duration = time.time() - start_time
    success_count = sum(1 for r in results if r['success'])
    fail_count = len(results) - success_count
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    successful_responses = [r for r in results if r['success'] and 'response_size' in r]
    avg_response_size = (sum(r['response_size'] for r in successful_responses) / 
                        len(successful_responses)) if successful_responses else 0
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                        🔨 BACKEND HAMMER REPORT 🔨                        ║
╚════════════════════════════════════════════════════════════════════════════╝

⏱️  Total Duration: {total_duration:.2f}s
🎯 Total Requests: {len(results)}
✅ Successful: {success_count} ({success_count/len(results)*100:.1f}%)
❌ Failed: {fail_count} ({fail_count/len(results)*100:.1f}%)
📊 Avg Response Time: {avg_duration:.3f}s
📏 Avg Response Size: {avg_response_size:.0f} characters
🚀 Requests Per Second: {len(results)/total_duration:.1f} RPS

{('🎉 BACKEND SURVIVED THE HAMMER!' if success_count > len(results) * 0.7 else '⚠️  BACKEND NEEDS ATTENTION')}
    """)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'./logs/backend_hammer_report_{timestamp}.json', 'w') as f:
        json.dump({
            'metadata': {
                'total_duration': total_duration,
                'total_requests': len(results),
                'success_rate': success_count / len(results),
                'avg_duration': avg_duration,
                'avg_response_size': avg_response_size
            },
            'results': results
        }, f, indent=2)

if __name__ == "__main__":
    run_backend_hammer()
