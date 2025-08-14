#!/bin/bash

# ULTIMATE CHAOS TESTING ORCHESTRATOR
# This script will launch EVERY possible test scenario simultaneously
# NO MERCY. MAXIMUM CHAOS.

set -e

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║  🔥🔥🔥 CHAOS ORCHESTRATOR: ROUND 2 ULTIMATE TESTING 🔥🔥🔥              ║"
echo "║                                                                           ║"
echo "║  WARNING: This will launch multiple chaos testing processes              ║"
echo "║  simultaneously across all SDKs and platforms.                          ║"
echo "║                                                                           ║"
echo "║  - Python SDK chaos testing                                              ║"
echo "║  - Node.js SDK stress testing                                            ║"
echo "║  - React frontend chaos app                                              ║"
echo "║  - Backend API hammering                                                 ║"
echo "║  - Memory persistence verification                                       ║"
echo "║  - Cross-SDK consistency testing                                         ║"
echo "║                                                                           ║"
echo "║  CTRL+C to abort before it's too late...                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Countdown
for i in {5..1}; do
    echo "⏰ Starting chaos in $i seconds..."
    sleep 1
done

echo "🚀 LAUNCHING CHAOS NOW!"
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Create logs directory
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "📁 Logs will be saved to: $LOGS_DIR"
echo ""

# Function to run command in background and log
run_chaos_test() {
    local name="$1"
    local command="$2"
    local log_file="$LOGS_DIR/chaos_${name}_${TIMESTAMP}.log"
    
    echo "🔥 Launching $name chaos test..."
    echo "   Command: $command"
    echo "   Log: $log_file"
    
    # Run in background and save PID
    bash -c "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo "   PID: $pid"
    echo "$pid" > "$LOGS_DIR/${name}_pid.txt"
    echo ""
}

# 1. Python SDK Ultimate Chaos
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🐍 LAUNCHING PYTHON SDK CHAOS"
echo "═══════════════════════════════════════════════════════════════════════════"
run_chaos_test "python_ultimate" "cd '$SCRIPT_DIR' && python3 round-2-ultimate-chaos.py"

# 2. Node.js SDK Stress Test
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🟢 LAUNCHING NODE.JS SDK STRESS TEST"
echo "═══════════════════════════════════════════════════════════════════════════"
NODE_STRESS_SCRIPT="$SCRIPT_DIR/node-stress-test.js"
cat > "$NODE_STRESS_SCRIPT" << 'EOF'
const { JeanClient } = require('../sdk/node/dist/index.js');

async function runNodeStressTest() {
    console.log('🟢 Node.js Stress Test Starting...');
    
    const client = new JeanClient({ 
        apiKey: 'jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk' 
    });
    
    const results = [];
    const startTime = Date.now();
    
    // Generate chaos messages
    const messages = [
        'What do you know about me?',
        'Remember this chaos test',
        'Node.js SDK testing in progress',
        'Store this memory: Node chaos test active',
        'Retrieve my previous messages',
        'Test conversation continuity',
        'Edge case: empty response check',
        'Memory persistence verification'
    ];
    
    // Add random messages
    for (let i = 0; i < 100; i++) {
        messages.push(`Random chaos message ${i}: ${Math.random().toString(36)}`);
    }
    
    // Run tests concurrently
    const concurrency = 10;
    const batches = [];
    
    for (let batch = 0; batch < 10; batch++) {
        const batchPromises = [];
        
        for (let i = 0; i < concurrency; i++) {
            const messageIndex = (batch * concurrency + i) % messages.length;
            const message = messages[messageIndex];
            
            const testPromise = (async () => {
                const testStart = Date.now();
                try {
                    const response = await client.getContext({
                        user_token: 'mock_jwt_token',
                        message: message,
                        is_new_conversation: Math.random() > 0.7
                    });
                    
                    return {
                        success: true,
                        duration: Date.now() - testStart,
                        responseSize: response.text.length,
                        batch: batch,
                        index: i
                    };
                } catch (error) {
                    return {
                        success: false,
                        duration: Date.now() - testStart,
                        error: error.message,
                        batch: batch,
                        index: i
                    };
                }
            })();
            
            batchPromises.push(testPromise);
        }
        
        console.log(`🔥 Launching batch ${batch + 1}/10 with ${concurrency} concurrent requests...`);
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);
        
        // Brief pause between batches
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Generate report
    const totalDuration = Date.now() - startTime;
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;
    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length;
    const avgResponseSize = results.filter(r => r.responseSize)
        .reduce((sum, r) => sum + r.responseSize, 0) / 
        Math.max(1, results.filter(r => r.responseSize).length);
    
    console.log(`
╔════════════════════════════════════════════════════════════════════════════╗
║                        🟢 NODE.JS CHAOS REPORT 🟢                         ║
╚════════════════════════════════════════════════════════════════════════════╝

⏱️  Total Duration: ${totalDuration}ms
🎯 Total Tests: ${results.length}
✅ Successful: ${successCount} (${(successCount/results.length*100).toFixed(1)}%)
❌ Failed: ${failCount} (${(failCount/results.length*100).toFixed(1)}%)
📊 Avg Response Time: ${avgDuration.toFixed(0)}ms
📏 Avg Response Size: ${avgResponseSize.toFixed(0)} characters
🚀 Requests Per Second: ${(results.length / (totalDuration/1000)).toFixed(1)} RPS

${successCount > results.length * 0.8 ? '🎉 NODE.JS SDK SURVIVED THE CHAOS!' : '⚠️  NODE.JS SDK NEEDS ATTENTION'}
    `);
    
    // Save detailed results
    const fs = require('fs');
    const reportPath = `./logs/node_stress_report_${Date.now()}.json`;
    fs.writeFileSync(reportPath, JSON.stringify({
        metadata: {
            totalDuration,
            totalTests: results.length,
            successRate: successCount / results.length,
            avgDuration,
            avgResponseSize
        },
        results
    }, null, 2));
    
    console.log(`📄 Detailed report saved: ${reportPath}`);
}

runNodeStressTest().catch(console.error);
EOF

run_chaos_test "node_stress" "cd '$ROOT_DIR' && node '$NODE_STRESS_SCRIPT'"

# 3. Backend API Hammer (Direct HTTP)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🔨 LAUNCHING BACKEND API HAMMER"
echo "═══════════════════════════════════════════════════════════════════════════"
BACKEND_HAMMER_SCRIPT="$SCRIPT_DIR/backend-hammer-v2.py"
cat > "$BACKEND_HAMMER_SCRIPT" << 'EOF'
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
EOF

run_chaos_test "backend_hammer" "cd '$SCRIPT_DIR' && python3 backend-hammer-v2.py"

# 4. React Chaos App (if we can build it)
echo "═══════════════════════════════════════════════════════════════════════════"
echo "⚛️  PREPARING REACT CHAOS APP"
echo "═══════════════════════════════════════════════════════════════════════════"

REACT_APP_DIR="$SCRIPT_DIR/react-chaos-app"
if [ -d "$REACT_APP_DIR" ]; then
    echo "📦 Installing React app dependencies..."
    cd "$REACT_APP_DIR"
    if npm install --silent > "$LOGS_DIR/react_install_${TIMESTAMP}.log" 2>&1; then
        echo "✅ Dependencies installed"
        echo "🚀 Launching React chaos app on port 3001..."
        run_chaos_test "react_app" "cd '$REACT_APP_DIR' && npm run dev"
        echo "🌐 React app should be available at: http://localhost:3001"
        echo "   Open this URL to run frontend chaos tests!"
    else
        echo "❌ Failed to install React dependencies - check logs"
    fi
    cd "$SCRIPT_DIR"
else
    echo "❌ React app directory not found"
fi

# 5. Memory Persistence Cross-Validation
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🧠 LAUNCHING MEMORY PERSISTENCE CROSS-VALIDATION"
echo "═══════════════════════════════════════════════════════════════════════════"
MEMORY_TEST_SCRIPT="$SCRIPT_DIR/memory-cross-validation.py"
cat > "$MEMORY_TEST_SCRIPT" << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sdk', 'python'))

from jeanmemory import JeanClient
import time
import json
import uuid
from datetime import datetime

def run_memory_cross_validation():
    print("🧠 Memory Persistence Cross-Validation Starting...")
    
    client = JeanClient('jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk')
    results = []
    
    # Test cases: Store memories and verify they persist
    test_memories = []
    for i in range(10):
        unique_id = str(uuid.uuid4())[:8]
        memory = f"CROSS_VALIDATION_TEST_{unique_id}_{i}_CHAOS_MEMORY"
        test_memories.append({'id': unique_id, 'memory': memory, 'index': i})
    
    print(f"📝 Storing {len(test_memories)} unique memories...")
    
    # Phase 1: Store all memories
    for mem_data in test_memories:
        try:
            start_time = time.time()
            response = client.get_context(
                user_token='memory_test_user',
                message=f"Remember this important information: {mem_data['memory']}",
                is_new_conversation=False
            )
            duration = time.time() - start_time
            
            results.append({
                'phase': 'store',
                'memory_id': mem_data['id'],
                'success': True,
                'duration': duration,
                'response_size': len(response.text)
            })
            print(f"✅ Stored memory {mem_data['index'] + 1}/{len(test_memories)}")
            
        except Exception as e:
            results.append({
                'phase': 'store',
                'memory_id': mem_data['id'],
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e)
            })
            print(f"❌ Failed to store memory {mem_data['index'] + 1}: {e}")
    
    print("⏰ Waiting 30 seconds for memories to propagate...")
    time.sleep(30)
    
    # Phase 2: Try to retrieve each memory
    print(f"🔍 Attempting to retrieve {len(test_memories)} memories...")
    
    for mem_data in test_memories:
        try:
            start_time = time.time()
            response = client.get_context(
                user_token='memory_test_user',
                message=f"Do you remember anything about {mem_data['id']}? What information do you have?",
                is_new_conversation=False
            )
            duration = time.time() - start_time
            
            # Check if memory was found
            memory_found = mem_data['id'] in response.text
            
            results.append({
                'phase': 'retrieve',
                'memory_id': mem_data['id'],
                'success': memory_found,
                'duration': duration,
                'response_size': len(response.text),
                'memory_found': memory_found
            })
            
            status = "✅" if memory_found else "❌"
            print(f"{status} Memory {mem_data['index'] + 1}/{len(test_memories)}: {'FOUND' if memory_found else 'MISSING'}")
            
        except Exception as e:
            results.append({
                'phase': 'retrieve',
                'memory_id': mem_data['id'],
                'success': False,
                'duration': time.time() - start_time,
                'error': str(e),
                'memory_found': False
            })
            print(f"❌ Failed to retrieve memory {mem_data['index'] + 1}: {e}")
    
    # Generate report
    store_results = [r for r in results if r['phase'] == 'store']
    retrieve_results = [r for r in results if r['phase'] == 'retrieve']
    
    stores_successful = sum(1 for r in store_results if r['success'])
    memories_found = sum(1 for r in retrieve_results if r.get('memory_found', False))
    
    persistence_rate = (memories_found / len(test_memories)) if test_memories else 0
    
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🧠 MEMORY PERSISTENCE REPORT 🧠                        ║
╚════════════════════════════════════════════════════════════════════════════╝

📝 Memories Stored: {stores_successful}/{len(test_memories)} ({stores_successful/len(test_memories)*100:.1f}%)
🔍 Memories Retrieved: {memories_found}/{len(test_memories)} ({memories_found/len(test_memories)*100:.1f}%)
🧠 Persistence Rate: {persistence_rate*100:.1f}%

{('🎉 MEMORY SYSTEM IS ROCK SOLID!' if persistence_rate > 0.8 else '⚠️  MEMORY PERSISTENCE NEEDS WORK' if persistence_rate > 0.5 else '🚨 SERIOUS MEMORY ISSUES!')}
    """)
    
    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f'./logs/memory_persistence_report_{timestamp}.json', 'w') as f:
        json.dump({
            'metadata': {
                'total_memories': len(test_memories),
                'stores_successful': stores_successful,
                'memories_found': memories_found,
                'persistence_rate': persistence_rate
            },
            'results': results,
            'test_memories': test_memories
        }, f, indent=2)

if __name__ == "__main__":
    run_memory_cross_validation()
EOF

run_chaos_test "memory_validation" "cd '$SCRIPT_DIR' && python3 memory-cross-validation.py"

# Monitor all processes
echo "═══════════════════════════════════════════════════════════════════════════"
echo "👁️  CHAOS MONITORING"
echo "═══════════════════════════════════════════════════════════════════════════"

echo "🔥 ALL CHAOS TESTS LAUNCHED!"
echo ""
echo "📊 Monitoring active processes:"

# Show all PIDs
for pid_file in "$LOGS_DIR"/*_pid.txt; do
    if [ -f "$pid_file" ]; then
        test_name=$(basename "$pid_file" _pid.txt)
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "   ✅ $test_name (PID: $pid) - RUNNING"
        else
            echo "   ❌ $test_name (PID: $pid) - FINISHED"
        fi
    fi
done

echo ""
echo "📁 Real-time logs available in: $LOGS_DIR"
echo "🌐 React app (if running): http://localhost:3001"
echo ""
echo "⏳ Tests will run until completion. Monitor logs for results!"
echo "🛑 Use 'kill -9 <PID>' to stop individual tests if needed"
echo ""
echo "🔥 CHAOS ORCHESTRATOR: MISSION LAUNCHED! 🔥"
EOF