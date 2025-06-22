#!/usr/bin/env python3
"""
Custom Query Testing Script for R&D Datasets

This script allows you to test custom queries on existing datasets
without re-running the full ingestion pipeline.

Usage:
    python test_custom_queries.py --dataset DATASET_NAME
    python test_custom_queries.py --dataset DATASET_NAME --query "Your custom query"
    python test_custom_queries.py --list-datasets
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class CustomQueryTester:
    """Test custom queries on existing R&D datasets"""
    
    def __init__(self):
        self.mem0_client = None
        self.data_dir = Path("rd_data")
        self.datasets_dir = self.data_dir / "datasets"
        self.metadata_file = self.datasets_dir / "datasets_metadata.json"
        
        # Load dataset metadata
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load datasets metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    async def _init_unified_memory(self):
        """Initialize local unified memory system"""
        try:
            from unified_memory_ingestion import initialize_mem0
            
            # Force local development mode
            os.environ['ENVIRONMENT'] = 'development'
            os.environ['USE_UNIFIED_MEMORY'] = 'true'
            
            # Initialize mem0
            self.mem0_client = await initialize_mem0()
            
            logger.info("✅ Unified memory system initialized locally")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize unified memory: {e}")
            raise
    
    def load_dataset(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Load a dataset by name or ID"""
        # Try to find by exact ID first
        if name_or_id in self.metadata:
            dataset_info = self.metadata[name_or_id]
            dataset_dir = self.datasets_dir / name_or_id
        else:
            # Try to find by name (get most recent)
            matching_datasets = [
                (ds_id, ds_info) for ds_id, ds_info in self.metadata.items() 
                if ds_info.get('name', '').lower() == name_or_id.lower()
            ]
            
            if not matching_datasets:
                logger.error(f"❌ Dataset '{name_or_id}' not found")
                return None
            
            # Get most recent dataset with this name
            dataset_id, dataset_info = max(matching_datasets, key=lambda x: x[1].get('created_at', ''))
            dataset_dir = self.datasets_dir / dataset_id
        
        # Load memories
        memories_file = dataset_dir / "memories.json"
        if not memories_file.exists():
            logger.error(f"❌ Memories file not found for dataset '{name_or_id}'")
            return None
        
        with open(memories_file, 'r') as f:
            memories = json.load(f)
        
        return {
            "info": dataset_info,
            "memories": memories,
            "dataset_dir": dataset_dir
        }
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets"""
        datasets = []
        for ds_id, ds_info in self.metadata.items():
            datasets.append({
                "name": ds_info.get('name', 'Unknown'),
                "dataset_id": ds_id,
                "memory_count": ds_info.get('memory_count', 0),
                "user_email": ds_info.get('user_email', 'N/A'),
                "created_at": ds_info.get('created_at', 'N/A'),
                "description": ds_info.get('description', '')
            })
        
        # Sort by creation date (most recent first)
        datasets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return datasets
    
    async def test_query(self, user_id: str, query: str) -> Dict[str, Any]:
        """Test a single query with proper RAG response"""
        try:
            logger.info(f"🔍 Testing query: '{query}'")
            
            if not self.mem0_client:
                await self._init_unified_memory()
            
            start_time = time.time()
            
            # Search using mem0 (includes vector + graph)
            search_results = self.mem0_client.search(
                query=query,
                user_id=user_id,
                limit=10
            )
            
            # Generate RAG response
            response = await self._generate_rag_response(query, search_results)
            
            processing_time = time.time() - start_time
            
            # Extract memories and relations
            memories = search_results.get('results', []) if isinstance(search_results, dict) else []
            relations = search_results.get('relations', []) if isinstance(search_results, dict) else []
            
            result = {
                "query": query,
                "response": response,
                "sources": memories,
                "relations": relations,
                "confidence": 1.0,
                "processing_time": processing_time,
                "memory_count": len(memories)
            }
            
            logger.info(f"✅ Query processed in {processing_time:.2f}s")
            logger.info(f"📊 Found {len(memories)} relevant memories")
            logger.info(f"💬 Response length: {len(response)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return {
                "query": query,
                "error": str(e),
                "processing_time": 0,
                "memory_count": 0
            }
    
    async def _generate_rag_response(self, query: str, search_results: Dict) -> str:
        """Generate RAG response using retrieved memories"""
        try:
            # Extract memories from search results
            memories = search_results.get('results', []) if isinstance(search_results, dict) else []
            relations = search_results.get('relations', []) if isinstance(search_results, dict) else []
            
            if not memories:
                return "No relevant memories found for this query."
            
            # Build context from memories
            context_parts = []
            for memory in memories[:5]:  # Use top 5 memories
                content = memory.get('memory', '') or memory.get('text', '') or memory.get('content', '')
                if content:
                    context_parts.append(content)
            
            context = "\n".join(context_parts)
            
            # Add relationship information if available
            if relations:
                relationship_context = "\nRelated connections: " + ", ".join([
                    f"{rel.get('source', '')} {rel.get('relationship', '')} {rel.get('destination', '')}"
                    for rel in relations[:3]
                ])
                context += relationship_context
            
            # Generate response using OpenAI
            from openai import OpenAI
            client = OpenAI()
            
            prompt = f"""Based on the following memories and context, provide a helpful and contextual response to the user's query.

Query: {query}

Relevant memories:
{context}

Instructions:
- Provide a natural, conversational response
- Use specific details from the memories when relevant
- If the memories don't contain relevant information, say so clearly
- Keep the response focused and helpful
- Don't make up information not present in the memories

Response:"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Failed to generate RAG response: {e}")
            return f"Error generating response: {str(e)}"
    
    async def test_multiple_queries(self, user_id: str, queries: List[str]) -> Dict[str, Any]:
        """Test multiple queries and return results"""
        results = {}
        
        print(f"\n🔍 Testing {len(queries)} queries...")
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Testing: '{query}'")
            result = await self.test_query(user_id, query)
            results[query] = result
            
            # Show brief result
            if 'error' in result:
                print(f"   ❌ Error: {result['error']}")
            else:
                print(f"   ✅ {result['memory_count']} sources, {len(result['response'])} chars")
                print(f"   📝 Preview: {result['response'][:100]}...")
        
        return results
    
    async def interactive_query_session(self, dataset_name: str):
        """Interactive session for testing queries"""
        # Load dataset
        dataset_data = self.load_dataset(dataset_name)
        if not dataset_data:
            return
        
        user_id = dataset_data["info"]["user_id"]
        dataset_info = dataset_data["info"]
        
        print(f"\n🎯 Interactive Query Session")
        print(f"📁 Dataset: {dataset_info['name']}")
        print(f"👤 User: {dataset_info.get('user_email', 'N/A')}")
        print(f"📊 Memories: {dataset_info['memory_count']}")
        print(f"📅 Created: {dataset_info['created_at'][:10]}")
        
        print(f"\n💡 Sample content preview:")
        for i, content in enumerate(dataset_info.get('content_analysis', {}).get('sample_content', [])[:3], 1):
            print(f"   {i}. {content}")
        
        print(f"\n🔍 Enter your queries (type 'exit' to finish, 'help' for examples):")
        
        all_results = {}
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'help':
                    print("\n💡 Example queries based on this dataset:")
                    print("   • What projects am I working on?")
                    print("   • Tell me about my launch strategy")
                    print("   • What are my pricing decisions?")
                    print("   • How do I handle marketing?")
                    print("   • What's my timeline for the project?")
                    continue
                elif not query:
                    continue
                
                # Test the query
                result = await self.test_query(user_id, query)
                all_results[query] = result
                
                if 'error' in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"\n📝 Response:")
                    print(f"{result['response']}")
                    print(f"\n📊 Stats: {result['memory_count']} sources, {result['processing_time']:.2f}s")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session ended by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Save results if any
        if all_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.data_dir / f"custom_queries_{dataset_info['name']}_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")
        
        print(f"\n🎉 Interactive session complete!")

async def main():
    parser = argparse.ArgumentParser(description="Test custom queries on R&D datasets")
    parser.add_argument("--dataset", help="Dataset name or ID to test")
    parser.add_argument("--query", help="Single query to test")
    parser.add_argument("--queries-file", help="File containing queries (one per line)")
    parser.add_argument("--list-datasets", action="store_true", help="List available datasets")
    parser.add_argument("--interactive", action="store_true", help="Interactive query session")
    
    args = parser.parse_args()
    
    tester = CustomQueryTester()
    
    if args.list_datasets:
        datasets = tester.list_datasets()
        print(f"\n📋 Available Datasets ({len(datasets)}):")
        for dataset in datasets:
            print(f"   📁 {dataset['name']}")
            print(f"      ID: {dataset['dataset_id'][:20]}...")
            print(f"      Memories: {dataset['memory_count']}")
            print(f"      User: {dataset['user_email']}")
            print(f"      Created: {dataset['created_at'][:10]}")
            if dataset.get('description'):
                print(f"      Description: {dataset['description']}")
            print()
    
    elif args.dataset:
        # Load dataset
        dataset_data = tester.load_dataset(args.dataset)
        if not dataset_data:
            return
        
        user_id = dataset_data["info"]["user_id"]
        
        if args.interactive or (not args.query and not args.queries_file):
            # Interactive mode
            await tester.interactive_query_session(args.dataset)
        
        elif args.query:
            # Single query
            print(f"\n🔍 Testing single query on dataset '{args.dataset}'")
            result = await tester.test_query(user_id, args.query)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n📝 Query: {args.query}")
                print(f"📝 Response: {result['response']}")
                print(f"📊 Sources: {result['memory_count']}")
                print(f"⏱️  Time: {result['processing_time']:.2f}s")
        
        elif args.queries_file:
            # Multiple queries from file
            queries_file = Path(args.queries_file)
            if not queries_file.exists():
                print(f"❌ Queries file not found: {args.queries_file}")
                return
            
            with open(queries_file, 'r') as f:
                queries = [line.strip() for line in f if line.strip()]
            
            print(f"\n🔍 Testing {len(queries)} queries from {args.queries_file}")
            results = await tester.test_multiple_queries(user_id, queries)
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = tester.data_dir / f"custom_queries_{args.dataset}_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"\n💾 Results saved to: {results_file}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main()) 