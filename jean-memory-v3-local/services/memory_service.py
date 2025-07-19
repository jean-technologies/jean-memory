"""
Memory Service for Jean Memory V3 Local
Handles mem0 with FAISS backend for local memory operations
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Import mem0 for memory management with FAISS backend
try:
    from mem0 import Memory
    import numpy as np
except ImportError as e:
    logging.error(f"Required dependencies not installed: {e}")
    logging.error("Please run: pip install mem0ai")
    raise

from config import get_config, get_data_paths, get_mem0_config

logger = logging.getLogger(__name__)

class LocalMemory:
    """Local memory item structure"""
    
    def __init__(self, 
                 id: str,
                 content: str,
                 embedding: Optional[np.ndarray] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 created_at: Optional[datetime] = None):
        self.id = id
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "source": "local"
        }

class MemoryService:
    """Local memory service using mem0 with FAISS backend"""
    
    def __init__(self):
        self.config = get_config()
        self.data_paths = get_data_paths()
        self.mem0_config = get_mem0_config()
        
        # Core components
        self.memory_client: Optional[Memory] = None
        self.memories: Dict[str, LocalMemory] = {}
        
        # State
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the memory service"""
        try:
            logger.info("🧠 Initializing mem0 with FAISS backend...")
            
            # Initialize mem0 with FAISS configuration
            await self._initialize_mem0_client()
            
            # Load existing memories
            await self._load_existing_memories()
            
            self.is_initialized = True
            logger.info(f"✅ Memory service initialized with mem0 + FAISS backend")
            
        except Exception as e:
            logger.error(f"❌ Memory service initialization failed: {e}")
            raise
    
    async def _initialize_mem0_client(self):
        """Initialize mem0 client with FAISS backend"""
        try:
            logger.info(f"📥 Initializing mem0 with FAISS backend...")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.memory_client = await loop.run_in_executor(
                None, 
                Memory,
                self.mem0_config
            )
            
            logger.info(f"✅ mem0 client initialized with FAISS backend")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize mem0 client: {e}")
            raise
    
    async def _load_existing_memories(self):
        """Load existing memories from disk (if any)"""
        # For now, start fresh. In future versions, we'll add persistence
        logger.info("📁 Starting with empty memory store")
        pass
    
    async def add_memory(self, 
                        content: str, 
                        user_id: str,
                        metadata: Optional[Dict[str, Any]] = None) -> LocalMemory:
        """Add a new memory to local storage using mem0"""
        try:
            # Prepare metadata for mem0
            mem0_metadata = {
                **(metadata or {}),
                "user_id": user_id,
                "type": "local",
                "source": "jean_memory_v3"
            }
            
            # Add memory using mem0
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.memory_client.add,
                content,
                user_id,
                mem0_metadata
            )
            
            # Extract memory ID from mem0 result
            memory_id = result.get('id') or f"local_{user_id}_{int(datetime.now().timestamp() * 1000)}"
            
            # Create local memory object for our tracking
            memory = LocalMemory(
                id=memory_id,
                content=content,
                metadata=mem0_metadata
            )
            
            # Store in our local cache
            self.memories[memory_id] = memory
            
            logger.info(f"✅ Added memory via mem0: {memory_id[:20]}...")
            return memory
            
        except Exception as e:
            logger.error(f"❌ Failed to add memory via mem0: {e}")
            raise
    
    async def search_memories(self, 
                             query: str,
                             user_id: str,
                             limit: int = 10,
                             threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search memories using mem0's semantic search"""
        try:
            # Use mem0's search functionality
            loop = asyncio.get_event_loop()
            
            # Set environment variable to avoid OpenMP threading issues
            os.environ['OMP_NUM_THREADS'] = '1'
            
            search_results = await loop.run_in_executor(
                None,
                self.memory_client.search,
                query,
                user_id,
                limit
            )
            
            results = []
            for mem0_result in search_results:
                # Convert mem0 result to our format
                memory_data = {
                    "id": mem0_result.get("id", "unknown"),
                    "content": mem0_result.get("memory", mem0_result.get("text", "")),
                    "metadata": mem0_result.get("metadata", {}),
                    "created_at": mem0_result.get("created_at", datetime.now().isoformat()),
                    "updated_at": mem0_result.get("updated_at", datetime.now().isoformat()),
                    "source": "local",
                    "score": mem0_result.get("score", 0.0)
                }
                
                # Apply threshold filter
                if memory_data["score"] >= threshold:
                    results.append(memory_data)
            
            logger.info(f"🔍 Found {len(results)} memories via mem0 for query: {query[:30]}...")
            return results
            
        except Exception as e:
            logger.error(f"❌ mem0 search failed: {e}")
            # Fallback to empty results instead of crashing
            return []
    
    async def get_memory(self, memory_id: str) -> Optional[LocalMemory]:
        """Get a specific memory by ID"""
        return self.memories.get(memory_id)
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory using mem0"""
        try:
            # Delete from mem0
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.memory_client.delete,
                memory_id
            )
            
            # Remove from local cache
            if memory_id in self.memories:
                del self.memories[memory_id]
            
            logger.info(f"✅ Deleted memory via mem0: {memory_id[:20]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete memory via mem0: {e}")
            return False
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            # Get stats from mem0 if available
            loop = asyncio.get_event_loop()
            mem0_stats = await loop.run_in_executor(
                None,
                getattr,
                self.memory_client,
                'get_stats',
                lambda: {}
            )
            
            # Filter local cache by user if specified
            if user_id:
                user_memories = [m for m in self.memories.values() 
                               if m.metadata.get("user_id") == user_id]
                count = len(user_memories)
            else:
                count = len(self.memories)
                user_memories = list(self.memories.values())
            
            return {
                "total_memories": count,
                "index_size": mem0_stats.get("index_size", 0),
                "embedding_dim": mem0_stats.get("embedding_dim", 384),  # Default for sentence transformers
                "oldest_memory": min((m.created_at for m in user_memories), default=None),
                "newest_memory": max((m.created_at for m in user_memories), default=None),
                "model": "mem0_with_faiss_backend"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {
                "total_memories": len(self.memories),
                "index_size": 0,
                "embedding_dim": 384,
                "oldest_memory": None,
                "newest_memory": None,
                "model": "mem0_with_faiss_backend"
            }
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.is_initialized and self.memory_client is not None
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up memory service...")
        
        # Clear local cache
        self.memories.clear()
        
        # mem0 handles its own cleanup
        self.memory_client = None
        
        logger.info("✅ Memory service cleanup complete")