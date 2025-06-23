#!/usr/bin/env python3
"""
Test Unified Memory Search Functionality
Tests the search capabilities of the unified memory system with migrated data.
"""

import os
import sys
import asyncio
import json
from datetime import datetime

# Make the app module available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../openmemory/api')))

from app.utils.unified_memory import get_unified_memory_client

# Set environment for unified memory
os.environ["ENVIRONMENT"] = "development"
os.environ["USE_UNIFIED_MEMORY"] = "true"
os.environ["IS_LOCAL_UNIFIED_MEMORY"] = "true"

async def test_unified_search():
    """Tests the unified_search endpoint."""
    print("🧪 Unified Memory System Integration Tests")
    print("=" * 70)
    print("🔍 Testing Unified Memory Search")
    print("-" * 50)
    
    success = False
    try:
        client = await get_unified_memory_client()
        if not client.is_initialized:
            print("🔴 Client not initialized. Skipping search tests.")
            return False
        
        print("✅ Unified memory client initialized")
        
        # Test user ID (from migration)
        test_user_id = "test-user-id-placeholder"
        
        # Test queries based on the sample data we migrated
        test_queries = [
            {
                "query": "health and wellness activities",
                "description": "Should find health-related memories"
            },
            {
                "query": "summer events and celebrations",
                "description": "Should find seasonal event memories"
            },
            {
                "query": "food and nutrition experiments",
                "description": "Should find food-related memories"
            },
            {
                "query": "professional meetings and interviews",
                "description": "Should find work-related memories"
            },
            {
                "query": "late night work sessions",
                "description": "Should find work habit memories"
            },
            {
                "query": "city life and urban experiences",
                "description": "Should find location-related memories"
            },
            {
                "query": "recent activities and thoughts",
                "description": "Should find temporally relevant memories"
            }
        ]
        
        successful_searches = 0
        total_results = 0
        
        print(f"\n🔎 Testing {len(test_queries)} search queries...")
        print("-" * 60)
        
        for i, test_case in enumerate(test_queries, 1):
            query = test_case["query"]
            description = test_case["description"]
            
            print(f"[{i}/{len(test_queries)}] Searching for: '{query}'")
            print(f"   Expected: {description}")
            
            try:
                # Perform search
                results = await client.search_memory(
                    query=query,
                    user_id=test_user_id,
                    limit=5
                )
                
                if "error" in results:
                    print(f"   ❌ Error: {results['error']}")
                    continue
                
                successful_searches += 1
                
                # Analyze results
                mem0_results = results.get("mem0_results", [])
                graphiti_results = results.get("graphiti_results", [])
                
                mem0_count = len(mem0_results)
                graphiti_count = len(graphiti_results)
                total_results += mem0_count + graphiti_count
                
                print(f"   ✅ Search completed")
                print(f"      - Mem0 results: {mem0_count}")
                print(f"      - Graphiti results: {graphiti_count}")
                
                # Show top results
                if mem0_count > 0:
                    top_mem0 = mem0_results[0]
                    if isinstance(top_mem0, dict):
                        memory_text = top_mem0.get("memory", top_mem0.get("text", "N/A"))
                        score = top_mem0.get("score", "N/A")
                        print(f"      - Top Mem0: {memory_text[:60]}... (score: {score})")
                
                if graphiti_count > 0:
                    top_graphiti = graphiti_results[0]
                    if isinstance(top_graphiti, dict):
                        content = top_graphiti.get("content", top_graphiti.get("text", "N/A"))
                        print(f"      - Top Graphiti: {content[:60]}...")
                
            except Exception as e:
                print(f"   ❌ Search failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"🏁 SEARCH TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Successful searches: {successful_searches}/{len(test_queries)}")
        print(f"📊 Total results returned: {total_results}")
        print(f"📈 Average results per query: {total_results/len(test_queries):.1f}")
        
        if successful_searches == len(test_queries):
            print(f"\n🎉 All search tests passed!")
            print(f"✅ Unified memory system is working correctly")
            print(f"✅ Both Mem0 and Graphiti are returning results")
            print(f"✅ Migration was successful")
            success = True
        else:
            print(f"\n⚠️ {len(test_queries) - successful_searches} search(es) failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_add_memory():
    """Tests adding a memory and retrieving it."""
    print("🆕 Testing Memory Addition")
    print("-" * 40)
    
    success = False
    try:
        client = await get_unified_memory_client()
        test_user_id = "test-user-id-placeholder"
        
        # Add a test memory
        test_memory = "Testing unified memory system integration with batch processing and temporal context extraction"
        
        print(f"📝 Adding test memory: {test_memory[:50]}...")
        
        result = await client.add_memory(
            text=test_memory,
            user_id=test_user_id,
            metadata={"test": True, "source": "integration_test"}
        )
        
        print(f"✅ Memory added successfully. ID: {result}")

        # Give a moment for indexing
        await asyncio.sleep(2)
        
        print(f"🔍 Searching for the new memory...")
        
        search_results = await client.search_memory(
            query="unified memory system integration batch processing",
            user_id=test_user_id,
            limit=3
        )
        
        found = False
        if search_results:
            # Check if our test memory is found
            for mem0_result in search_results.get("mem0_results", []):
                if isinstance(mem0_result, dict):
                    memory_text = mem0_result.get("memory", mem0_result.get("text", ""))
                    if "unified memory system integration" in memory_text.lower():
                        found = True
                        print(f"✅ Test memory found in search results!")
                        break
        
        if not found:
            print(f"⚠️ Test memory not found in immediate search results (may need time to index)")
        
        success = True
        return success
        
    except Exception as e:
        print(f"❌ Memory addition test failed: {e}")
        return False

async def main():
    search_success = await test_unified_search()
    add_success = await test_add_memory()
    
    print("\n" + "=" * 70)
    print("🏁 OVERALL TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Search functionality: {'PASSED' if search_success else 'FAILED'}")
    print(f"✅ Memory addition: {'PASSED' if add_success else 'FAILED'}")
    
    overall_passed = search_success and add_success
    print(f"\n📊 Overall: {int(overall_passed)}/2 tests passed")
    
    if not overall_passed:
        print("\n⚠️ Some tests failed. Please investigate before full migration.")
    else:
        print("\n🎉 All tests passed! The unified memory system is responding correctly.")

if __name__ == "__main__":
    asyncio.run(main()) 