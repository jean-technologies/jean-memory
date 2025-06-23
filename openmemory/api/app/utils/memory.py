import os
from mem0 import Memory
from app.settings import config  # Import the application config
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_memory_client(custom_instructions: str = None):
    """
    Initializes and returns a Mem0 client configured for the correct environment.
    This function now uses the centralized 'config' object from settings.py.
    
    NOTE: This function does not support user-specific routing.
    For user-specific routing (including test user routing), use get_memory_client_for_user().
    """
    collection_name = None  # Initialize for robust error logging
    try:
        collection_name = config.QDRANT_COLLECTION_NAME
        if not collection_name:
            raise ValueError("MAIN_QDRANT_COLLECTION_NAME must be set via config.")

        qdrant_config = {
            "collection_name": collection_name,
        }

        if config.is_local_development:
            qdrant_config["host"] = config.QDRANT_HOST
            qdrant_config["port"] = config.QDRANT_PORT
        elif config.QDRANT_HOST and "cloud.qdrant.io" in config.QDRANT_HOST:
            qdrant_config["url"] = config.qdrant_url
            if config.QDRANT_API_KEY:
                qdrant_config["api_key"] = config.QDRANT_API_KEY
        else:
            qdrant_config["host"] = config.QDRANT_HOST
            qdrant_config["port"] = config.QDRANT_PORT
            if config.QDRANT_API_KEY:
                qdrant_config["api_key"] = config.QDRANT_API_KEY
        
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment variables.")
        
        mem0_config = {
            "vector_store": {"provider": "qdrant", "config": qdrant_config},
            "llm": {
                "provider": config.LLM_PROVIDER,
                "config": {"model": config.OPENAI_MODEL, "api_key": config.OPENAI_API_KEY},
            },
            "embedder": {
                "provider": config.EMBEDDER_PROVIDER,
                "config": {"model": config.EMBEDDER_MODEL, "api_key": config.OPENAI_API_KEY},
            },
            "version": "v1.1"
        }
        
        # Legacy unified memory check (for backward compatibility)
        if should_use_unified_memory():
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            neo4j_user = os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = os.getenv("NEO4J_PASSWORD", "fasho93fasho")
            
            mem0_config["graph_store"] = {
                "provider": "neo4j",
                "config": {
                    "url": neo4j_uri,
                    "username": neo4j_user,
                    "password": neo4j_password
                }
            }
            print(f"INFO: Enabled Mem0 Graph Memory with Neo4j at {neo4j_uri}")

        memory_instance = Memory.from_config(config_dict=mem0_config)

    except Exception as e:
        collection_str = f"'{collection_name}'" if collection_name else "Not Available"
        print(f"ERROR: Error initializing memory client with collection {collection_str}: {e}")
        raise Exception(f"Could not initialize memory client: {e}")
            
    return memory_instance


def get_memory_client_for_user(user_id: str, custom_instructions: str = None):
    """
    Get the appropriate memory client for a specific user.
    This function handles user-specific routing including test user routing.
    
    Args:
        user_id: The user ID to determine routing for
        custom_instructions: Optional custom instructions (not used currently)
    
    Returns:
        Memory client (either old Qdrant system or new unified system)
    """
    try:
        # Import here to avoid circular imports
        from app.utils.unified_memory import should_use_unified_memory, get_unified_memory_client
        
        # Check if this user should use the new unified memory system
        if should_use_unified_memory(user_id):
            logger.info(f"🧪 Routing user {user_id[:8]}... to NEW unified memory system")
            # Return the unified memory client configured for new system
            return get_unified_memory_client(user_id)
        else:
            # Use the old Qdrant-based system
            logger.debug(f"📦 Routing user {user_id[:8]}... to OLD Qdrant system")
            return get_memory_client(custom_instructions)
            
    except ImportError as e:
        logger.warning(f"Unified memory system not available: {e}. Falling back to standard client.")
        return get_memory_client(custom_instructions)
    except Exception as e:
        logger.error(f"Error in user-specific memory client routing: {e}")
        # Fallback to standard client for safety
        return get_memory_client(custom_instructions)


async def get_enhanced_memory_client():
    """
    Get the appropriate memory client based on configuration.
    This function is now async to properly initialize the unified client.
    
    NOTE: This function does not support user-specific routing.
    For user-specific routing, use get_memory_client_for_user().
    
    Returns:
        - UnifiedMemorySystem if unified memory is enabled
        - Standard Mem0 client otherwise
    """
    if should_use_unified_memory():
        try:
            # Import the async client factory from the unified memory module
            from app.utils.unified_memory import get_enhanced_memory_client as get_unified_client
            return await get_unified_client()
        except ImportError as e:
            print(f"WARNING: Unified memory not available: {e}. Falling back to standard Mem0 client.")
            # Fallback to a sync-created standard client
            return get_memory_client()
    else:
        # Production or when unified memory is disabled
        return get_memory_client()


def should_use_unified_memory() -> bool:
    """
    Determine if unified memory features should be used (legacy function).
    
    NOTE: This function does not support user-specific routing.
    For user-specific routing, use should_use_unified_memory(user_id) from unified_memory.py.
    
    Returns:
        True if unified memory should be used, False otherwise
    """
    return (
        config.is_local_development and 
        os.getenv("USE_UNIFIED_MEMORY", "false").lower() == "true"
    )
