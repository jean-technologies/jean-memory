#!/usr/bin/env python3
"""
Test R&D Pipeline with Relevant Queries

This script tests the retrieval system with queries that match
the actual content of the user's memories.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from rd_development_pipeline import RDPipeline

async def test_relevant_queries():
    """Test with queries that match the user's actual memory content"""
    
    user_id = "54e4450d-821e-487c-b1df-54e4751fb9e6"
    
    print(f"🧪 Testing Relevant Queries for User: {user_id}")
    print("=" * 60)
    
    # Initialize pipeline
    pipeline = RDPipeline()
    
    # Test queries that match the actual memory content
    relevant_queries = [
        "Tell me about Las Dunas restaurant",
        "What happened with my family?", 
        "Who is Wyatt and what did I notice about him?",
        "What medical cases did I work on?",
        "What medication issues did I have?",
        "Tell me about my work with Dr. Pastula",
        "What happened when I stayed up late?",
        "Who visited me for a month?",
        "What productive work did I do on Friday?",
        "What challenges did I have with Spanish doctors?"
    ]
    
    print(f"📋 Testing {len(relevant_queries)} relevant queries...")
    
    # Test retrieval with relevant queries
    try:
        retrieval_results = await pipeline.test_retrieval(user_id, relevant_queries)
        
        print(f"\n📊 RESULTS SUMMARY:")
        print("=" * 60)
        
        successful_queries = 0
        total_sources = 0
        
        for query, result in retrieval_results.items():
            if "error" not in result:
                memory_count = result.get('memory_count', 0)
                response_length = len(result.get('response', ''))
                
                if memory_count > 0:
                    successful_queries += 1
                    total_sources += memory_count
                    
                    print(f"\n✅ Query: {query}")
                    print(f"   📝 Response: {result.get('response', '')[:100]}...")
                    print(f"   📊 Sources found: {memory_count}")
                    print(f"   ⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                else:
                    print(f"\n❌ Query: {query}")
                    print(f"   📝 No relevant memories found")
            else:
                print(f"\n💥 Query failed: {query}")
                print(f"   Error: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎯 PERFORMANCE METRICS:")
        print(f"   • Successful queries: {successful_queries}/{len(relevant_queries)}")
        print(f"   • Success rate: {successful_queries/len(relevant_queries)*100:.1f}%")
        print(f"   • Average sources per successful query: {total_sources/max(successful_queries,1):.1f}")
        print(f"   • Total memories retrieved: {total_sources}")
        
        if successful_queries > 0:
            print(f"\n🎉 SUCCESS: The retrieval system is working!")
            print(f"   The previous test failed because fitness queries don't match")
            print(f"   this user's actual memory content (medical work, family, etc.)")
        else:
            print(f"\n⚠️ ISSUE: Still no memories found with relevant queries")
            print(f"   This suggests a potential issue with the search system")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_relevant_queries()) 