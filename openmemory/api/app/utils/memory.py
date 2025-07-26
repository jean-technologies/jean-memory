import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Calculate project root more explicitly
# Current file path: /path/to/your-memory/openmemory/api/app/utils/memory.py
# Project root path: /path/to/your-memory/
current_dir = Path(__file__).parent.resolve()  # app/utils/
api_dir = current_dir.parent.parent  # openmemory/api/
openmemory_dir = api_dir.parent  # openmemory/
project_root = openmemory_dir.parent  # your-memory/

# Add project root to Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from jean_memory.mem0_adapter_optimized import get_memory_client_v2_optimized
from app.settings import config  # Import the application config


def get_memory_client(custom_instructions: str = None):
    """
    Initializes and returns a Jean Memory V2 client with mem0 compatibility.
    Provides enhanced multi-source memory (mem0 + Graphiti) while maintaining 100% API compatibility.
    """
    try:
        # Jean Memory V2 handles all configuration internally using environment variables
        # It automatically configures both mem0 (Qdrant) and Graphiti (Neo4j) backends
        
        # Verify required environment variables are set
        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # For local development (localhost), QDRANT_API_KEY is optional
        # For cloud deployment, QDRANT_API_KEY is required
        required_vars = ["QDRANT_HOST", "OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        # Check if QDRANT_API_KEY is required (cloud deployment)
        if qdrant_host and qdrant_host != "localhost" and not qdrant_api_key:
            missing_vars.append("QDRANT_API_KEY")
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables for Jean Memory V2: {missing_vars}")
        
        # Optional: Check for Neo4j variables (used by Graphiti backend)
        neo4j_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
        neo4j_available = all(os.getenv(var) for var in neo4j_vars)
        
        if not neo4j_available:
            logger.warning("Neo4j variables not found - Jean Memory V2 will run in mem0-only mode")
            logger.info("To enable graph memory, set: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        
        # Get Jean Memory V2 OPTIMIZED adapter - provides 100% mem0 API compatibility with 3-5x performance
        # The adapter automatically handles async/sync contexts
        memory_instance = get_memory_client_v2_optimized()
        
        logger.info("Jean Memory V2 initialized successfully - Enhanced multi-source memory ready")
        return memory_instance

    except Exception as e:
        # Enhanced logging
        logger.error(f"Error initializing Jean Memory V2 client: {e}")
        logger.info("Falling back to basic configuration...")
        raise Exception(f"Could not initialize Jean Memory V2 client: {e}")


async def get_async_memory_client(custom_instructions: str = None):
    """
    Initializes and returns an async Jean Memory V2 client with mem0-compatible API.
    This is the async version for use in FastAPI endpoints with comprehensive logging.
    """
    import time
    init_start = time.time()
    
    logger.info(f"🔧 [Memory Client] ===== INITIALIZING ASYNC MEMORY CLIENT =====")
    
    try:
        # Import OPTIMIZED async adapter
        logger.info(f"🔧 [Memory Client] Importing optimized async adapter")
        from jean_memory.mem0_adapter_optimized import get_async_memory_client_v2_optimized
        logger.info(f"🔧 [Memory Client] ✅ Import successful")
        
        # Verify required environment variables are set (same as sync version)
        logger.info(f"🔧 [Memory Client] Checking environment variables")
        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        logger.info(f"🔧 [Memory Client] QDRANT_HOST: {qdrant_host}")
        logger.info(f"🔧 [Memory Client] QDRANT_API_KEY: {'***set***' if qdrant_api_key else 'not set'}")
        logger.info(f"🔧 [Memory Client] OPENAI_API_KEY: {'***set***' if openai_api_key else 'not set'}")
        
        # For local development (localhost), QDRANT_API_KEY is optional
        # For cloud deployment, QDRANT_API_KEY is required
        required_vars = ["QDRANT_HOST", "OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        # Check if QDRANT_API_KEY is required (cloud deployment)
        if qdrant_host and qdrant_host != "localhost" and not qdrant_api_key:
            missing_vars.append("QDRANT_API_KEY")
        
        if missing_vars:
            logger.error(f"🔧 [Memory Client] ❌ Missing environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables for Jean Memory V2: {missing_vars}")
        
        logger.info(f"🔧 [Memory Client] ✅ Required environment variables validated")
        
        # Optional: Check for Neo4j variables (used by Graphiti backend)
        neo4j_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"]
        neo4j_available = all(os.getenv(var) for var in neo4j_vars)
        
        logger.info(f"🔧 [Memory Client] Neo4j check: {neo4j_available}")
        if neo4j_available:
            neo4j_uri = os.getenv("NEO4J_URI")
            logger.info(f"🔧 [Memory Client] NEO4J_URI: {neo4j_uri}")
            logger.info(f"🔧 [Memory Client] NEO4J_USER: {os.getenv('NEO4J_USER')}")
            logger.info(f"🔧 [Memory Client] NEO4J_PASSWORD: {'***set***' if os.getenv('NEO4J_PASSWORD') else 'not set'}")
        else:
            logger.warning(f"🔧 [Memory Client] ⚠️ Neo4j variables not found - Jean Memory V2 will run in mem0-only mode")
            logger.info(f"🔧 [Memory Client] To enable graph memory, set: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        
        # Validate environment variables
        logger.info(f"🔧 [Memory Client] Creating Jean Memory V2 configuration")
        
        # Create config from current environment variables (FIXED: No hardcoded values)
        from jean_memory.config import JeanMemoryConfig
        
        # Get actual environment values - NO HARDCODED FALLBACKS
        neo4j_uri_env = os.getenv("NEO4J_URI")
        neo4j_user_env = os.getenv("NEO4J_USER") 
        neo4j_password_env = os.getenv("NEO4J_PASSWORD")
        
        # Validate critical environment variables
        if not openai_api_key:
            logger.error(f"🔧 [Memory Client] ❌ OPENAI_API_KEY is required but not set")
            raise ValueError("OPENAI_API_KEY is required but not set in environment")
            
        if not qdrant_host:
            logger.error(f"🔧 [Memory Client] ❌ QDRANT_HOST is required but not set")
            raise ValueError("QDRANT_HOST is required but not set in environment")
        
        config_dict = {
            'OPENAI_API_KEY': openai_api_key,  # FIXED: Use actual environment value
            'QDRANT_HOST': qdrant_host,
            'QDRANT_PORT': os.getenv("QDRANT_PORT", "6333"),
            'QDRANT_API_KEY': qdrant_api_key or "",  # Empty string for localhost
            'NEO4J_URI': neo4j_uri_env,  # May be None if not configured
            'NEO4J_USER': neo4j_user_env,  # May be None if not configured
            'NEO4J_PASSWORD': neo4j_password_env,  # May be None if not configured
            'GEMINI_API_KEY': os.getenv("GEMINI_API_KEY") or ""
        }
        
        logger.info(f"🔧 [Memory Client] Configuration dict created with {len(config_dict)} keys")
        logger.info(f"🔧 [Memory Client] Qdrant configured for: {qdrant_host}:{os.getenv('QDRANT_PORT', '6333')}")
        
        # Create config from environment variables (clean config without hardcoded values)
        config_start = time.time()
        config = JeanMemoryConfig.from_dict(config_dict)
        config_time = time.time() - config_start
        logger.info(f"🔧 [Memory Client] ✅ Config created in {config_time:.3f}s")
        
        # Get async Jean Memory V2 OPTIMIZED adapter with explicit config
        logger.info(f"🔧 [Memory Client] Initializing optimized memory adapter")
        adapter_start = time.time()
        memory_instance = get_async_memory_client_v2_optimized(config={'jean_memory_config': config})
        adapter_time = time.time() - adapter_start
        total_time = time.time() - init_start
        
        logger.info(f"🔧 [Memory Client] ✅ Adapter initialized in {adapter_time:.3f}s")
        logger.info(f"🔧 [Memory Client] ===== ASYNC MEMORY CLIENT READY in {total_time:.3f}s =====")
        logger.info(f"🔧 [Memory Client] Enhanced multi-source memory ready (3-5x faster performance)")
        return memory_instance

    except Exception as e:
        total_time = time.time() - init_start
        # Enhanced logging
        logger.error(f"🔧 [Memory Client] ❌ INITIALIZATION FAILED after {total_time:.3f}s: {e}", exc_info=True)
        logger.error(f"🔧 [Memory Client] ❌ Environment check:")
        logger.error(f"🔧 [Memory Client]   - QDRANT_HOST: {os.getenv('QDRANT_HOST')}")
        logger.error(f"🔧 [Memory Client]   - OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
        logger.error(f"🔧 [Memory Client]   - NEO4J_URI: {os.getenv('NEO4J_URI')}")
        raise Exception(f"Could not initialize async Jean Memory V2 client: {e}")
