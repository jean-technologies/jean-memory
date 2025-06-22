#!/usr/bin/env python3
"""
R&D Development Pipeline for Unified Memory System

This script provides a streamlined R&D environment for:
1. Downloading real customer data from Supabase
2. Running unified memory ingestion locally
3. Testing GraphRAG retrieval
4. Interactive analysis and refinement

Usage:
    python rd_development_pipeline.py --user-id USER_ID [options]
    python rd_development_pipeline.py --interactive  # Browse available users
    python rd_development_pipeline.py --user-id USER_ID --sample-size 100 --analyze
"""

import os
import sys
import json
import time
import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rd_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class RDPipeline:
    """R&D Pipeline for Unified Memory System Development"""
    
    def __init__(self):
        self.db_connection = None
        self.mem0_client = None
        self.graphiti_client = None
        self.graphrag_pipeline = None
        self.data_dir = Path("rd_data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize connections
        self._init_supabase()
        
    def _init_supabase(self):
        """Initialize direct PostgreSQL connection for data download"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # Direct PostgreSQL connection to Supabase
            db_config = {
                'host': 'db.masapxpxcwvsjpuymbmd.supabase.co',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres',
                'password': 'jeanmemorytypefasho'
            }
            
            self.db_connection = psycopg2.connect(**db_config)
            logger.info("✅ Connected to PostgreSQL database for data download")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    async def _init_unified_memory(self):
        """Initialize local unified memory system"""
        try:
            from unified_memory_ingestion import initialize_mem0, initialize_graphiti
            
            # Force local development mode
            os.environ['ENVIRONMENT'] = 'development'
            os.environ['USE_UNIFIED_MEMORY'] = 'true'
            
            # Initialize mem0 and graphiti separately
            self.mem0_client = await initialize_mem0()
            self.graphiti_client = await initialize_graphiti()
            
            logger.info("✅ Unified memory system initialized locally")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize unified memory: {e}")
            raise
    
    async def _init_graphrag(self):
        """Initialize GraphRAG pipeline"""
        try:
            from graphrag_pipeline import GraphRAGPipeline
            
            self.graphrag_pipeline = GraphRAGPipeline()
            logger.info("✅ GraphRAG pipeline initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GraphRAG: {e}")
            raise
    
    def list_available_users(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List available users with memory counts"""
        try:
            from psycopg2.extras import RealDictCursor
            
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            
            # Get users with memory counts, filtering for users with at least 5 memories
            cursor.execute("""
                SELECT user_id, COUNT(*) as memory_count 
                FROM memories 
                WHERE deleted_at IS NULL
                GROUP BY user_id 
                HAVING COUNT(*) >= 5
                ORDER BY memory_count DESC 
                LIMIT %s;
            """, (limit,))
            
            users = cursor.fetchall()
            cursor.close()
            
            if not users:
                logger.warning("No users found with sufficient memories")
                return []
            
            logger.info(f"✅ Found {len(users)} users with memories")
            return [{"user_id": user['user_id'], "memory_count": user['memory_count']} for user in users]
            
        except Exception as e:
            logger.error(f"❌ Failed to list users: {e}")
            return []
    
    def download_user_memories(self, user_id: str, sample_size: Optional[int] = None) -> List[Dict[str, Any]]:
        """Download memories for a specific user"""
        try:
            from psycopg2.extras import RealDictCursor
            
            logger.info(f"📥 Downloading memories for user: {user_id}")
            
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            
            # Get all memories for the user, excluding deleted ones
            if sample_size:
                cursor.execute("""
                    SELECT m.*, u.email as user_email
                    FROM memories m 
                    LEFT JOIN users u ON m.user_id = u.id 
                    WHERE m.user_id = %s AND m.deleted_at IS NULL
                    ORDER BY m.created_at DESC 
                    LIMIT %s;
                """, (user_id, sample_size))
            else:
                cursor.execute("""
                    SELECT m.*, u.email as user_email
                    FROM memories m 
                    LEFT JOIN users u ON m.user_id = u.id 
                    WHERE m.user_id = %s AND m.deleted_at IS NULL
                    ORDER BY m.created_at DESC;
                """, (user_id,))
            
            memories = cursor.fetchall()
            cursor.close()
            
            if not memories:
                logger.warning(f"⚠️ No memories found for user: {user_id}")
                return []
            
            # Convert to list of dicts for JSON serialization
            memories_list = [dict(memory) for memory in memories]
            logger.info(f"✅ Downloaded {len(memories_list)} memories for user {user_id}")
            
            # Save to file for analysis
            output_file = self.data_dir / f"user_{user_id}_memories.json"
            with open(output_file, 'w') as f:
                json.dump(memories_list, f, indent=2, default=str)
            
            logger.info(f"💾 Saved memories to: {output_file}")
            return memories_list
            
        except Exception as e:
            logger.error(f"❌ Failed to download memories: {e}")
            return []
    
    async def ingest_memories(self, memories: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """Ingest memories into unified memory system"""
        try:
            logger.info(f"🔄 Ingesting {len(memories)} memories into unified system...")
            
            if not hasattr(self, 'mem0_client') or not self.mem0_client:
                await self._init_unified_memory()
            
            results = {
                "total_memories": len(memories),
                "mem0_ingested": 0,
                "graphiti_episodes": 0,
                "errors": []
            }
            
            for i, memory in enumerate(memories):
                try:
                    # Extract memory content
                    content = memory.get('content', '')
                    if not content:
                        continue
                    
                    # Ingest into mem0
                    mem0_result = self.mem0_client.add(
                        content,
                        user_id=user_id,
                        metadata={
                            "original_id": memory.get('id'),
                            "created_at": memory.get('created_at'),
                            "updated_at": memory.get('updated_at')
                        }
                    )
                    
                    if mem0_result:
                        results["mem0_ingested"] += 1
                    
                    # Progress update
                    if (i + 1) % 10 == 0:
                        logger.info(f"   Processed {i + 1}/{len(memories)} memories...")
                        
                except Exception as e:
                    error_msg = f"Error processing memory {i}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Create temporal episodes with Graphiti (simplified for R&D)
            try:
                from unified_memory_ingestion import create_temporal_episode
                
                # Group memories by time periods for episodes
                if len(memories) >= 5:
                    episode_memories = memories[:5]  # Take first 5 for episode
                    episode_result = await create_temporal_episode(
                        self.graphiti_client,
                        episode_memories,
                        f"User_{user_id}_Episode_{datetime.now().strftime('%Y%m%d_%H%M')}",
                        f"Memory episode for user {user_id}"
                    )
                    results["graphiti_episodes"] = 1
                else:
                    results["graphiti_episodes"] = 0
                    
            except Exception as e:
                error_msg = f"Graphiti ingestion error: {str(e)}"
                logger.warning(error_msg)
                results["errors"].append(error_msg)
                results["graphiti_episodes"] = 0
            
            logger.info(f"✅ Ingestion complete: {results['mem0_ingested']} mem0, {results['graphiti_episodes']} episodes")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest memories: {e}")
            raise
    
    async def test_retrieval(self, user_id: str, test_queries: List[str]) -> Dict[str, Any]:
        """Test unified memory retrieval with various queries"""
        try:
            logger.info(f"🔍 Testing retrieval with {len(test_queries)} queries...")
            
            if not hasattr(self, 'mem0_client') or not self.mem0_client:
                await self._init_unified_memory()
            
            results = {}
            
            for query in test_queries:
                logger.info(f"   Testing query: '{query}'")
                
                try:
                    # Test mem0 search (includes vector + graph)
                    start_time = time.time()
                    
                    search_results = self.mem0_client.search(
                        query=query,
                        user_id=user_id,
                        limit=10
                    )
                    
                    processing_time = time.time() - start_time
                    
                    # Extract results - handle mem0's response format
                    if isinstance(search_results, dict):
                        memories = search_results.get('results', [])
                        relations = search_results.get('relations', [])
                    elif isinstance(search_results, list):
                        memories = search_results
                        relations = []
                    else:
                        memories = []
                        relations = []
                    
                    # Create response from top memories
                    if memories:
                        response_parts = []
                        for mem in memories[:3]:  # Top 3 memories
                            if isinstance(mem, dict):
                                content = mem.get('memory', mem.get('text', mem.get('content', '')))
                                if content:
                                    response_parts.append(content)
                        
                        response = " | ".join(response_parts) if response_parts else "No relevant memories found"
                        
                        # Add relation information if available
                        if relations:
                            relation_info = f" [Relations: {len(relations)} found]"
                            response += relation_info
                    else:
                        response = "No memories found"
                    
                    results[query] = {
                        "response": response,
                        "sources": memories,
                        "confidence": 1.0 if memories else 0.0,
                        "processing_time": processing_time,
                        "memory_count": len(memories)
                    }
                    
                    logger.info(f"     ✅ Response length: {len(response)}")
                    logger.info(f"     📊 Sources: {len(memories)}")
                    
                except Exception as e:
                    logger.error(f"     ❌ Query failed: {str(e)}")
                    results[query] = {"error": str(e)}
            
            # Save results
            output_file = self.data_dir / f"user_{user_id}_retrieval_results.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"💾 Saved retrieval results to: {output_file}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to test retrieval: {e}")
            raise
    
    def analyze_results(self, user_id: str) -> Dict[str, Any]:
        """Analyze ingestion and retrieval results"""
        try:
            logger.info(f"📊 Analyzing results for user: {user_id}")
            
            analysis = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "memory_analysis": {},
                "retrieval_analysis": {},
                "recommendations": []
            }
            
            # Analyze memories
            memory_file = self.data_dir / f"user_{user_id}_memories.json"
            if memory_file.exists():
                with open(memory_file, 'r') as f:
                    memories = json.load(f)
                
                analysis["memory_analysis"] = {
                    "total_memories": len(memories),
                    "date_range": self._get_date_range(memories),
                    "content_types": self._analyze_content_types(memories),
                    "avg_content_length": sum(len(m.get('content', '')) for m in memories) / len(memories)
                }
            
            # Analyze retrieval results
            retrieval_file = self.data_dir / f"user_{user_id}_retrieval_results.json"
            if retrieval_file.exists():
                with open(retrieval_file, 'r') as f:
                    retrieval_results = json.load(f)
                
                successful_queries = [q for q, r in retrieval_results.items() if "error" not in r]
                
                analysis["retrieval_analysis"] = {
                    "total_queries": len(retrieval_results),
                    "successful_queries": len(successful_queries),
                    "success_rate": len(successful_queries) / len(retrieval_results) if retrieval_results else 0,
                    "avg_response_length": self._calc_avg_response_length(retrieval_results),
                    "avg_sources_per_query": self._calc_avg_sources(retrieval_results)
                }
            
            # Generate recommendations
            analysis["recommendations"] = self._generate_recommendations(analysis)
            
            # Save analysis
            output_file = self.data_dir / f"user_{user_id}_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            logger.info(f"💾 Saved analysis to: {output_file}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze results: {e}")
            return {}
    
    def _get_date_range(self, memories: List[Dict[str, Any]]) -> Dict[str, str]:
        """Get date range of memories"""
        dates = [m.get('created_at') for m in memories if m.get('created_at')]
        if not dates:
            return {}
        
        return {
            "earliest": min(dates),
            "latest": max(dates),
            "span_days": (datetime.fromisoformat(max(dates).replace('Z', '+00:00')) - 
                         datetime.fromisoformat(min(dates).replace('Z', '+00:00'))).days
        }
    
    def _analyze_content_types(self, memories: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze content types in memories"""
        types = {}
        for memory in memories:
            content = memory.get('content', '').lower()
            if 'workout' in content or 'exercise' in content or 'gym' in content:
                types['fitness'] = types.get('fitness', 0) + 1
            elif 'work' in content or 'meeting' in content or 'project' in content:
                types['work'] = types.get('work', 0) + 1
            elif 'travel' in content or 'trip' in content:
                types['travel'] = types.get('travel', 0) + 1
            else:
                types['general'] = types.get('general', 0) + 1
        
        return types
    
    def _calc_avg_response_length(self, results: Dict[str, Any]) -> float:
        """Calculate average response length"""
        lengths = [len(r.get('response', '')) for r in results.values() if 'response' in r]
        return sum(lengths) / len(lengths) if lengths else 0
    
    def _calc_avg_sources(self, results: Dict[str, Any]) -> float:
        """Calculate average sources per query"""
        source_counts = [len(r.get('sources', [])) for r in results.values() if 'sources' in r]
        return sum(source_counts) / len(source_counts) if source_counts else 0
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        memory_analysis = analysis.get("memory_analysis", {})
        retrieval_analysis = analysis.get("retrieval_analysis", {})
        
        # Memory recommendations
        if memory_analysis.get("total_memories", 0) < 10:
            recommendations.append("Consider testing with more memories for better analysis")
        
        if memory_analysis.get("avg_content_length", 0) < 50:
            recommendations.append("Memories are quite short - consider preprocessing to extract more context")
        
        # Retrieval recommendations
        success_rate = retrieval_analysis.get("success_rate", 0)
        if success_rate < 0.8:
            recommendations.append("Low retrieval success rate - check query processing and error handling")
        
        avg_sources = retrieval_analysis.get("avg_sources_per_query", 0)
        if avg_sources < 2:
            recommendations.append("Low source diversity - consider improving graph traversal")
        
        return recommendations
    
    async def interactive_mode(self):
        """Interactive mode for R&D exploration"""
        print("\n🔬 R&D Interactive Mode")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. List available users")
            print("2. Download user memories")
            print("3. Ingest memories")
            print("4. Test retrieval")
            print("5. Analyze results")
            print("6. Full pipeline run")
            print("0. Exit")
            
            choice = input("\nSelect option: ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                users = self.list_available_users()
                print(f"\n📋 Available Users ({len(users)}):")
                for user in users[:10]:  # Show top 10
                    print(f"   {user.get('user_id', 'N/A')} - {user.get('memory_count', 0)} memories")
            
            elif choice == "2":
                user_id = input("Enter user ID: ").strip()
                sample_size = input("Sample size (press Enter for all): ").strip()
                sample_size = int(sample_size) if sample_size else None
                
                memories = self.download_user_memories(user_id, sample_size)
                print(f"✅ Downloaded {len(memories)} memories")
            
            elif choice == "3":
                user_id = input("Enter user ID: ").strip()
                memory_file = self.data_dir / f"user_{user_id}_memories.json"
                
                if not memory_file.exists():
                    print(f"❌ No memories file found for user {user_id}. Download first.")
                    continue
                
                with open(memory_file, 'r') as f:
                    memories = json.load(f)
                
                results = await self.ingest_memories(memories, user_id)
                print(f"✅ Ingestion complete: {results}")
            
            elif choice == "4":
                user_id = input("Enter user ID: ").strip()
                queries = [
                    "What exercises do I do?",
                    "Where do I like to work out?",
                    "What are my fitness goals?",
                    "What projects am I working on?",
                    "Who do I work with?"
                ]
                
                results = await self.test_retrieval(user_id, queries)
                print(f"✅ Tested {len(results)} queries")
            
            elif choice == "5":
                user_id = input("Enter user ID: ").strip()
                analysis = self.analyze_results(user_id)
                
                print(f"\n📊 Analysis Summary:")
                print(f"   Memories: {analysis.get('memory_analysis', {}).get('total_memories', 0)}")
                print(f"   Success Rate: {analysis.get('retrieval_analysis', {}).get('success_rate', 0):.2%}")
                print(f"   Recommendations: {len(analysis.get('recommendations', []))}")
            
            elif choice == "6":
                user_id = input("Enter user ID: ").strip()
                sample_size = input("Sample size (press Enter for 50): ").strip()
                sample_size = int(sample_size) if sample_size else 50
                
                print(f"\n🚀 Running full pipeline for user {user_id}...")
                
                # Download
                memories = self.download_user_memories(user_id, sample_size)
                if not memories:
                    print("❌ No memories to process")
                    continue
                
                # Ingest
                await self.ingest_memories(memories, user_id)
                
                # Test retrieval
                test_queries = [
                    "What exercises do I do?",
                    "Where do I like to work out?",
                    "What are my fitness goals?",
                    "What projects am I working on?",
                    "Who do I work with?",
                    "What are my daily routines?",
                    "What places do I visit frequently?"
                ]
                
                await self.test_retrieval(user_id, test_queries)
                
                # Analyze
                analysis = self.analyze_results(user_id)
                
                print(f"\n🎉 Pipeline complete! Check rd_data/ for results.")
                print(f"📊 Success rate: {analysis.get('retrieval_analysis', {}).get('success_rate', 0):.2%}")

async def main():
    parser = argparse.ArgumentParser(description="R&D Development Pipeline")
    parser.add_argument("--user-id", help="User ID to process")
    parser.add_argument("--sample-size", type=int, help="Number of memories to sample")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--analyze", action="store_true", help="Run analysis after processing")
    parser.add_argument("--list-users", action="store_true", help="List available users")
    
    args = parser.parse_args()
    
    pipeline = RDPipeline()
    
    if args.interactive:
        await pipeline.interactive_mode()
    elif args.list_users:
        users = pipeline.list_available_users()
        print(f"\n📋 Available Users ({len(users)}):")
        for user in users:
            print(f"   {user.get('user_id', 'N/A')} - {user.get('memory_count', 0)} memories")
    elif args.user_id:
        # Run pipeline for specific user
        memories = pipeline.download_user_memories(args.user_id, args.sample_size)
        if memories:
            await pipeline.ingest_memories(memories, args.user_id)
            
            test_queries = [
                "What exercises do I do?",
                "Where do I like to work out?",
                "What are my fitness goals?",
                "What projects am I working on?",
                "Who do I work with?"
            ]
            
            await pipeline.test_retrieval(args.user_id, test_queries)
            
            if args.analyze:
                pipeline.analyze_results(args.user_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main()) 