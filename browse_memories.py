#!/usr/bin/env python3
"""
Browse Your Enhanced Memories

Simple interface to explore your memories and run semantic searches.
"""

import asyncio
from qdrant_openai_query_system import QdrantOpenAIQuerySystem

async def browse_memories():
    system = QdrantOpenAIQuerySystem()
    
    print("🚀 Initializing memory browser...")
    if not await system.initialize():
        print("❌ Failed to initialize")
        return
    
    # Show all memories first
    try:
        from qdrant_client.http.models import Filter
        all_results = system.qdrant_client.scroll(
            collection_name=system.collection_name,
            limit=30
        )
        
        print(f"\n📚 YOUR {len(all_results[0])} ENHANCED MEMORIES:")
        print("="*60)
        
        for i, result in enumerate(all_results[0], 1):
            payload = result.payload
            print(f"\n{i}. [{payload.get('confidence', 'unknown')}] {payload.get('text', '')[:80]}...")
            print(f"   Context: {payload.get('temporal_context', '')}")
            if payload.get('temporal_keywords'):
                print(f"   Keywords: {', '.join(payload.get('temporal_keywords', []))}")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"❌ Error browsing memories: {e}")
        return
    
    # Interactive search
    print("\n🔍 SEMANTIC SEARCH")
    print("Try searching for:")
    print("  - 'fitness' or 'workout'")
    print("  - 'food' or 'restaurant'") 
    print("  - 'work' or 'career'")
    print("  - 'San Francisco' or 'location'")
    print("  - Any topic you're interested in!")
    
    while True:
        try:
            query = input("\n🔍 Search query (or 'quit'): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Search with low threshold
            results = await system.semantic_search(query, limit=5, min_score=0.2)
            
            if results:
                print(f"\n✅ FOUND {len(results)} RELEVANT MEMORIES:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. Score: {result['score']:.3f} | Confidence: {result['confidence']}")
                    print(f"   Memory: {result['text']}")
                    print(f"   Context: {result['temporal_context']}")
                    if result['temporal_keywords']:
                        print(f"   Keywords: {', '.join(result['temporal_keywords'])}")
            else:
                print("❌ No matches found. Try a broader search term.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print("\n👋 Memory browser closed!")

if __name__ == "__main__":
    asyncio.run(browse_memories()) 