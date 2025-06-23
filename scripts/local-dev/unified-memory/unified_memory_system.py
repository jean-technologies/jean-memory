import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from logging import INFO
from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
# from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF # Not used in basic search

from mem0 import Memory # type: ignore

# Configure logging
logging.basicConfig(
    level=INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# --- Configuration from Environment Variables ---
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://neo4j_db:7687')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD')

MEM0_GRAPH_STORE_URL = os.environ.get('MEM0_GRAPH_STORE_URL', NEO4J_URI) # Use same Neo4j by default
MEM0_GRAPH_STORE_USERNAME = os.environ.get('MEM0_GRAPH_STORE_USERNAME', NEO4J_USER)
MEM0_GRAPH_STORE_PASSWORD = os.environ.get('MEM0_GRAPH_STORE_PASSWORD', NEO4J_PASSWORD)

# Qdrant defaults (if not specified in Mem0 config, it uses localhost:6333)
QDRANT_HOST = os.environ.get('QDRANT_HOST', 'qdrant_db')
QDRANT_PORT = int(os.environ.get('QDRANT_PORT', 6333))


class UnifiedMemorySystem:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError('OPENAI_API_KEY must be set')
        if not NEO4J_PASSWORD:
            logger.warning('NEO4J_PASSWORD is not set. This might cause connection issues.')
        if not MEM0_GRAPH_STORE_PASSWORD:
            logger.warning('MEM0_GRAPH_STORE_PASSWORD is not set for Mem0 Neo4j graph store.')

        logger.info(f"Initializing Graphiti with Neo4j URI: {NEO4J_URI}")
        self.graphiti = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

        mem0_config_dict = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": QDRANT_HOST,
                    "port": QDRANT_PORT,
                }
            },
            "graph_store": {
                "provider": "neo4j",
                "config": {
                    "url": MEM0_GRAPH_STORE_URL,
                    "username": MEM0_GRAPH_STORE_USERNAME,
                    "password": MEM0_GRAPH_STORE_PASSWORD,
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": OPENAI_API_KEY,
                    "model": "gpt-4o" # User updated, Mem0 needs an LLM
                }
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "api_key": OPENAI_API_KEY,
                    "model": "text-embedding-3-small"
                }
            },
            "history_db_path": "/tmp/mem0_history.db", # Path for Mem0's history DB (e.g., SQLite)
            "custom_fact_extraction_prompt": None, # Optional: Custom prompt for fact extraction
            "custom_update_memory_prompt": None,   # Optional: Custom prompt for memory updates
            # "version": "v0.1" # Optional: Mem0Config has a default version if not specified
        }

        logger.info("Initializing Mem0 with config dict using Memory.from_config(): %s", mem0_config_dict)
        # Use the from_config class method as per Mem0 examples
        self.mem0 = Memory.from_config(mem0_config_dict)
        self.is_graphiti_initialized = False

    async def async_init(self):
        """Perform asynchronous initializations."""
        try:
            logger.info("Building Graphiti indices and constraints...")
            await self.graphiti.build_indices_and_constraints()
            self.is_graphiti_initialized = True
            logger.info("Graphiti initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Graphiti: {e}")
            # Depending on the error, you might want to raise it or handle it

    async def add_memory(self, content: str, user_id: str, metadata: dict = None):
        if not self.is_graphiti_initialized:
            logger.warning("Graphiti not initialized. Skipping Graphiti add_episode.")
            # Alternatively, await self.async_init() here if it's safe to do so
        else:
            try:
                episode_name = f"{user_id}_memory_{datetime.now(timezone.utc).isoformat()}"
                logger.info(f"Adding to Graphiti: '{content[:50]}...' as episode '{episode_name}'")
                await self.graphiti.add_episode(
                    name=episode_name,
                    episode_body=content,
                    source=EpisodeType.text,
                    source_description=metadata.get("source_description", "Unified Memory System Entry"),
                    reference_time=datetime.now(timezone.utc),
                )
                logger.info(f"Added episode to Graphiti: {episode_name}")
            except Exception as e:
                logger.error(f"Error adding episode to Graphiti: {e}")

        try:
            logger.info(f"Adding to Mem0: '{content[:50]}...' for user_id '{user_id}'")
            # Mem0's add method is synchronous. Run in executor if in async context.
            loop = asyncio.get_event_loop()
            mem0_messages = [{"role": "user", "content": content}]
            # Mem0's add method returns a list of memory IDs or a dict with info.
            # Let's assume it's a dict for now based on some examples.
            result = await loop.run_in_executor(
                None, lambda: self.mem0.add(mem0_messages, user_id=user_id, metadata=metadata)
            )
            logger.info(f"Added memory to Mem0 for user {user_id}. Result: {result}")
        except Exception as e:
            logger.error(f"Error adding memory to Mem0: {e}")

    async def search_memory(self, query: str, user_id: str):
        results = {"graphiti_results": [], "mem0_results": []}

        if not self.is_graphiti_initialized:
            logger.warning("Graphiti not initialized. Skipping Graphiti search.")
        else:
            try:
                logger.info(f"Searching Graphiti for: '{query}'")
                graphiti_search_results = await self.graphiti.search(query)
                results["graphiti_results"] = [
                    {
                        "fact": r.fact,
                        "uuid": r.uuid,
                        "source_node_uuid": r.source_node_uuid,
                        "target_node_uuid": r.target_node_uuid,
                        "valid_at": r.valid_at.isoformat() if hasattr(r, 'valid_at') and r.valid_at else None,
                        "invalid_at": r.invalid_at.isoformat() if hasattr(r, 'invalid_at') and r.invalid_at else None,
                    }
                    for r in graphiti_search_results
                ]
                logger.info(f"Graphiti search found {len(results['graphiti_results'])} results.")
            except Exception as e:
                logger.error(f"Error searching Graphiti: {e}")

        try:
            logger.info(f"Searching Mem0 for: '{query}' with user_id '{user_id}'")
            # Mem0's search method is synchronous.
            loop = asyncio.get_event_loop()
            mem0_search_results = await loop.run_in_executor(
                None, lambda: self.mem0.search(query, user_id=user_id)
            )
            # Mem0 search results are typically a list of dictionaries (memory objects)
            results["mem0_results"] = mem0_search_results 
            logger.info(f"Mem0 search found {len(results['mem0_results'])} results.")
        except Exception as e:
            logger.error(f"Error searching Mem0: {e}")
        
        return results

    async def close(self):
        logger.info("Closing Graphiti connection...")
        if self.graphiti:
            await self.graphiti.close()
        # Mem0 does not have an explicit close() method in the basic Memory class for its stores.
        # Connections (like Qdrant client, DB connections) are managed internally.
        logger.info("Unified Memory System connections closed (Graphiti explicitly).")

async def main():
    logger.info("Starting Unified Memory System demo...")
    ums = UnifiedMemorySystem()
    
    try:
        await ums.async_init() # Initialize Graphiti indices

        if not ums.is_graphiti_initialized:
            logger.error("Failed to initialize Graphiti. Aborting demo.")
            return

        # Example memories
        user_alice = "alice"
        user_bob = "bob"

        await ums.add_memory(
            content="Alice enjoys learning about space exploration and black holes.",
            user_id=user_alice,
            metadata={"category": "hobbies", "source_description": "User profile update"}
        )
        await asyncio.sleep(1) # Small delay for processing if needed

        await ums.add_memory(
            content="Bob is planning a trip to Paris next summer.",
            user_id=user_bob,
            metadata={"category": "travel_plans"}
        )
        await asyncio.sleep(1)

        await ums.add_memory(
            content="Alice also likes to read science fiction novels, especially by Arthur C. Clarke.",
            user_id=user_alice,
            metadata={"category": "hobbies"}
        )
        await asyncio.sleep(1)

        # Example searches
        logger.info("\n--- Searching for Alice's hobbies ---")
        alice_hobbies_results = await ums.search_memory(query="What are Alice's hobbies?", user_id=user_alice)
        print(json.dumps(alice_hobbies_results, indent=2))

        logger.info("\n--- Searching for Bob's travel plans ---")
        bob_travel_results = await ums.search_memory(query="Where is Bob planning to travel?", user_id=user_bob)
        print(json.dumps(bob_travel_results, indent=2))
        
        logger.info("\n--- Generic search for 'Paris' (Bob's context) ---")
        paris_results_bob = await ums.search_memory(query="Paris", user_id=user_bob)
        print(json.dumps(paris_results_bob, indent=2))

    except Exception as e:
        logger.error(f"An error occurred in the main execution: {e}", exc_info=True)
    finally:
        await ums.close()
        logger.info("\nUnified Memory System demo finished.")

if __name__ == '__main__':
    # Ensure OPENAI_API_KEY is set before running
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please create a .env file with your OpenAI API key or set it in your environment.")
    else:
        asyncio.run(main())
