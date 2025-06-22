#!/usr/bin/env python3
"""
Test GraphRAG Relationship Discovery Fix
Verify that the fixed pipeline now discovers relationships correctly
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphrag_pipeline import GraphRAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_relationship_discovery():
    """Test that the fixed GraphRAG pipeline discovers relationships"""
    
    print("🧪 Testing GraphRAG Relationship Discovery Fix")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = GraphRAGPipeline()
    user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
    
    # Test queries that should find relationships
    test_queries = [
        "What fitness activities do I do?",
        "Tell me about my cooking habits",
        "What work activities have I done?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🎯 Test {i}: '{query}'")
        print("-" * 40)
        
        try:
            # Process query
            start_time = datetime.now()
            
            # Step 1: Query Decomposition
            entities, query_type, temporal_context = await pipeline._decompose_query(query)
            print(f"📝 Query Decomposition:")
            print(f"  Entities: {entities}")
            print(f"  Type: {query_type}")
            
            # Step 2: Semantic Search
            seed_memories = await pipeline._semantic_search(query, user_id)
            print(f"🔍 Semantic Search:")
            print(f"  Found {len(seed_memories)} seed memories")
            
            # Step 3: Graph Expansion (THE KEY TEST)
            expanded_context = await pipeline._expand_graph_context(entities, seed_memories, user_id)
            print(f"🕸️ Graph Expansion:")
            print(f"  Nodes: {len(expanded_context.get('nodes', []))}")
            print(f"  Relationships: {len(expanded_context.get('relationships', []))}")
            
            if expanded_context.get('relationships'):
                rel_types = [r['type'] for r in expanded_context['relationships']]
                unique_types = list(set(rel_types))
                print(f"  Relationship types: {unique_types}")
                print(f"  TEMPORAL_NEIGHBOR: {rel_types.count('TEMPORAL_NEIGHBOR')}")
                print(f"  RELATED_TOPIC: {rel_types.count('RELATED_TOPIC')}")
                print(f"  ✅ SUCCESS: Relationships discovered!")
            else:
                print(f"  ❌ FAILED: No relationships found")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            print(f"⏱️ Processing time: {processing_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            logger.exception("Query processing failed")
    
    print(f"\n🎉 GraphRAG Relationship Discovery Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_relationship_discovery()) 