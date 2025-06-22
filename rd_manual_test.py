#!/usr/bin/env python3
"""
Manual R&D Test Script

Since your Supabase service key has restricted permissions (which is good for security),
this script allows you to test the R&D pipeline with a specific user ID.

Usage:
    python rd_manual_test.py --user-id USER_ID
    python rd_manual_test.py --user-id USER_ID --sample-size 50
"""

import asyncio
import argparse
from rd_development_pipeline import RDPipeline

async def main():
    parser = argparse.ArgumentParser(description="Manual R&D Test with Specific User ID")
    parser.add_argument("--user-id", required=True, help="User ID to test with")
    parser.add_argument("--sample-size", type=int, default=30, help="Number of memories to sample")
    
    args = parser.parse_args()
    
    print(f"🔬 Manual R&D Test")
    print(f"=" * 50)
    print(f"User ID: {args.user_id}")
    print(f"Sample Size: {args.sample_size}")
    
    # Initialize pipeline
    pipeline = RDPipeline()
    
    try:
        # Step 1: Download memories
        print(f"\n1️⃣ Downloading {args.sample_size} memories for user {args.user_id}...")
        memories = pipeline.download_user_memories(args.user_id, args.sample_size)
        
        if not memories:
            print("❌ No memories found for this user ID")
            print("\n💡 Tips:")
            print("   • Check if the user ID is correct")
            print("   • Try a different user ID")
            print("   • Verify the user has memories in the database")
            return
        
        print(f"   ✅ Downloaded {len(memories)} memories")
        
        # Step 2: Ingest into unified memory system
        print(f"\n2️⃣ Ingesting memories into unified system...")
        ingestion_results = await pipeline.ingest_memories(memories, args.user_id)
        print(f"   ✅ Ingested {ingestion_results['mem0_ingested']} into mem0")
        print(f"   ✅ Created {ingestion_results['graphiti_episodes']} temporal episodes")
        
        if ingestion_results['errors']:
            print(f"   ⚠️ {len(ingestion_results['errors'])} errors occurred")
        
        # Step 3: Test retrieval
        print(f"\n3️⃣ Testing GraphRAG retrieval...")
        test_queries = [
            "What exercises do I do?",
            "Where do I like to work out?",
            "What are my fitness goals?",
            "What projects am I working on?",
            "Who do I work with?",
            "What are my daily routines?"
        ]
        
        retrieval_results = await pipeline.test_retrieval(args.user_id, test_queries)
        successful_queries = len([q for q, r in retrieval_results.items() if "error" not in r])
        print(f"   ✅ Successful queries: {successful_queries}/{len(test_queries)}")
        
        # Step 4: Analyze results
        print(f"\n4️⃣ Analyzing results...")
        analysis = pipeline.analyze_results(args.user_id)
        
        # Print sample results
        print(f"\n📊 Sample Results:")
        for query, result in list(retrieval_results.items())[:2]:
            if "error" not in result:
                response = result.get('response', '')[:200]
                sources = len(result.get('sources', []))
                print(f"   Q: {query}")
                print(f"   A: {response}{'...' if len(response) == 200 else ''}")
                print(f"   Sources: {sources}")
                print()
        
        # Summary
        success_rate = analysis.get('retrieval_analysis', {}).get('success_rate', 0)
        print(f"🎯 Pipeline Summary:")
        print(f"   • User ID: {args.user_id}")
        print(f"   • Memories processed: {len(memories)}")
        print(f"   • Mem0 ingestion: {ingestion_results['mem0_ingested']}")
        print(f"   • Graphiti episodes: {ingestion_results['graphiti_episodes']}")
        print(f"   • Retrieval success rate: {success_rate:.1%}")
        print(f"   • Recommendations: {len(analysis.get('recommendations', []))}")
        
        print(f"\n📁 Results saved to rd_data/ folder:")
        print(f"   • user_{args.user_id}_memories.json")
        print(f"   • user_{args.user_id}_retrieval_results.json")
        print(f"   • user_{args.user_id}_analysis.json")
        
        print(f"\n🎉 R&D test complete!")
        print(f"\n🔄 Next steps:")
        print(f"   • Try different sample sizes: --sample-size 50")
        print(f"   • Test with different user IDs")
        print(f"   • Analyze results in rd_data/ folder")
        print(f"   • Refine algorithms based on findings")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   • Check if user ID exists in database")
        print(f"   • Verify Supabase credentials")
        print(f"   • Check rd_pipeline.log for details")

if __name__ == "__main__":
    asyncio.run(main()) 