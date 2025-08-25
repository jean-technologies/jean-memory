"""
Jean Memory V2 - Advanced Hybrid Memory System
==============================================

A sophisticated memory system combining:
- Mem0 Graph Memory for semantic understanding
- Graphiti temporal reasoning for time-aware insights  
- Gemini AI synthesis for intelligent responses

Features:
- Hybrid search with AI synthesis
- Advanced ingestion with safety checks
- Comprehensive error handling
- Async/await support
- Enterprise-ready configuration
- V1 compatibility layer
- Database cleaning utilities for testing
- Dynamic Qdrant indexing for optimal performance
- Unified API for all memory operations

Quick Start with New Unified API (Recommended):
    from jean_memory import JeanMemoryAPI
    
    # Initialize API (loads from openmemory/api/.env.test automatically)
    api = JeanMemoryAPI()
    
    # Add memories
    result = await api.add_memory("I love pizza", user_id="alice")
    
    # Search memories
    results = await api.search_memories("food preferences", user_id="alice") 
    
    # Clear memories (with confirmation)
    await api.clear_memories(user_id="alice", confirm=True)

Convenience Functions:
    from jean_memory import add_memory, search_memories, clear_memories
    
    # Direct function calls
    await add_memory("I work at OpenAI", user_id="bob")
    results = await search_memories("job", user_id="bob")
    await clear_memories(user_id="bob", confirm=True)

Legacy Quick Start with OpenMemory Test Environment:
    from jean_memory import JeanMemoryV2
    
    # Load from openmemory/api/.env.test automatically
    jm = JeanMemoryV2.from_openmemory_test_env()
    
    # Use the library
    await jm.ingest_memories(["test memory"], user_id="test_user")
    result = await jm.search("test query", user_id="test_user")
    
    # Clean up for testing
    await jm.clear_user_data_for_testing("test_user", confirm=True)
"""

__version__ = "2.0.0"
__author__ = "Jean Memory Team"

# Core exports
from .config import JeanMemoryConfig

# New Unified API (v2.0) - removed (api.py moved to backup)
from .models import (
    AddMemoryRequest, AddMemoryResponse,
    AddMemoriesBulkRequest, AddMemoriesBulkResponse,
    SearchMemoriesRequest, SearchMemoriesResponse,
    ClearMemoriesRequest, ClearMemoriesResponse,
    MemoryItem, MemoryType, SearchStrategy,
    SystemStatus, APIConfig
)
# Index setup utilities - removed (moved to backup)
# Utility exports - removed (moved to backup)
from .exceptions import (
    JeanMemoryError,
    ConfigurationError,
    IngestionError,
    SearchError,
    DatabaseConnectionError,
    AuthenticationError,
    ValidationError
)

# Database utilities for testing - removed (moved to backup)

# Setup utilities - removed (moved to backup)

# Orchestrator - removed (moved to backup)

# Convenience aliases
Config = JeanMemoryConfig

__all__ = [
    # Core classes
    "JeanMemoryConfig",
    "Config",  # Alias
    
    
    # API Models
    "AddMemoryRequest", "AddMemoryResponse",
    "AddMemoriesBulkRequest", "AddMemoriesBulkResponse", 
    "SearchMemoriesRequest", "SearchMemoriesResponse",
    "ClearMemoriesRequest", "ClearMemoriesResponse",
    "MemoryItem", "MemoryType", "SearchStrategy",
    "SystemStatus", "APIConfig",
    
    
    # Exceptions
    "JeanMemoryError",
    "ConfigurationError", 
    "IngestionError",
    "SearchError",
    "DatabaseConnectionError",
    "AuthenticationError",
    "ValidationError",
    
] 