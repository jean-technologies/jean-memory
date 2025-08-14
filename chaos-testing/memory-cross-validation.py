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
