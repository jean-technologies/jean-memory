#!/usr/bin/env python3
"""
User-Specific Unified Memory Testing Pipeline

This script:
1. Downloads memories for a specific user from Supabase
2. Runs them through the unified memory ingestion pipeline (mem0 + Graphiti)
3. Allows interactive querying of the ingested memories
4. Provides performance metrics and testing results

Usage:
    python test_user_unified_memory.py --user-id <USER_ID> [--sample-size 50] [--interactive]
"""

import os
import sys
import json
import asyncio
import logging
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import psycopg2
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserMemoryTester:
    """Complete testing pipeline for user-specific unified memory system"""
    
    def __init__(self, user_id: str, sample_size: int = 50):
        self.user_id = user_id
        self.sample_size = sample_size
        self.raw_memories = []
        self.processed_memories = []
        self.unified_memory = None
        self.graphiti = None
        
    def connect_to_supabase(self):
        """Connect to Supabase PostgreSQL database using existing pattern"""
        try:
            # Use environment variables for connection
            connection_params = {
                'host': os.getenv('SUPABASE_DB_HOST', 'db.masapxpxcwvsjpuymbmd.supabase.co'),
                'port': os.getenv('SUPABASE_DB_PORT', '5432'),
                'database': os.getenv('SUPABASE_DB_NAME', 'postgres'),
                'user': os.getenv('SUPABASE_DB_USER', 'postgres'),
                'password': os.getenv('SUPABASE_DB_PASSWORD')
            }
            
            # If password not in env, prompt for it
            if not connection_params['password']:
                logger.warning("⚠️  SUPABASE_DB_PASSWORD not found in environment")
                connection_params['password'] = input("Enter your Supabase database password: ")
            
            conn = psycopg2.connect(**connection_params)
            logger.info("✅ Connected to Supabase database")
            return conn
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def download_user_memories(self) -> List[Dict[str, Any]]:
        """Download memories for the specific user"""
        logger.info(f"📥 Downloading memories for user: {self.user_id}")
        
        conn = self.connect_to_supabase()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            
            # Get user info if available
            try:
                cursor.execute("""
                    SELECT email, created_at
                    FROM auth.users 
                    WHERE id = %s
                """, (self.user_id,))
                
                user_info = cursor.fetchone()
                if user_info:
                    logger.info(f"👤 Found user: {user_info[0]} (created: {user_info[1]})")
                else:
                    logger.info(f"👤 User ID: {self.user_id} (proceeding with download)")
            except Exception as e:
                logger.warning(f"⚠️  Could not query user info: {e}")
            
            # Download memories with limit for testing
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = %s 
                AND state = 'active'
                ORDER BY created_at DESC
                LIMIT %s
            """, (self.user_id, self.sample_size))
            
            memories = cursor.fetchall()
            logger.info(f"📚 Found {len(memories)} memories for user")
            
            # Convert to structured format
            raw_memories = []
            for memory in memories:
                memory_id, content, metadata, created_at, updated_at = memory
                
                raw_memory = {
                    "id": str(memory_id),
                    "text": content,  # Use 'text' field for consistency with pipeline
                    "content": content,
                    "metadata": metadata if metadata else {},
                    "created_at": created_at.isoformat() if created_at else None,
                    "updated_at": updated_at.isoformat() if updated_at else None,
                    "user_id": self.user_id,
                    "memory_date": created_at.isoformat() if created_at else None,
                    "temporal_context": f"Memory from {created_at.strftime('%Y-%m-%d')}" if created_at else "Unknown date",
                    "confidence": "medium"  # Default confidence
                }
                raw_memories.append(raw_memory)
            
            cursor.close()
            conn.close()
            
            self.raw_memories = raw_memories
            return raw_memories
            
        except Exception as e:
            logger.error(f"❌ Error downloading memories: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                conn.close()
            return []
    
    def save_raw_memories(self, filename: Optional[str] = None):
        """Save downloaded memories to file"""
        if not filename:
            filename = f"user_{self.user_id[:8]}_raw_memories.json"
        
        output_data = {
            "user_id": self.user_id,
            "download_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_memories": len(self.raw_memories),
            "sample_size": self.sample_size,
            "memories": self.raw_memories
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(self.raw_memories)} raw memories to {filename}")
        return filename
    
    async def preprocess_memories(self) -> List[Dict[str, Any]]:
        """Preprocess memories with Gemini for better temporal context"""
        if not self.raw_memories:
            logger.error("❌ No raw memories to preprocess")
            return []
        
        logger.info(f"🤖 Preprocessing {len(self.raw_memories)} memories with Gemini...")
        
        try:
            # Try to import and use existing preprocessing
            from preprocess_memories_gemini_batch import preprocess_memories_batch
            
            # Preprocess memories in batches
            enhanced_memories = await preprocess_memories_batch(
                self.raw_memories,
                batch_size=10
            )
            
            logger.info(f"✅ Enhanced {len(enhanced_memories)} memories")
            
            # Show confidence distribution
            confidence_dist = {}
            for mem in enhanced_memories:
                conf = mem.get('confidence', 'unknown')
                confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
            
            logger.info(f"📊 Confidence distribution: {confidence_dist}")
            
            self.processed_memories = enhanced_memories
            return enhanced_memories
            
        except ImportError:
            logger.warning("⚠️  Gemini preprocessing not available, using raw memories")
            self.processed_memories = self.raw_memories
            return self.raw_memories
        except Exception as e:
            logger.error(f"❌ Preprocessing failed: {e}")
            logger.info("📝 Using raw memories without preprocessing")
            self.processed_memories = self.raw_memories
            return self.raw_memories
    
    async def initialize_unified_system(self):
        """Initialize the unified memory system (mem0 + Graphiti)"""
        logger.info("🧠 Initializing unified memory system...")
        
        try:
            # Import unified memory components
            from unified_memory_ingestion import initialize_mem0, initialize_graphiti
            
            # Initialize mem0
            logger.info("  🔧 Initializing mem0...")
            self.unified_memory = await initialize_mem0()
            logger.info("  ✅ mem0 ready")
            
            # Initialize Graphiti
            logger.info("  🔧 Initializing Graphiti...")
            self.graphiti = await initialize_graphiti()
            logger.info("  ✅ Graphiti ready")
            
            logger.info("🚀 Unified memory system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize unified system: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def ingest_memories(self) -> Dict[str, Any]:
        """Ingest processed memories into unified system"""
        if not self.processed_memories:
            logger.error("❌ No processed memories to ingest")
            return {}
        
        if not self.unified_memory or not self.graphiti:
            logger.error("❌ Unified system not initialized")
            return {}
        
        logger.info(f"📝 Ingesting {len(self.processed_memories)} memories...")
        
        ingestion_results = {
            "total_memories": len(self.processed_memories),
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "mem0_results": [],
            "temporal_episodes": 0,
            "errors": []
        }
        
        # Ingest memories one by one
        for i, memory in enumerate(self.processed_memories, 1):
            try:
                logger.info(f"  📝 Ingesting memory {i}/{len(self.processed_memories)}: {memory['text'][:50]}...")
                
                # Add to mem0 (handles vector storage + entity extraction)
                result = self.unified_memory.add(
                    memory['text'],
                    user_id=self.user_id,
                    metadata={
                        "temporal_context": memory.get('temporal_context', ''),
                        "confidence": memory.get('confidence', 'medium'),
                        "original_created_at": memory.get('created_at'),
                        "memory_date": memory.get('memory_date'),
                        "test_ingestion": True
                    }
                )
                
                ingestion_results["mem0_results"].append(result)
                ingestion_results["successful_ingestions"] += 1
                
                logger.info(f"    ✅ mem0 ID: {result.get('id', 'unknown')}")
                
            except Exception as e:
                logger.error(f"    ❌ Failed to ingest memory {i}: {e}")
                ingestion_results["failed_ingestions"] += 1
                ingestion_results["errors"].append(str(e))
        
        # Create temporal episodes with Graphiti
        try:
            logger.info("🎬 Creating temporal episodes with Graphiti...")
            
            # Group memories by temporal context for episodes
            temporal_groups = {}
            for memory in self.processed_memories:
                context = memory.get('temporal_context', 'Unknown')
                if context not in temporal_groups:
                    temporal_groups[context] = []
                temporal_groups[context].append(memory)
            
            # Create episodes for each temporal group
            from unified_memory_ingestion import create_temporal_episode
            
            for context, memories in temporal_groups.items():
                if len(memories) >= 2:  # Only create episodes for groups with multiple memories
                    episode_name = f"user_{self.user_id[:8]}_{context.lower().replace(' ', '_')}"
                    episode_description = f"Temporal episode: {context}"
                    
                    await create_temporal_episode(
                        self.graphiti,
                        memories,
                        episode_name,
                        episode_description
                    )
                    
                    ingestion_results["temporal_episodes"] += 1
            
            logger.info(f"✅ Created {ingestion_results['temporal_episodes']} temporal episodes")
            
        except Exception as e:
            logger.error(f"❌ Failed to create temporal episodes: {e}")
            ingestion_results["errors"].append(f"Temporal episodes: {str(e)}")
        
        logger.info("📊 Ingestion Summary:")
        logger.info(f"  ✅ Successful: {ingestion_results['successful_ingestions']}")
        logger.info(f"  ❌ Failed: {ingestion_results['failed_ingestions']}")
        logger.info(f"  🎬 Episodes: {ingestion_results['temporal_episodes']}")
        
        return ingestion_results
    
    async def test_queries(self) -> List[Dict[str, Any]]:
        """Test the unified system with sample queries"""
        if not self.unified_memory or not self.graphiti:
            logger.error("❌ Unified system not initialized")
            return []
        
        # Import search function
        from unified_memory_ingestion import search_unified_memory
        
        # Test queries
        test_queries = [
            "What activities do I do?",
            "Tell me about my recent memories",
            "What happened this week?",
            "Who are the people I interact with?",
            "What are my interests?"
        ]
        
        query_results = []
        
        logger.info(f"🔍 Testing {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n❓ Query {i}: {query}")
            
            try:
                results = await search_unified_memory(
                    self.unified_memory,
                    self.graphiti,
                    query,
                    self.user_id
                )
                
                query_result = {
                    "query": query,
                    "mem0_results": len(results.get('mem0_results', [])),
                    "graphiti_results": len(results.get('graphiti_results', [])),
                    "success": True
                }
                
                logger.info(f"  📊 mem0: {query_result['mem0_results']} results")
                logger.info(f"  📊 Graphiti: {query_result['graphiti_results']} results")
                
                # Show top results
                if results.get('mem0_results'):
                    for j, result in enumerate(results['mem0_results'][:2], 1):
                        memory_text = result.get('memory', result.get('text', str(result)))
                        logger.info(f"    {j}. {memory_text[:60]}...")
                
                query_results.append(query_result)
                
            except Exception as e:
                logger.error(f"  ❌ Query failed: {e}")
                query_results.append({
                    "query": query,
                    "error": str(e),
                    "success": False
                })
        
        return query_results
    
    async def interactive_mode(self):
        """Interactive query mode for testing"""
        if not self.unified_memory or not self.graphiti:
            logger.error("❌ Unified system not initialized")
            return
        
        from unified_memory_ingestion import search_unified_memory
        
        print("\n🚀 Interactive Query Mode")
        print("=" * 50)
        print(f"👤 User: {self.user_id}")
        print(f"📚 Memories ingested: {len(self.processed_memories)}")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                query = input("❓ Your query: ").strip()
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not query:
                    continue
                
                print(f"🔍 Searching for: {query}")
                
                results = await search_unified_memory(
                    self.unified_memory,
                    self.graphiti,
                    query,
                    self.user_id
                )
                
                # Display results
                print("\n📊 Results:")
                print(f"  mem0: {len(results.get('mem0_results', []))} results")
                print(f"  Graphiti: {len(results.get('graphiti_results', []))} results")
                
                # Show top mem0 results
                if results.get('mem0_results'):
                    print("\n🧠 Top mem0 Results:")
                    for i, result in enumerate(results['mem0_results'][:3], 1):
                        memory_text = result.get('memory', result.get('text', str(result)))
                        print(f"  {i}. {memory_text[:80]}...")
                
                # Show Graphiti results
                if results.get('graphiti_results'):
                    print("\n🎬 Graphiti Results:")
                    for i, result in enumerate(results['graphiti_results'][:3], 1):
                        if hasattr(result, 'fact'):
                            print(f"  {i}. {result.fact[:80]}...")
                        else:
                            print(f"  {i}. {str(result)[:80]}...")
                
                print("\n" + "-" * 50)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def run_complete_test(self, interactive: bool = False) -> Dict[str, Any]:
        """Run the complete testing pipeline"""
        logger.info(f"🚀 Starting complete unified memory test for user: {self.user_id}")
        logger.info(f"�� Sample size: {self.sample_size}")
        
        test_results = {
            "user_id": self.user_id,
            "sample_size": self.sample_size,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "stages": {}
        }
        
        try:
            # Stage 1: Download memories
            logger.info("\n" + "=" * 60)
            logger.info("📥 STAGE 1: DOWNLOADING USER MEMORIES")
            logger.info("=" * 60)
            
            memories = self.download_user_memories()
            if not memories:
                raise Exception("No memories downloaded")
            
            self.save_raw_memories()
            test_results["stages"]["download"] = {
                "success": True,
                "memories_count": len(memories)
            }
            
            # Stage 2: Preprocess memories
            logger.info("\n" + "=" * 60)
            logger.info("🤖 STAGE 2: PREPROCESSING MEMORIES")
            logger.info("=" * 60)
            
            processed = await self.preprocess_memories()
            test_results["stages"]["preprocessing"] = {
                "success": True,
                "processed_count": len(processed)
            }
            
            # Stage 3: Initialize unified system
            logger.info("\n" + "=" * 60)
            logger.info("🧠 STAGE 3: INITIALIZING UNIFIED SYSTEM")
            logger.info("=" * 60)
            
            init_success = await self.initialize_unified_system()
            if not init_success:
                raise Exception("Failed to initialize unified system")
            
            test_results["stages"]["initialization"] = {"success": True}
            
            # Stage 4: Ingest memories
            logger.info("\n" + "=" * 60)
            logger.info("📝 STAGE 4: INGESTING MEMORIES")
            logger.info("=" * 60)
            
            ingestion_results = await self.ingest_memories()
            test_results["stages"]["ingestion"] = ingestion_results
            
            # Stage 5: Test queries
            logger.info("\n" + "=" * 60)
            logger.info("🔍 STAGE 5: TESTING QUERIES")
            logger.info("=" * 60)
            
            query_results = await self.test_queries()
            test_results["stages"]["queries"] = query_results
            
            # Stage 6: Interactive mode (if requested)
            if interactive:
                logger.info("\n" + "=" * 60)
                logger.info("🎮 STAGE 6: INTERACTIVE MODE")
                logger.info("=" * 60)
                
                await self.interactive_mode()
            
            test_results["end_time"] = datetime.now(timezone.utc).isoformat()
            test_results["success"] = True
            
            # Final summary
            logger.info("\n" + "=" * 60)
            logger.info("🎉 TEST COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            logger.info(f"👤 User: {self.user_id}")
            logger.info(f"�� Memories processed: {len(self.processed_memories)}")
            logger.info(f"✅ Successful ingestions: {ingestion_results.get('successful_ingestions', 0)}")
            logger.info(f"🎬 Temporal episodes: {ingestion_results.get('temporal_episodes', 0)}")
            logger.info(f"🔍 Test queries: {len([q for q in query_results if q.get('success')])}")
            
            return test_results
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            
            test_results["end_time"] = datetime.now(timezone.utc).isoformat()
            test_results["success"] = False
            test_results["error"] = str(e)
            
            return test_results

def main():
    parser = argparse.ArgumentParser(
        description='Test unified memory system with specific user data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python test_user_unified_memory.py --user-id abc123 --sample-size 30
  python test_user_unified_memory.py --user-id abc123 --interactive
  python test_user_unified_memory.py --user-id abc123 --sample-size 100 --interactive""")
    
    parser.add_argument(
        '--user-id', 
        required=True, 
        help='User ID to download memories for'
    )
    parser.add_argument(
        '--sample-size', 
        type=int, 
        default=50, 
        help='Number of memories to download and test (default: 50)'
    )
    parser.add_argument(
        '--interactive', 
        action='store_true', 
        help='Enter interactive query mode after testing'
    )
    parser.add_argument(
        '--save-results', 
        help='Save test results to JSON file'
    )
    
    args = parser.parse_args()
    
    async def run_test():
        tester = UserMemoryTester(args.user_id, args.sample_size)
        results = await tester.run_complete_test(interactive=args.interactive)
        
        if args.save_results:
            with open(args.save_results, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"💾 Test results saved to {args.save_results}")
        
        return results
    
    # Run the async test
    asyncio.run(run_test())

if __name__ == "__main__":
    main() 