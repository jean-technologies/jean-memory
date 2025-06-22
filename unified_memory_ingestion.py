#!/usr/bin/env python3
"""
Unified Memory Ingestion Pipeline
Implements mem0 for vector + graph storage and Graphiti for temporal episodes
Following official documentation patterns
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom Entity Types for Graphiti
class Person(BaseModel):
    """A person entity"""
    role: str | None = Field(..., description="The person's role or occupation")
    location: str | None = Field(..., description="Where the person is located")
    expertise: str | None = Field(..., description="The person's area of expertise")

class Activity(BaseModel):
    """An activity or action"""
    activity_type: str | None = Field(..., description="The type of activity")
    frequency: str | None = Field(..., description="How often the activity occurs")
    location: str | None = Field(..., description="Where the activity takes place")

class Project(BaseModel):
    """A project or work item"""
    project_type: str | None = Field(..., description="The type of project")
    status: str | None = Field(..., description="Current status of the project")
    category: str | None = Field(..., description="Category or type of project")

async def initialize_mem0():
    """Initialize mem0 with graph support following official docs"""
    from mem0 import Memory
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Configuration following official documentation
    config = {
        "graph_store": {
            "provider": "neo4j",
            "config": {
                "url": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                "username": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
            }
        },
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "user": os.getenv("PG_USER"),
                "password": os.getenv("PG_PASSWORD", ""),
                "host": os.getenv("PG_HOST"),
                "port": os.getenv("PG_PORT"),
                "dbname": os.getenv("PG_DBNAME", "mem0_test"),
                "collection_name": "unified_memory_mem0"
            }
        },
        "llm": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
                "api_key": os.getenv("OPENAI_API_KEY")
            }
        },
        "version": "v1.1",
        "history_db_path": "unified_memory_history.db"
    }
    
    # Handle SQLite history database issues
    history_db_path = Path(".mem0_history.db")
    
    # If database exists, fix the old_history table issue
    if history_db_path.exists():
        try:
            conn = sqlite3.connect(str(history_db_path))
            cursor = conn.cursor()
            
            # Check if old_history exists and drop it
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='old_history'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE old_history")
                conn.commit()
                logger.info("✅ Cleaned up old_history table")
            
            conn.close()
        except Exception as e:
            logger.warning(f"SQLite cleanup warning: {e}")
            # If we can't fix it, just remove the database
            history_db_path.unlink()
            logger.info("✅ Removed problematic SQLite database")
    
    # Initialize mem0
    try:
        memory = Memory.from_config(config_dict=config)
        logger.info("✅ mem0 initialized with graph support")
        return memory
    except Exception as e:
        # If still having issues, use a custom history path
        if "old_history" in str(e):
            config["history_db_path"] = ".mem0_history_new.db"
            memory = Memory.from_config(config_dict=config)
            logger.info("✅ mem0 initialized with new history database")
            return memory
        else:
            raise

async def initialize_graphiti():
    """Initialize Graphiti following official docs"""
    from graphiti_core import Graphiti
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Neo4j connection parameters
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "your-neo4j-password")
    
    # Initialize Graphiti
    graphiti = Graphiti(neo4j_uri, neo4j_user, neo4j_password)
    
    # Build indices and constraints
    await graphiti.build_indices_and_constraints()
    logger.info("✅ Graphiti initialized with indices built")
    
    return graphiti

async def add_memory_with_graph(memory, text: str, user_id: str, metadata: Dict[str, Any] = None):
    """Add memory using mem0 with automatic entity extraction"""
    
    logger.info(f"📝 Adding memory: {text[:60]}...")
    
    # Add memory - mem0 will automatically extract entities and create graph relationships
    result = memory.add(
        text,
        user_id=user_id,
        metadata=metadata or {}
    )
    
    logger.info(f"✅ Memory added with ID: {result.get('id', 'N/A')}")
    
    # The graph relationships are automatically created by mem0
    # including MENTIONS, RELATES_TO relationships
    
    return result

async def create_temporal_episode(graphiti, memories: List[Dict], episode_name: str, description: str):
    """Create temporal episode using Graphiti"""
    from graphiti_core.nodes import EpisodeType
    
    # Combine memories into episode content - handle both 'content' and 'text' fields
    episode_parts = []
    for m in memories[:5]:
        content = m.get('content', '') or m.get('text', '')
        if content:
            episode_parts.append(content[:100])
    
    episode_content = " | ".join(episode_parts)
    
    # Ensure we have content
    if not episode_content.strip():
        logger.warning(f"⚠️ No content found for episode {episode_name}")
        return None
    
    # Define entity types for this episode
    entity_types = {
        "Person": Person,
        "Activity": Activity,
        "Project": Project
    }
    
    logger.info(f"🎬 Creating episode: {episode_name}")
    logger.info(f"   Episode content length: {len(episode_content)} characters")
    
    try:
        # Add episode with custom entity types
        result = await graphiti.add_episode(
            name=episode_name,
            episode_body=episode_content,
            source=EpisodeType.text,
            source_description=description,
            reference_time=datetime.now(timezone.utc),
            entity_types=entity_types
        )
        
        logger.info(f"✅ Episode created: {episode_name}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to create episode {episode_name}: {e}")
        return None

async def search_unified_memory(memory, graphiti, query: str, user_id: str):
    """Search across both mem0 and Graphiti"""
    
    results = {
        "mem0_results": [],
        "graphiti_results": []
    }
    
    # Search mem0 (vector + graph)
    logger.info(f"🔍 Searching mem0 for: {query}")
    mem0_results = memory.search(query=query, user_id=user_id)
    results["mem0_results"] = mem0_results
    
    # Search Graphiti (temporal episodes)
    logger.info(f"🔍 Searching Graphiti for: {query}")
    graphiti_results = await graphiti.search(query)
    results["graphiti_results"] = graphiti_results
    
    return results

async def ingest_memories_unified(memories_data: List[Dict]):
    """Main ingestion pipeline using mem0 + Graphiti"""
    
    print("🚀 UNIFIED MEMORY INGESTION PIPELINE")
    print("=" * 80)
    
    # Initialize systems
    memory = await initialize_mem0()
    graphiti = await initialize_graphiti()
    
    user_id = os.getenv("TEST_USER_ID", "test-user-id")
    
    # Group memories by temporal context
    temporal_groups = {}
    
    # Step 1: Add all memories to mem0
    print("\n📥 Step 1: Adding memories to mem0...")
    for i, memory_data in enumerate(memories_data):
        text = memory_data.get('text', '')
        temporal_context = memory_data.get('temporal_context', 'Unknown')
        
        # Add to mem0 with metadata
        metadata = {
            "temporal_context": temporal_context,
            "confidence": memory_data.get('confidence', 'medium'),
            "temporal_keywords": memory_data.get('temporal_keywords', []),
            "created_at": memory_data.get('created_at', datetime.now().isoformat())
        }
        
        result = await add_memory_with_graph(memory, text, user_id, metadata)
        
        # Group for episodes
        if temporal_context not in temporal_groups:
            temporal_groups[temporal_context] = []
        temporal_groups[temporal_context].append({
            "text": text,
            "mem0_id": result.get('id'),
            **memory_data
        })
    
    # Step 2: Create temporal episodes with Graphiti
    print(f"\n🎬 Step 2: Creating {len(temporal_groups)} temporal episodes...")
    for context, group_memories in temporal_groups.items():
        if len(group_memories) >= 2:  # Only create episodes for grouped memories
            episode_name = f"episode_{context.lower().replace(' ', '_')[:30]}"
            await create_temporal_episode(
                graphiti,
                group_memories,
                episode_name,
                f"Temporal episode for {context}"
            )
    
    # Step 3: Verify integration
    print("\n🔍 Step 3: Verifying integration...")
    
    # Test search
    test_query = "What activities do I do?"
    results = await search_unified_memory(memory, graphiti, test_query, user_id)
    
    print(f"\n✅ INGESTION COMPLETE:")
    print(f"   mem0 memories: {len(results['mem0_results'])}")
    print(f"   Graphiti results: {len(results['graphiti_results'])}")
    
    # Close connections
    await graphiti.close()
    
    return memory, graphiti

async def test_with_sample_data():
    """Test the pipeline with sample data"""
    
    # Sample memories
    sample_memories = [
        {
            "text": "I go to Fitness SF Transbay gym for deadlifts",
            "temporal_context": "Ongoing routine as of 2025-06-17",
            "confidence": "medium",
            "temporal_keywords": ["go", "gym", "deadlifts"]
        },
        {
            "text": "I'm working on a computer vision project for fitness form analysis",
            "temporal_context": "Ongoing project as of 2025-06-17",
            "confidence": "medium",
            "temporal_keywords": ["working", "project", "fitness"]
        },
        {
            "text": "I cook ground turkey breakfast sandwiches regularly",
            "temporal_context": "Ongoing routine as of 2025-06-17",
            "confidence": "medium",
            "temporal_keywords": ["cook", "regularly"]
        }
    ]
    
    # Run ingestion
    memory, graphiti = await ingest_memories_unified(sample_memories)
    
    # Test queries
    print("\n🧪 TESTING QUERIES:")
    
    queries = [
        "What fitness activities do I do?",
        "Tell me about my projects",
        "What are my cooking habits?"
    ]
    
    for query in queries:
        print(f"\n❓ Query: {query}")
        results = await search_unified_memory(memory, graphiti, query, os.getenv("TEST_USER_ID", "test-user-id"))
        
        if results['mem0_results']:
            print(f"   mem0 found: {len(results['mem0_results'])} results")
            for r in results['mem0_results'][:2]:
                if isinstance(r, dict):
                    print(f"   - {r.get('memory', '')[:80]}...")
                else:
                    print(f"   - {str(r)[:80]}...")
        
        if results['graphiti_results']:
            print(f"   Graphiti found: {len(results['graphiti_results'])} results")
            for r in results['graphiti_results'][:2]:
                if hasattr(r, 'fact'):
                    print(f"   - {r.fact[:80]}...")
                else:
                    print(f"   - {str(r)[:80]}...")

async def migrate_existing_memories():
    """Migrate your existing enhanced_memories_openai to unified system"""
    
    print("📦 MIGRATING EXISTING MEMORIES TO UNIFIED SYSTEM")
    print("=" * 80)
    
    from qdrant_client import QdrantClient
    
    # Fetch existing memories
    qdrant_client = QdrantClient(host="localhost", port=6333)
    
    existing_memories = []
    offset = None
    
    while True:
        batch, offset = qdrant_client.scroll(
            collection_name="enhanced_memories_openai",
            limit=100,
            offset=offset,
            with_payload=True
        )
        
        if not batch:
            break
            
        existing_memories.extend(batch)
        
        if offset is None:
            break
    
    print(f"Found {len(existing_memories)} memories to migrate")
    
    # Convert to format for ingestion
    memories_to_ingest = []
    for memory_point in existing_memories:
        payload = memory_point.payload
        memories_to_ingest.append({
            "text": payload.get("text", ""),
            "temporal_context": payload.get("temporal_context", "Unknown"),
            "confidence": payload.get("confidence", "medium"),
            "temporal_keywords": payload.get("temporal_keywords", []),
            "created_at": payload.get("created_at", datetime.now().isoformat())
        })
    
    # Ingest using unified pipeline
    await ingest_memories_unified(memories_to_ingest)
    
    print("\n✅ Migration complete!")
    print("📝 Next steps:")
    print("   1. Update GraphRAG pipeline to use 'unified_memory_mem0' collection")
    print("   2. The graph now has both mem0 entities and Graphiti episodes")
    print("   3. You can query across both systems seamlessly")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        # Run migration
        asyncio.run(migrate_existing_memories())
    else:
        # Run test
        asyncio.run(test_with_sample_data()) 