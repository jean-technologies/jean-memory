#!/usr/bin/env python3
"""
Test script to debug agentic orchestration locally
"""

import asyncio
import logging
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging to see all our debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_agentic_orchestration():
    """Test the agentic orchestration with logging."""
    try:
        # Import after setting up logging
        from app.mcp_orchestration import get_smart_orchestrator
        from app.context import user_id_var, client_name_var, background_tasks_var
        from fastapi import BackgroundTasks
        
        print("🚀 Starting agentic orchestration test...")
        
        # Set up context (simulating a real request)
        test_user_id = "test_user_123"
        test_client = "test_client"
        background_tasks = BackgroundTasks()
        
        user_token = user_id_var.set(test_user_id)
        client_token = client_name_var.set(test_client)
        tasks_token = background_tasks_var.set(background_tasks)
        
        try:
            # Get orchestrator instance
            orchestrator = get_smart_orchestrator()
            
            # Test with weather question (should need context for location)
            print("\n" + "="*60)
            print("TEST 1: Weather question (should need location context)")
            print("="*60)
            
            result = await orchestrator.orchestrate_smart_context(
                user_message="what's the weather like",
                user_id=test_user_id,
                client_name=test_client,
                is_new_conversation=False,
                needs_context=True,
                background_tasks=background_tasks
            )
            
            print(f"\n📋 FINAL RESULT:")
            print(f"Length: {len(result)} characters")
            print(f"Content: {result}")
            
            print("\n" + "="*60)
            print("TEST 2: Generic question (shouldn't need context)")
            print("="*60)
            
            result2 = await orchestrator.orchestrate_smart_context(
                user_message="what is 2 + 2",
                user_id=test_user_id,
                client_name=test_client,
                is_new_conversation=False,
                needs_context=True,
                background_tasks=background_tasks
            )
            
            print(f"\n📋 FINAL RESULT:")
            print(f"Length: {len(result2)} characters")
            print(f"Content: {result2}")
            
        finally:
            # Clean up context
            user_id_var.reset(user_token)
            client_name_var.reset(client_token)  
            background_tasks_var.reset(tasks_token)
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agentic_orchestration())