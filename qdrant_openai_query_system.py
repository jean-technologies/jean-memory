#!/usr/bin/env python3
"""
Qdrant OpenAI Query System

This script provides a comprehensive interface for querying your enhanced memories
using OpenAI embeddings (consistent with mem0) and Qdrant vector search.
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Set environment
os.environ["ENVIRONMENT"] = "development"

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QdrantOpenAIQuerySystem:
    """Enhanced memory query system using OpenAI embeddings and Qdrant"""
    
    def __init__(self):
        self.qdrant_client = None
        self.openai_client = None
        self.collection_name = "enhanced_memories_openai"
        self.embedding_model = "text-embedding-3-small"  # Latest OpenAI model
        self.embedding_dimension = 1536  # text-embedding-3-small dimension
        
    async def initialize(self):
        """Initialize Qdrant and OpenAI clients"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams
            from openai import OpenAI
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # Initialize clients
            self.qdrant_client = QdrantClient(host="localhost", port=6333)
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Create collection with OpenAI embedding dimensions
            try:
                self.qdrant_client.get_collection(self.collection_name)
                logger.info(f"✅ Collection '{self.collection_name}' already exists")
            except:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.embedding_dimension, distance=Distance.COSINE),
                )
                logger.info(f"✅ Created new collection '{self.collection_name}' with OpenAI embeddings")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    def get_openai_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"❌ OpenAI embedding failed: {e}")
            return None
    
    async def reingest_with_openai_embeddings(self):
        """Re-ingest memories using OpenAI embeddings"""
        logger.info("🔄 Re-ingesting memories with OpenAI embeddings...")
        
        # Load enhanced memories
        with open("sample_30_preprocessed_v2.json", 'r') as f:
            data = json.load(f)
        
        memories = data.get('memories', [])
        user_id = data.get('user_id', 'fa97efb5-410d-4806-b137-8cf13b6cb464')
        
        logger.info(f"📥 Processing {len(memories)} memories with OpenAI embeddings...")
        
        # Clear existing data
        try:
            self.qdrant_client.delete_collection(self.collection_name)
        except:
            pass
        
        # Recreate collection
        from qdrant_client.http.models import Distance, VectorParams
        self.qdrant_client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.embedding_dimension, distance=Distance.COSINE),
        )
        
        # Process memories with OpenAI embeddings
        from qdrant_client.http.models import PointStruct
        
        points = []
        for i, memory in enumerate(memories):
            try:
                memory_text = memory.get('memory_text', '')
                
                # Generate OpenAI embedding
                embedding = self.get_openai_embedding(memory_text)
                if not embedding:
                    continue
                
                # Create point with enhanced metadata
                point = PointStruct(
                    id=i + 1,
                    vector=embedding,
                    payload={
                        "original_id": memory.get('id', ''),
                        "user_id": user_id,
                        "text": memory_text,
                        "confidence": memory.get('confidence', 'medium'),
                        "temporal_context": memory.get('temporal_context', ''),
                        "temporal_keywords": memory.get('temporal_keywords', []),
                        "reasoning": memory.get('reasoning', ''),
                        "created_at": memory.get('created_at', ''),
                        "enhanced_processing": True,
                        "embedding_model": self.embedding_model,
                        "source": "enhanced_preprocessing_v2_openai"
                    }
                )
                
                points.append(point)
                
                if len(points) % 10 == 0:
                    logger.info(f"  📊 Generated embeddings for {len(points)}/{len(memories)} memories")
                
            except Exception as e:
                logger.error(f"  ❌ Error processing memory {i}: {e}")
        
        # Upload all points
        if points:
            self.qdrant_client.upsert(collection_name=self.collection_name, points=points)
            logger.info(f"✅ Successfully ingested {len(points)} memories with OpenAI embeddings")
        
        return len(points)
    
    async def semantic_search(self, query: str, limit: int = 10, min_score: float = 0.3) -> List[Dict]:
        """Perform semantic search on memories"""
        logger.info(f"🔍 Searching for: '{query}'")
        
        # Generate query embedding
        query_embedding = self.get_openai_embedding(query)
        if not query_embedding:
            return []
        
        # Search Qdrant
        search_results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=min_score
        )
        
        results = []
        for result in search_results:
            results.append({
                "score": result.score,
                "text": result.payload.get("text", ""),
                "confidence": result.payload.get("confidence", ""),
                "temporal_context": result.payload.get("temporal_context", ""),
                "temporal_keywords": result.payload.get("temporal_keywords", []),
                "reasoning": result.payload.get("reasoning", ""),
                "created_at": result.payload.get("created_at", "")
            })
        
        logger.info(f"✅ Found {len(results)} relevant memories")
        return results
    
    async def filter_search(self, filters: Dict[str, Any], limit: int = 20) -> List[Dict]:
        """Search with filters (confidence, temporal context, etc.)"""
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue
        
        # Build filter conditions
        conditions = []
        for key, value in filters.items():
            if key == "confidence":
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            elif key == "contains_text":
                # This would need to be done post-search since Qdrant doesn't have text search
                pass
        
        # Perform filtered search
        search_results = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(must=conditions) if conditions else None,
            limit=limit
        )
        
        results = []
        for result in search_results[0]:  # scroll returns (points, next_page_offset)
            payload = result.payload
            
            # Apply text filters post-search
            if "contains_text" in filters:
                if filters["contains_text"].lower() not in payload.get("text", "").lower():
                    continue
            
            results.append({
                "text": payload.get("text", ""),
                "confidence": payload.get("confidence", ""),
                "temporal_context": payload.get("temporal_context", ""),
                "temporal_keywords": payload.get("temporal_keywords", []),
                "reasoning": payload.get("reasoning", ""),
                "created_at": payload.get("created_at", "")
            })
        
        logger.info(f"✅ Found {len(results)} filtered memories")
        return results
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            
            # Get sample of memories for analysis
            sample_results = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                limit=100
            )
            
            # Analyze confidence distribution
            confidence_counts = {}
            temporal_contexts = []
            
            for result in sample_results[0]:
                confidence = result.payload.get("confidence", "unknown")
                confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
                
                temporal_context = result.payload.get("temporal_context", "")
                if temporal_context:
                    temporal_contexts.append(temporal_context)
            
            return {
                "total_memories": collection_info.points_count,
                "embedding_model": self.embedding_model,
                "embedding_dimension": self.embedding_dimension,
                "confidence_distribution": confidence_counts,
                "sample_temporal_contexts": temporal_contexts[:10]
            }
            
        except Exception as e:
            logger.error(f"❌ Stats collection failed: {e}")
            return {}

# Interactive CLI
async def interactive_query_session():
    """Interactive query session"""
    system = QdrantOpenAIQuerySystem()
    
    logger.info("🚀 Initializing Qdrant OpenAI Query System...")
    if not await system.initialize():
        return
    
    # Check if we need to reingest with OpenAI embeddings
    try:
        stats = await system.get_collection_stats()
        if stats.get("total_memories", 0) == 0:
            logger.info("📥 No memories found. Ingesting with OpenAI embeddings...")
            await system.reingest_with_openai_embeddings()
        else:
            logger.info(f"✅ Found {stats.get('total_memories', 0)} memories in collection")
    except:
        logger.info("📥 Creating new collection with OpenAI embeddings...")
        await system.reingest_with_openai_embeddings()
    
    # Show stats
    stats = await system.get_collection_stats()
    logger.info("\n📊 COLLECTION STATISTICS:")
    logger.info(f"  Total memories: {stats.get('total_memories', 0)}")
    logger.info(f"  Embedding model: {stats.get('embedding_model', 'unknown')}")
    logger.info(f"  Confidence distribution: {stats.get('confidence_distribution', {})}")
    
    # Interactive queries
    logger.info("\n🎯 READY FOR QUERIES!")
    logger.info("Try these example queries:")
    logger.info("  - 'workout exercise fitness'")
    logger.info("  - 'food cooking restaurant'") 
    logger.info("  - 'work job career'")
    logger.info("  - 'travel vacation trip'")
    
    while True:
        try:
            query = input("\n🔍 Enter your search query (or 'quit' to exit): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Perform search
            results = await system.semantic_search(query, limit=5)
            
            if results:
                logger.info(f"\n✅ TOP {len(results)} RESULTS:")
                for i, result in enumerate(results, 1):
                    logger.info(f"\n{i}. Score: {result['score']:.3f} | Confidence: {result['confidence']}")
                    logger.info(f"   Memory: {result['text'][:100]}...")
                    logger.info(f"   Context: {result['temporal_context']}")
                    if result['temporal_keywords']:
                        logger.info(f"   Keywords: {', '.join(result['temporal_keywords'])}")
            else:
                logger.info("❌ No relevant memories found. Try a different query.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
    
    logger.info("👋 Query session ended!")

# Batch query examples
async def run_example_queries():
    """Run example queries to demonstrate the system"""
    system = QdrantOpenAIQuerySystem()
    
    if not await system.initialize():
        return
    
    # Ensure data is ingested
    stats = await system.get_collection_stats()
    if stats.get("total_memories", 0) == 0:
        await system.reingest_with_openai_embeddings()
    
    example_queries = [
        "fitness workout exercise gym",
        "food cooking restaurant dining",
        "work career job professional",
        "travel vacation trip adventure",
        "learning education books reading",
        "technology software programming",
        "family relationships friends social"
    ]
    
    logger.info("🎯 RUNNING EXAMPLE QUERIES:")
    
    for query in example_queries:
        logger.info(f"\n🔍 Query: '{query}'")
        results = await system.semantic_search(query, limit=3)
        
        if results:
            for i, result in enumerate(results, 1):
                logger.info(f"  {i}. [{result['score']:.3f}] {result['text'][:80]}...")
        else:
            logger.info("  No matches found")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Qdrant OpenAI Query System')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run interactive query session')
    parser.add_argument('--examples', '-e', action='store_true', help='Run example queries')
    parser.add_argument('--reingest', '-r', action='store_true', help='Reingest memories with OpenAI embeddings')
    
    args = parser.parse_args()
    
    if args.interactive:
        asyncio.run(interactive_query_session())
    elif args.examples:
        asyncio.run(run_example_queries())
    elif args.reingest:
        async def reingest():
            system = QdrantOpenAIQuerySystem()
            if await system.initialize():
                await system.reingest_with_openai_embeddings()
        asyncio.run(reingest())
    else:
        # Default to interactive
        asyncio.run(interactive_query_session()) 