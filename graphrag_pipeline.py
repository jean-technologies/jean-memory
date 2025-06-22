#!/usr/bin/env python3
"""
GraphRAG Pipeline Implementation
Combines vector search (Qdrant) with graph traversal (Neo4j) 
Following KG²RAG and HippoRAG research patterns
Now integrated with unified memory system (mem0 + Graphiti)
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import asyncio

# Core dependencies
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from neo4j import GraphDatabase
import google.generativeai as genai
import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure APIs
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
openai.api_key = os.getenv('OPENAI_API_KEY')

@dataclass
class GraphRAGQuery:
    """Query structure for GraphRAG pipeline"""
    query: str
    entities: List[str]
    temporal_context: Optional[str]
    semantic_intent: str
    confidence: float

@dataclass
class GraphRAGResult:
    """Result structure from GraphRAG pipeline"""
    answer: str
    supporting_memories: List[Dict]
    graph_paths: List[Dict]
    confidence: float
    sources: List[str]

class GraphRAGPipeline:
    def __init__(self):
        # Initialize connections
        self.qdrant = QdrantClient(host="localhost", port=6333)
        self.neo4j_driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", os.getenv("NEO4J_PASSWORD", "your-neo4j-password"))
        )
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Updated to use unified memory collection
        self.collection_name = "unified_memory_mem0"
        self.embedding_model = "text-embedding-3-small"
        
        logger.info("✅ GraphRAG Pipeline initialized with unified memory system")
    
    def close(self):
        """Clean up connections"""
        self.neo4j_driver.close()
    
    async def decompose_query(self, query: str) -> GraphRAGQuery:
        """Step 1: Decompose query into entities, temporal context, and intent"""
        
        prompt = f"""
        Analyze this query and extract structured information:
        Query: "{query}"
        
        Extract:
        1. Named entities (people, places, activities, objects)
        2. Temporal context (time references, ongoing vs past)
        3. Semantic intent (what information is being sought)
        
        Format as JSON:
        {{
            "entities": ["entity1", "entity2"],
            "temporal_context": "description of time context",
            "semantic_intent": "what the user wants to know",
            "confidence": 0.0-1.0
        }}
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            result = json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            
            return GraphRAGQuery(
                query=query,
                entities=result.get('entities', []),
                temporal_context=result.get('temporal_context'),
                semantic_intent=result.get('semantic_intent', query),
                confidence=result.get('confidence', 0.8)
            )
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return GraphRAGQuery(
                query=query,
                entities=[],
                temporal_context=None,
                semantic_intent=query,
                confidence=0.5
            )
    
    async def semantic_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Step 2: Vector search for semantically similar memories"""
        
        # Get embedding
        response = openai.embeddings.create(
            model=self.embedding_model,
            input=query
        )
        query_vector = response.data[0].embedding
        
        # Search in Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=True
        )
        
        memories = []
        for hit in results:
            memory = {
                'id': hit.id,
                'text': hit.payload.get('data', hit.payload.get('text', '')),  # mem0 uses 'data' field
                'score': hit.score,
                'temporal_context': hit.payload.get('temporal_context', ''),
                'confidence': hit.payload.get('confidence', 'medium'),
                'metadata': hit.payload
            }
            memories.append(memory)
        
        logger.info(f"📊 Found {len(memories)} semantically similar memories")
        return memories
    
    async def graph_expansion(self, seed_memories: List[Dict], entities: List[str]) -> List[Dict]:
        """Step 3: Expand from seed memories using graph traversal"""
        
        expanded_paths = []
        
        with self.neo4j_driver.session() as session:
            # First, find relationships from mem0's graph
            for memory in seed_memories[:5]:  # Limit to top 5 to avoid explosion
                memory_text = memory['text']
                
                # Query for related entities and relationships
                cypher_query = """
                MATCH (m:Memory)-[r:MENTIONS|RELATES_TO]-(e:Entity)
                WHERE m.text CONTAINS $text_fragment
                WITH m, e, r
                MATCH (e)-[r2:RELATES_TO]-(e2:Entity)
                WHERE e2.name IN $entities OR e.name IN $entities
                RETURN DISTINCT 
                    m.text as memory_text,
                    e.name as entity1,
                    type(r) as rel_type,
                    e2.name as entity2,
                    r2.properties as rel_properties
                LIMIT 20
                """
                
                result = session.run(
                    cypher_query,
                    text_fragment=memory_text[:50],
                    entities=entities
                )
                
                for record in result:
                    path = {
                        'source_memory': memory_text,
                        'entity1': record['entity1'],
                        'relation': record['rel_type'],
                        'entity2': record['entity2'],
                        'properties': dict(record['rel_properties']) if record['rel_properties'] else {}
                    }
                    expanded_paths.append(path)
            
            # Also query Graphiti episodes for temporal relationships
            episode_query = """
            MATCH (e:Episodic)-[:MENTIONS]-(entity:Entity)
            WHERE entity.name IN $entities
            RETURN e.content as content, e.created_at as created_at
            LIMIT 10
            """
            
            episode_result = session.run(episode_query, entities=entities)
            
            for record in episode_result:
                expanded_paths.append({
                    'type': 'episode',
                    'content': record['content'],
                    'created_at': record['created_at']
                })
        
        logger.info(f"🔗 Expanded to {len(expanded_paths)} graph connections")
        return expanded_paths
    
    async def find_temporal_neighbors(self, memories: List[Dict], temporal_context: str) -> List[Dict]:
        """Step 4: Find temporally related memories"""
        
        temporal_neighbors = []
        
        # Parse temporal context
        is_ongoing = any(word in temporal_context.lower() for word in ['ongoing', 'current', 'regularly', 'routine'])
        
        for memory in memories:
            mem_temporal = memory.get('temporal_context', '')
            
            # Match similar temporal contexts
            if is_ongoing and 'ongoing' in mem_temporal.lower():
                temporal_neighbors.append(memory)
            elif not is_ongoing and any(word in mem_temporal.lower() for word in ['occurred', 'happened', 'was']):
                temporal_neighbors.append(memory)
        
        logger.info(f"⏰ Found {len(temporal_neighbors)} temporally related memories")
        return temporal_neighbors
    
    async def synthesize_context(self, 
                               query: GraphRAGQuery,
                               semantic_results: List[Dict],
                               graph_paths: List[Dict],
                               temporal_neighbors: List[Dict]) -> str:
        """Step 5: Synthesize all results into coherent context"""
        
        # Combine all sources
        context_parts = []
        
        # Add semantic search results
        context_parts.append("## Relevant Memories:")
        for mem in semantic_results[:5]:
            context_parts.append(f"- {mem['text']} ({mem['temporal_context']})")
        
        # Add graph relationships
        if graph_paths:
            context_parts.append("\n## Related Information from Graph:")
            for path in graph_paths[:10]:
                if path.get('type') == 'episode':
                    context_parts.append(f"- Episode: {path['content'][:100]}...")
                else:
                    context_parts.append(f"- {path['entity1']} {path['relation']} {path['entity2']}")
        
        # Add temporal context
        if temporal_neighbors:
            context_parts.append(f"\n## Temporal Context ({query.temporal_context}):")
            for mem in temporal_neighbors[:5]:
                context_parts.append(f"- {mem['text']}")
        
        return "\n".join(context_parts)
    
    async def generate_answer(self, query: str, context: str) -> GraphRAGResult:
        """Step 6: Generate final answer using Gemini"""
        
        prompt = f"""
        Based on the following context from a personal memory system, answer the query.
        
        Query: {query}
        
        Context:
        {context}
        
        Provide a comprehensive answer that:
        1. Directly addresses the query
        2. Synthesizes information from multiple sources
        3. Maintains temporal accuracy
        4. Acknowledges any uncertainty
        
        Format: Natural, conversational response.
        """
        
        response = self.gemini_model.generate_content(prompt)
        
        return GraphRAGResult(
            answer=response.text,
            supporting_memories=[],  # Would be filled with actual memories used
            graph_paths=[],  # Would be filled with actual paths
            confidence=0.85,
            sources=['mem0', 'graphiti', 'neo4j']
        )
    
    async def query(self, query: str) -> GraphRAGResult:
        """Main pipeline execution"""
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 GraphRAG Query: {query}")
        logger.info(f"{'='*60}")
        
        # Step 1: Decompose query
        decomposed = await self.decompose_query(query)
        logger.info(f"📝 Entities: {decomposed.entities}")
        logger.info(f"⏰ Temporal: {decomposed.temporal_context}")
        
        # Step 2: Semantic search
        semantic_results = await self.semantic_search(query)
        
        # Step 3: Graph expansion
        graph_paths = await self.graph_expansion(semantic_results, decomposed.entities)
        
        # Step 4: Temporal neighbors
        temporal_neighbors = await self.find_temporal_neighbors(
            semantic_results, 
            decomposed.temporal_context or ""
        )
        
        # Step 5: Synthesize context
        context = await self.synthesize_context(
            decomposed,
            semantic_results,
            graph_paths,
            temporal_neighbors
        )
        
        # Step 6: Generate answer
        result = await self.generate_answer(query, context)
        
        # Add metadata
        result.supporting_memories = semantic_results[:5]
        result.graph_paths = graph_paths[:5]
        
        return result

async def test_unified_graphrag():
    """Test the GraphRAG pipeline with unified memory system"""
    
    pipeline = GraphRAGPipeline()
    
    test_queries = [
        "What fitness activities do I do and where?",
        "Tell me about my work with Oracle colleagues",
        "What projects am I working on?",
        "What happened in June 2025?",
        "What are my ongoing routines?"
    ]
    
    for query in test_queries:
        try:
            result = await pipeline.query(query)
            
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")
            print(f"\n📝 Answer:\n{result.answer}")
            print(f"\n🔗 Sources: {', '.join(result.sources)}")
            print(f"🎯 Confidence: {result.confidence:.2f}")
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
    
    pipeline.close()

async def interactive_mode():
    """Interactive query mode"""
    
    pipeline = GraphRAGPipeline()
    
    print("\n🚀 GraphRAG Interactive Mode (Unified Memory System)")
    print("Type 'exit' to quit")
    print("="*60)
    
    while True:
        query = input("\n❓ Your query: ").strip()
        
        if query.lower() == 'exit':
            break
        
        if not query:
            continue
        
        try:
            result = await pipeline.query(query)
            
            print(f"\n📝 Answer:\n{result.answer}")
            
            # Optionally show details
            show_details = input("\n🔍 Show details? (y/n): ").strip().lower()
            if show_details == 'y':
                print("\n📊 Supporting Memories:")
                for mem in result.supporting_memories[:3]:
                    print(f"  - {mem['text'][:100]}... (score: {mem['score']:.3f})")
                
                if result.graph_paths:
                    print("\n🔗 Graph Connections:")
                    for path in result.graph_paths[:3]:
                        print(f"  - {path}")
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
    
    pipeline.close()
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_mode())
    else:
        asyncio.run(test_unified_graphrag()) 