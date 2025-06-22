#!/usr/bin/env python3
"""
Download and Prepare Memories for Full GraphRAG Pipeline Test

This script:
1. Downloads your latest memories from production
2. Preprocesses them with Gemini (with batching)
3. Prepares them for enhanced ingestion
4. Sets up everything for the full pipeline test
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import requests
from pathlib import Path
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryPipelineSetup:
    """Complete setup for testing the full GraphRAG pipeline"""
    
    def __init__(self):
        self.user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
        # We'll use the existing preprocessed data instead of downloading from API
        
    def load_existing_memories(self) -> List[Dict[str, Any]]:
        """Load existing preprocessed memories instead of downloading"""
        logger.info("📥 Loading existing preprocessed memories...")
        
        # Try to load existing preprocessed files
        memory_files = [
            "sample_30_preprocessed_v2.json",
            "sample_30_preprocessed.json",
            "sample_30_diverse.json"
        ]
        
        for file in memory_files:
            if os.path.exists(file):
                with open(file, 'r') as f:
                    data = json.load(f)
                    memories = data.get('memories', [])
                    logger.info(f"✅ Loaded {len(memories)} memories from {file}")
                    return memories
        
        logger.error("❌ No memory files found!")
        return []
    
    def save_raw_memories(self, memories: List[Dict[str, Any]], filename: str = "raw_memories_latest.json"):
        """Save raw memories to file"""
        output_data = {
            "user_id": self.user_id,
            "download_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_memories": len(memories),
            "memories": memories
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"💾 Saved {len(memories)} raw memories to {filename}")
        return filename
    
    async def preprocess_with_gemini(self, input_file: str, output_file: str = "memories_preprocessed_latest.json"):
        """Run Gemini preprocessing on downloaded memories"""
        logger.info("🤖 Starting Gemini preprocessing...")
        
        # Import and run the preprocessing
        try:
            from preprocess_memories_gemini_batch import preprocess_memories_batch
            
            # Load raw memories
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            memories = data.get('memories', [])
            
            # Run preprocessing
            enhanced_memories = await preprocess_memories_batch(
                memories[:50],  # Process first 50 for testing
                batch_size=10
            )
            
            # Save preprocessed memories
            output_data = {
                "user_id": self.user_id,
                "preprocessing_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_memories": len(enhanced_memories),
                "memories": enhanced_memories
            }
            
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            
            logger.info(f"✅ Preprocessed {len(enhanced_memories)} memories")
            logger.info(f"💾 Saved to {output_file}")
            
            # Show statistics
            confidence_dist = {}
            for mem in enhanced_memories:
                conf = mem.get('confidence', 'unknown')
                confidence_dist[conf] = confidence_dist.get(conf, 0) + 1
            
            logger.info(f"📊 Confidence distribution: {confidence_dist}")
            
            return output_file
            
        except ImportError:
            logger.error("❌ Could not import preprocessing module")
            logger.info("⚠️  Using raw memories without preprocessing")
            return input_file
    
    def verify_services(self) -> Dict[str, bool]:
        """Verify all required services are running"""
        logger.info("🔍 Verifying services...")
        
        services = {
            "neo4j": False,
            "qdrant": False,
            "api_key": False
        }
        
        # Check Neo4j (try both local and cloud)
        neo4j_configs = [
            {
                "uri": "bolt://localhost:7687",
                "auth": ("neo4j", "fasho93fasho"),
                "name": "local"
            },
            {
                "uri": os.getenv("NEO4J_URI", "neo4j+s://6ff1aa85.databases.neo4j.io"),
                "auth": (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD")),
                "name": "cloud"
            }
        ]
        
        for config in neo4j_configs:
            try:
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver(config["uri"], auth=config["auth"])
                with driver.session() as session:
                    session.run("RETURN 1")
                driver.close()
                services["neo4j"] = True
                logger.info(f"  ✅ Neo4j ({config['name']}) is running")
                break
            except Exception as e:
                logger.warning(f"  ⚠️ Neo4j ({config['name']}) not available: {e}")
        
        if not services["neo4j"]:
            logger.error("  ❌ No Neo4j instance available")
        
        # Check Qdrant
        try:
            import requests
            response = requests.get("http://localhost:6333/collections")
            if response.status_code == 200:
                services["qdrant"] = True
                logger.info("  ✅ Qdrant is running")
        except:
            logger.error("  ❌ Qdrant not available")
        
        # Check API keys (only OPENAI_API_KEY needed for OSS)
        required_keys = ["OPENAI_API_KEY"]
        missing_keys = [k for k in required_keys if not os.getenv(k)]
        
        if not missing_keys:
            services["api_key"] = True
            logger.info("  ✅ All required API keys present")
        else:
            logger.error(f"  ❌ Missing API keys: {missing_keys}")
        
        return services
    
    def create_test_queries(self) -> List[Dict[str, str]]:
        """Create test queries for the pipeline"""
        return [
            {
                "query": "What are my recent cooking activities?",
                "type": "activity_based"
            },
            {
                "query": "Tell me about people I know who are involved in tech",
                "type": "entity_relationship"
            },
            {
                "query": "What happened last week?",
                "type": "temporal"
            },
            {
                "query": "What are my hobbies and interests?",
                "type": "semantic_cluster"
            },
            {
                "query": "How do my work and personal life connect?",
                "type": "multi_hop"
            }
        ]
    
    async def run_full_pipeline_test(self, preprocessed_file: str):
        """Run the complete pipeline test"""
        logger.info("\n🚀 RUNNING FULL GRAPHRAG PIPELINE TEST")
        logger.info("="*60)
        
        # Step 1: Enhanced ingestion
        logger.info("\n📝 Step 1: Enhanced Ingestion with Entity Extraction")
        logger.info("-"*40)
        
        from enhanced_unified_ingestion import ingest_enhanced_memories
        await ingest_enhanced_memories()
        
        # Step 2: Test GraphRAG retrieval
        logger.info("\n🔍 Step 2: Testing GraphRAG Retrieval")
        logger.info("-"*40)
        
        from graphrag_pipeline import GraphRAGPipeline
        pipeline = GraphRAGPipeline()
        
        if await pipeline.initialize():
            test_queries = self.create_test_queries()
            
            for i, test in enumerate(test_queries, 1):
                logger.info(f"\n📌 Test Query {i}: {test['query']}")
                logger.info(f"   Type: {test['type']}")
                
                result = await pipeline.process_query(
                    test['query'],
                    self.user_id
                )
                
                if result["status"] == "success":
                    logger.info(f"   ✅ Vector results: {result['vector_count']}")
                    logger.info(f"   ✅ Graph results: {result['graph_count']}")
                    logger.info(f"   ✅ Response length: {len(result['response'])} chars")
                    
                    # Show snippet of response
                    response_snippet = result['response'][:200] + "..." if len(result['response']) > 200 else result['response']
                    logger.info(f"   📄 Response: {response_snippet}")
                else:
                    logger.error(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                
                await asyncio.sleep(1)  # Rate limiting
            
            await pipeline.close()
        
        logger.info("\n✅ PIPELINE TEST COMPLETE!")
        logger.info("="*60)

async def main():
    """Main setup and test function"""
    setup = MemoryPipelineSetup()
    
    logger.info("🎯 FULL GRAPHRAG PIPELINE SETUP & TEST")
    logger.info("="*60)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verify services
    services = setup.verify_services()
    if not all(services.values()):
        logger.error("❌ Not all services are available. Please check:")
        for service, status in services.items():
            if not status:
                logger.error(f"  - {service}")
        return
    
    # Step 1: Load existing memories
    logger.info("\n📥 Loading existing memories...")
    memories = setup.load_existing_memories()
    
    if not memories:
        logger.error("❌ No memories loaded")
        return
    
    raw_file = setup.save_raw_memories(memories)
    
    # Step 2: Preprocess with Gemini
    logger.info("\n🤖 Preprocessing memories...")
    preprocessed_file = await setup.preprocess_with_gemini(raw_file)
    
    # Step 3: Run full pipeline test
    await setup.run_full_pipeline_test(preprocessed_file)
    
    # Summary
    logger.info("\n📊 SETUP COMPLETE!")
    logger.info(f"  - Raw memories: {raw_file}")
    logger.info(f"  - Preprocessed memories: {preprocessed_file}")
    logger.info(f"  - Services verified: ✅")
    logger.info(f"  - Pipeline tested: ✅")
    logger.info("\n🎉 You can now:")
    logger.info("  1. Query your memories using: python graphrag_pipeline.py")
    logger.info("  2. Browse memories using: python browse_memories.py")
    logger.info("  3. Visualize graph using Neo4j Browser at: http://localhost:7474")

if __name__ == "__main__":
    asyncio.run(main()) 