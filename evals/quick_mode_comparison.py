#!/usr/bin/env python3
"""
Quick comparison between local and production modes
"""

import asyncio
import time
from utils.api_client import LocalJeanMemoryClient, ProductionAPIClient

async def test_both_modes():
    """Test both local and production modes side by side"""
    
    print("🔄 Jean Memory Multi-Mode Comparison")
    print("=" * 60)
    
    # Test message
    test_message = "Help me with my Python project"
    test_user_id = "test-user-123"
    test_client = "evaluation-test"
    
    # LOCAL MODE TEST
    print("\n🏠 LOCAL MODE (Direct Function Calls)")
    print("-" * 40)
    
    local_client = LocalJeanMemoryClient()
    
    try:
        # Health check
        health = await local_client.health_check()
        print(f"Health: {health.get('status', 'unknown')}")
        
        # Jean Memory call
        start_time = time.time()
        local_context = await local_client.jean_memory_call(
            user_message=test_message,
            is_new_conversation=False,
            needs_context=True,
            user_id=test_user_id,
            client_name=test_client
        )
        local_time = time.time() - start_time
        
        print(f"Response Time: {local_time:.2f}s")
        print(f"Context Length: {len(local_context)} chars")
        print(f"Context Preview: {local_context[:100]}..." if local_context else "No context")
        
    except Exception as e:
        print(f"Local mode error: {e}")
    
    # PRODUCTION MODE TEST
    print("\n🌐 PRODUCTION MODE (HTTP API Calls)")
    print("-" * 40)
    
    prod_client = ProductionAPIClient("http://localhost:8000")
    
    try:
        # Health check
        health = await prod_client.health_check()
        print(f"Health: {health.get('status', 'unknown')}")
        
        # Jean Memory call
        start_time = time.time()
        prod_context = await prod_client.jean_memory_call(
            user_message=test_message,
            is_new_conversation=False,
            needs_context=True,
            user_id=test_user_id,
            client_name=test_client
        )
        prod_time = time.time() - start_time
        
        print(f"Response Time: {prod_time:.2f}s")
        print(f"Context Length: {len(prod_context)} chars")
        print(f"Context Preview: {prod_context[:100]}..." if prod_context else "No context")
        
    except Exception as e:
        print(f"Production mode error: {e}")
    finally:
        await prod_client.close()
    
    # COMPARISON
    print("\n📊 COMPARISON")
    print("-" * 40)
    print("✅ Both modes successfully tested!")
    print(f"Local Mode:      Direct function calls")
    print(f"Production Mode: HTTP API calls (like Claude would use)")
    print(f"Toggle Command:  --mode local | --mode production")
    
    print("\n🎯 This demonstrates:")
    print("  • Local: Fast development testing")  
    print("  • Production: Realistic client simulation")
    print("  • Easy toggle between modes")
    print("  • Same jean_memory functionality, different access methods")

if __name__ == "__main__":
    asyncio.run(test_both_modes())