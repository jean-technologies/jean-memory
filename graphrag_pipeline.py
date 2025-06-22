#!/usr/bin/env python3
"""
GraphRAG Pipeline - Research-Backed Implementation

This implements the complete GraphRAG pipeline based on:
- KG²RAG: Knowledge Graph-Guided Retrieval Augmented Generation
- HippoRAG: Neurobiologically Inspired Long-Term Memory

Pipeline Steps:
1. Query Preprocessing & Decomposition (Conscious Mind)
2. Initial Retrieval - Semantic Search (Qdrant)
3. Contextual Expansion - Graph Traversal (Neo4j)
4. Synthesis & Fusion (Memory Weaver)
5. Final Response Generation
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GraphRAGPipeline:
    """Complete GraphRAG implementation with vector + graph fusion"""
    
    def __init__(self):
        self.qdrant_client = None
        self.neo4j_driver = None
        self.openai_client = None
        self.gemini_client = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize all clients and connections"""
        try:
            from qdrant_client import QdrantClient
            from neo4j import GraphDatabase
            from openai import OpenAI
            import google.generativeai as genai
            from dotenv import load_dotenv
            
            load_dotenv()
            
            # Initialize Qdrant
            self.qdrant_client = QdrantClient(host="localhost", port=6333)
            logger.info("✅ Qdrant client initialized")
            
            # Initialize Neo4j
            self.neo4j_driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
            )
            logger.info("✅ Neo4j driver initialized")
            
            # Initialize OpenAI
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            logger.info("✅ OpenAI client initialized")
            
            # Initialize Gemini
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
            logger.info("✅ Gemini client initialized")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def process_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        Main GraphRAG pipeline entry point
        
        Args:
            query: User's natural language query
            user_id: User identifier for filtering
            
        Returns:
            Complete response with context and answer
        """
        if not self.initialized:
            return {"error": "Pipeline not initialized"}
        
        logger.info(f"🎯 Processing query: '{query}'")
        
        # Step 1: Query Preprocessing & Decomposition
        decomposition = await self._decompose_query(query)
        
        # Step 2: Initial Retrieval - Semantic Search
        seed_memories = await self._semantic_search(
            decomposition['semantic_query'], 
            user_id,
            limit=10
        )
        
        # Step 3: Contextual Expansion - Graph Traversal
        expanded_context = await self._expand_graph_context(
            decomposition['entity_anchors'],
            seed_memories,
            user_id
        )
        
        # Step 4: Synthesis & Fusion
        synthesized_context = await self._synthesize_context(
            query,
            seed_memories,
            expanded_context,
            decomposition
        )
        
        # Step 5: Final Response Generation
        final_response = await self._generate_response(
            query,
            synthesized_context
        )
        
        return {
            "query": query,
            "decomposition": decomposition,
            "seed_memories": len(seed_memories),
            "graph_nodes": len(expanded_context.get('nodes', [])),
            "graph_relationships": len(expanded_context.get('relationships', [])),
            "synthesized_context": synthesized_context,
            "response": final_response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _decompose_query(self, query: str) -> Dict[str, Any]:
        """
        Step 1: Query Preprocessing & Decomposition
        Use Gemini to extract entities and semantic intent
        """
        logger.info("📝 Step 1: Query Decomposition")
        
        prompt = f"""
Analyze this query and extract key components for a memory search system:

Query: "{query}"

Extract:
1. Entity Anchors - Key people, places, projects, or concepts mentioned
2. Temporal Context - Any time references or periods
3. Core Semantic Intent - What information is being sought
4. Query Type - factual, relationship, temporal, or analytical

Return as JSON:
{{
  "entity_anchors": [
    {{"type": "Person|Place|Project|Concept", "name": "entity name", "confidence": 0.0-1.0}}
  ],
  "temporal_context": {{
    "explicit_dates": ["any dates mentioned"],
    "relative_time": "past|present|future|specific period",
    "time_keywords": ["temporal keywords"]
  }},
  "semantic_query": "reformulated query focusing on core intent",
  "query_type": "factual|relationship|temporal|analytical",
  "original_query": "{query}"
}}
"""
        
        try:
            response = self.gemini_client.generate_content(prompt)
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            
            logger.info(f"  ✅ Extracted {len(result.get('entity_anchors', []))} entities")
            logger.info(f"  ✅ Query type: {result.get('query_type', 'unknown')}")
            
            return result
            
        except Exception as e:
            logger.error(f"  ❌ Decomposition failed: {e}")
            return {
                "entity_anchors": [],
                "temporal_context": {},
                "semantic_query": query,
                "query_type": "unknown",
                "original_query": query
            }
    
    async def _semantic_search(self, query: str, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Step 2: Initial Retrieval - Semantic Search
        Find seed memories using vector similarity
        """
        logger.info("🔍 Step 2: Semantic Search")
        
        try:
            # Generate query embedding
            embedding_response = self.openai_client.embeddings.create(
                input=query,
                model="text-embedding-3-small"
            )
            query_embedding = embedding_response.data[0].embedding
            
            # Search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name="enhanced_memories_openai",
                query_vector=query_embedding,
                limit=limit,
                query_filter={
                    "must": [
                        {"key": "user_id", "match": {"value": user_id}}
                    ]
                }
            )
            
            # Format results
            memories = []
            for result in search_results:
                memories.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "temporal_context": result.payload.get("temporal_context", ""),
                    "confidence": result.payload.get("confidence", ""),
                    "metadata": result.payload
                })
            
            logger.info(f"  ✅ Found {len(memories)} seed memories")
            return memories
            
        except Exception as e:
            logger.error(f"  ❌ Semantic search failed: {e}")
            return []
    
    async def _expand_graph_context(
        self, 
        entity_anchors: List[Dict],
        seed_memories: List[Dict],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Step 3: Contextual Expansion - Graph Traversal
        Expand context using Neo4j relationships
        """
        logger.info("🕸️ Step 3: Graph Context Expansion")
        
        expanded_context = {
            "nodes": [],
            "relationships": [],
            "subgraphs": []
        }
        
        with self.neo4j_driver.session() as session:
            try:
                # Extract entities from seed memories
                memory_entities = set()
                for memory in seed_memories:
                    # Simple entity extraction from memory text
                    # In production, use NER or more sophisticated extraction
                    words = memory['text'].split()
                    for word in words:
                        if word[0].isupper() and len(word) > 2:
                            memory_entities.add(word)
                
                # Combine with query entities
                all_entities = [anchor['name'] for anchor in entity_anchors]
                all_entities.extend(list(memory_entities)[:10])  # Limit to avoid explosion
                
                if not all_entities:
                    logger.info("  ⚠️ No entities found for expansion")
                    return expanded_context
                
                # Query 1: Find direct relationships between entities
                cypher_direct = """
                MATCH (n:Memory {user_id: $user_id})
                WHERE any(entity IN $entities WHERE n.text CONTAINS entity)
                WITH n
                MATCH (n)-[r]-(m:Memory {user_id: $user_id})
                WHERE any(entity IN $entities WHERE m.text CONTAINS entity)
                RETURN n, r, m
                LIMIT 50
                """
                
                result = session.run(cypher_direct, user_id=user_id, entities=all_entities)
                
                for record in result:
                    if record['n']:
                        expanded_context['nodes'].append({
                            "id": record['n'].element_id,
                            "properties": dict(record['n'])
                        })
                    if record['m']:
                        expanded_context['nodes'].append({
                            "id": record['m'].element_id,
                            "properties": dict(record['m'])
                        })
                    if record['r']:
                        expanded_context['relationships'].append({
                            "type": record['r'].type,
                            "properties": dict(record['r'])
                        })
                
                # Query 2: Find temporal neighbors
                if seed_memories:
                    for memory in seed_memories[:3]:  # Top 3 memories
                        temporal_context = memory.get('temporal_context', '')
                        if temporal_context:
                            cypher_temporal = """
                            MATCH (n:Memory {user_id: $user_id})
                            WHERE n.temporal_context CONTAINS $temporal_keyword
                            RETURN n
                            LIMIT 10
                            """
                            
                            # Extract date from temporal context
                            import re
                            date_match = re.search(r'\d{4}-\d{2}-\d{2}', temporal_context)
                            if date_match:
                                temporal_result = session.run(
                                    cypher_temporal, 
                                    user_id=user_id,
                                    temporal_keyword=date_match.group()
                                )
                                
                                for record in temporal_result:
                                    if record['n']:
                                        expanded_context['nodes'].append({
                                            "id": record['n'].element_id,
                                            "properties": dict(record['n']),
                                            "temporal_neighbor": True
                                        })
                
                # Deduplicate nodes
                seen_ids = set()
                unique_nodes = []
                for node in expanded_context['nodes']:
                    if node['id'] not in seen_ids:
                        seen_ids.add(node['id'])
                        unique_nodes.append(node)
                expanded_context['nodes'] = unique_nodes
                
                logger.info(f"  ✅ Expanded to {len(expanded_context['nodes'])} nodes")
                logger.info(f"  ✅ Found {len(expanded_context['relationships'])} relationships")
                
            except Exception as e:
                logger.error(f"  ❌ Graph expansion failed: {e}")
        
        return expanded_context
    
    async def _synthesize_context(
        self,
        query: str,
        seed_memories: List[Dict],
        expanded_context: Dict[str, Any],
        decomposition: Dict[str, Any]
    ) -> str:
        """
        Step 4: Synthesis & Fusion
        Use Gemini to weave together vector and graph results
        """
        logger.info("🧵 Step 4: Context Synthesis")
        
        # Prepare seed memories text
        seed_text = "\n\n".join([
            f"[Score: {m['score']:.3f}] {m['text']} (Context: {m['temporal_context']})"
            for m in seed_memories[:5]
        ])
        
        # Prepare graph context
        graph_nodes_text = "\n".join([
            f"- {node['properties'].get('text', '')[:100]}... ({node['properties'].get('temporal_context', 'No date')})"
            for node in expanded_context['nodes'][:10]
        ])
        
        graph_relationships = expanded_context['relationships'][:5]
        relationships_text = f"Found {len(graph_relationships)} relationships in the memory graph"
        
        synthesis_prompt = f"""
You are synthesizing search results from a personal memory system to answer a query.

Original Query: "{query}"
Query Type: {decomposition.get('query_type', 'unknown')}
Key Entities: {', '.join([e['name'] for e in decomposition.get('entity_anchors', [])])}

SEMANTIC SEARCH RESULTS (Most relevant memories):
{seed_text}

GRAPH CONTEXT (Related memories and connections):
{graph_nodes_text}

{relationships_text}

TASK: Create a coherent, comprehensive context that:
1. Prioritizes information directly answering the query
2. Incorporates temporal relationships and patterns
3. Connects related memories to provide complete picture
4. Maintains chronological clarity when relevant
5. Highlights key entities and their relationships

Synthesize these results into a single, well-structured context that directly addresses the user's question.
Focus on creating a narrative that connects the dots between different memories.
"""
        
        try:
            response = self.gemini_client.generate_content(synthesis_prompt)
            synthesized = response.text.strip()
            
            logger.info(f"  ✅ Synthesized {len(synthesized)} characters of context")
            return synthesized
            
        except Exception as e:
            logger.error(f"  ❌ Synthesis failed: {e}")
            # Fallback to simple concatenation
            return f"Relevant memories:\n{seed_text}"
    
    async def _generate_response(self, query: str, context: str) -> str:
        """
        Step 5: Final Response Generation
        Use Gemini to generate the final answer
        """
        logger.info("💬 Step 5: Response Generation")
        
        response_prompt = f"""
Based on the following context from a personal memory system, answer the user's question.

Context:
{context}

Question: {query}

Instructions:
- Answer directly and specifically based on the provided context
- If the context doesn't contain enough information, acknowledge what is known and what is missing
- Be precise with dates, names, and relationships
- Maintain a helpful, conversational tone
- If there are patterns or insights across multiple memories, highlight them

Answer:
"""
        
        try:
            response = self.gemini_client.generate_content(response_prompt)
            answer = response.text.strip()
            
            logger.info(f"  ✅ Generated {len(answer)} character response")
            return answer
            
        except Exception as e:
            logger.error(f"  ❌ Response generation failed: {e}")
            return "I encountered an error generating the response. Please try again."

# Interactive CLI for testing
async def interactive_graphrag_session():
    """Interactive GraphRAG query session"""
    pipeline = GraphRAGPipeline()
    
    logger.info("🚀 Initializing GraphRAG Pipeline...")
    if not await pipeline.initialize():
        logger.error("Failed to initialize pipeline")
        return
    
    logger.info("\n🎯 GRAPHRAG PIPELINE READY!")
    logger.info("This implements the full research-backed GraphRAG approach:")
    logger.info("  1. Query Decomposition (Entity + Intent extraction)")
    logger.info("  2. Vector Search (Semantic similarity)")
    logger.info("  3. Graph Expansion (Relationship traversal)")
    logger.info("  4. Context Synthesis (Fusion of results)")
    logger.info("  5. Response Generation (Final answer)")
    
    print("\nExample queries to try:")
    print("  - 'What were my main fitness activities in June 2025?'")
    print("  - 'How has my workout routine evolved over time?'")
    print("  - 'What connections exist between my work projects and fitness goals?'")
    print("  - 'Tell me about my experiences in San Francisco'")
    
    user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"  # Your user ID
    
    while True:
        try:
            query = input("\n🔍 Enter your query (or 'quit'): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Process query through full pipeline
            print("\n⏳ Processing through GraphRAG pipeline...")
            result = await pipeline.process_query(query, user_id)
            
            if "error" in result:
                print(f"\n❌ Error: {result['error']}")
            else:
                print(f"\n📊 PIPELINE RESULTS:")
                print(f"  - Query Type: {result['decomposition'].get('query_type', 'unknown')}")
                print(f"  - Entities Found: {len(result['decomposition'].get('entity_anchors', []))}")
                print(f"  - Seed Memories: {result['seed_memories']}")
                print(f"  - Graph Nodes: {result['graph_nodes']}")
                print(f"  - Relationships: {result['graph_relationships']}")
                
                print(f"\n💡 ANSWER:")
                print(result['response'])
                
                # Optional: Show decomposition details
                show_details = input("\nShow detailed decomposition? (y/n): ").lower()
                if show_details == 'y':
                    print(f"\n🔍 DECOMPOSITION:")
                    print(json.dumps(result['decomposition'], indent=2))
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("\n👋 GraphRAG session ended!")

# Batch processing for evaluation
async def evaluate_graphrag_pipeline():
    """Run evaluation queries through the pipeline"""
    pipeline = GraphRAGPipeline()
    
    if not await pipeline.initialize():
        return
    
    test_queries = [
        {
            "query": "What fitness activities have I done recently?",
            "expected_entities": ["fitness", "gym", "workout"]
        },
        {
            "query": "Tell me about my experiences with Barry's Bootcamp",
            "expected_entities": ["Barry's Bootcamp", "trainer", "bootcamp"]
        },
        {
            "query": "What happened in San Francisco in July 2024?",
            "expected_entities": ["San Francisco", "July", "fireworks"]
        },
        {
            "query": "How do I organize my work setup?",
            "expected_entities": ["desk", "monitor", "Suptek"]
        }
    ]
    
    user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
    
    logger.info("📊 EVALUATING GRAPHRAG PIPELINE")
    logger.info("="*60)
    
    for i, test in enumerate(test_queries, 1):
        logger.info(f"\n🧪 Test {i}: {test['query']}")
        
        result = await pipeline.process_query(test['query'], user_id)
        
        if "error" not in result:
            # Check entity extraction
            found_entities = [e['name'].lower() for e in result['decomposition'].get('entity_anchors', [])]
            expected_found = sum(1 for exp in test['expected_entities'] if any(exp in ent for ent in found_entities))
            
            logger.info(f"  ✅ Entity extraction: {expected_found}/{len(test['expected_entities'])}")
            logger.info(f"  ✅ Seeds found: {result['seed_memories']}")
            logger.info(f"  ✅ Graph expanded: {result['graph_nodes']} nodes")
            logger.info(f"  📝 Response preview: {result['response'][:100]}...")
        else:
            logger.error(f"  ❌ Pipeline failed: {result['error']}")
    
    logger.info("\n✅ Evaluation complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='GraphRAG Pipeline')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run interactive session')
    parser.add_argument('--evaluate', '-e', action='store_true', help='Run evaluation queries')
    
    args = parser.parse_args()
    
    if args.evaluate:
        asyncio.run(evaluate_graphrag_pipeline())
    else:
        # Default to interactive
        asyncio.run(interactive_graphrag_session()) 