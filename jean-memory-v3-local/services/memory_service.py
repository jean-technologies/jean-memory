"""
Memory Service for Jean Memory V3 Local
Handles FAISS vector storage and local memory operations
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# We'll use sentence-transformers for local embeddings initially
# Then integrate mem0 with FAISS backend
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
except ImportError as e:
    logging.error(f"Required dependencies not installed: {e}")
    logging.error("Please run: pip install sentence-transformers faiss-cpu")
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
    """Local memory service using FAISS and sentence-transformers"""
    
    def __init__(self):
        self.config = get_config()
        self.data_paths = get_data_paths()
        
        # Core components
        self.embedding_model: Optional[SentenceTransformer] = None
        self.faiss_index: Optional[faiss.Index] = None
        self.memories: Dict[str, LocalMemory] = {}
        self.id_to_faiss_id: Dict[str, int] = {}
        self.faiss_id_to_id: Dict[int, str] = {}
        self.next_faiss_id = 0
        
        # State
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the memory service"""
        try:
            logger.info("🧠 Initializing memory service...")
            
            # Load embedding model
            await self._load_embedding_model()
            
            # Initialize FAISS index
            await self._initialize_faiss_index()
            
            # Load existing memories
            await self._load_existing_memories()
            
            self.is_initialized = True
            logger.info(f"✅ Memory service initialized with {len(self.memories)} memories")
            
        except Exception as e:
            logger.error(f"❌ Memory service initialization failed: {e}")
            raise
    
    async def _load_embedding_model(self):
        """Load the local embedding model"""
        try:
            logger.info(f"📥 Loading embedding model: {self.config.embedding_model}")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None, 
                SentenceTransformer, 
                self.config.embedding_model
            )
            
            logger.info(f"✅ Embedding model loaded (dim: {self.embedding_model.get_sentence_embedding_dimension()})")
            
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
    
    async def _initialize_faiss_index(self):
        """Initialize FAISS index"""
        try:
            # Get embedding dimension
            dim = self.embedding_model.get_sentence_embedding_dimension()
            
            # Create FAISS index (using Inner Product for cosine similarity with normalized vectors)
            self.faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
            
            logger.info(f"✅ FAISS index initialized (dim: {dim})")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize FAISS index: {e}")
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
        """Add a new memory to local storage"""
        try:
            # Generate unique ID
            memory_id = f"local_{user_id}_{int(datetime.now().timestamp() * 1000)}"
            
            # Generate embedding
            embedding = await self._generate_embedding(content)
            
            # Create memory object
            memory = LocalMemory(
                id=memory_id,
                content=content,
                embedding=embedding,
                metadata={
                    **(metadata or {}),
                    "user_id": user_id,
                    "type": "local"
                }
            )
            
            # Add to FAISS index
            faiss_id = self.next_faiss_id
            self.next_faiss_id += 1
            
            # Normalize embedding for cosine similarity
            normalized_embedding = embedding / np.linalg.norm(embedding)
            
            # Add to FAISS (note: FAISS expects float32)
            self.faiss_index.add_with_ids(
                normalized_embedding.astype(np.float32).reshape(1, -1),
                np.array([faiss_id], dtype=np.int64)
            )
            
            # Store mappings
            self.id_to_faiss_id[memory_id] = faiss_id
            self.faiss_id_to_id[faiss_id] = memory_id
            self.memories[memory_id] = memory
            
            logger.info(f"✅ Added memory: {memory_id[:20]}...")
            return memory
            
        except Exception as e:
            logger.error(f"❌ Failed to add memory: {e}")
            raise
    
    async def search_memories(self, 
                             query: str,
                             user_id: str,
                             limit: int = 10,
                             threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search memories using semantic similarity"""
        try:
            if not self.memories:
                return []
            
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            normalized_query = query_embedding / np.linalg.norm(query_embedding)
            
            # Search FAISS index
            scores, indices = self.faiss_index.search(
                normalized_query.astype(np.float32).reshape(1, -1), 
                min(limit * 2, len(self.memories))  # Get more results to filter by user
            )
            
            results = []
            for score, faiss_id in zip(scores[0], indices[0]):
                if faiss_id == -1:  # FAISS returns -1 for empty slots
                    continue
                    
                memory_id = self.faiss_id_to_id.get(faiss_id)
                if not memory_id:
                    continue
                    
                memory = self.memories.get(memory_id)
                if not memory:
                    continue
                
                # Filter by user
                if memory.metadata.get("user_id") != user_id:
                    continue
                
                # Apply threshold
                if score < threshold:
                    continue
                
                result = memory.to_dict()
                result["score"] = float(score)
                results.append(result)
                
                if len(results) >= limit:
                    break
            
            # Sort by score (descending)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            logger.info(f"🔍 Found {len(results)} memories for query: {query[:30]}...")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def get_memory(self, memory_id: str) -> Optional[LocalMemory]:
        """Get a specific memory by ID"""
        return self.memories.get(memory_id)
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        try:
            if memory_id not in self.memories:
                return False
            
            # Remove from FAISS index
            faiss_id = self.id_to_faiss_id.get(memory_id)
            if faiss_id is not None:
                # FAISS doesn't support direct deletion, so we'll mark as deleted
                # In a production system, we'd rebuild the index periodically
                del self.id_to_faiss_id[memory_id]
                del self.faiss_id_to_id[faiss_id]
            
            # Remove from memory store
            del self.memories[memory_id]
            
            logger.info(f"✅ Deleted memory: {memory_id[:20]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete memory: {e}")
            return False
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics"""
        if user_id:
            user_memories = [m for m in self.memories.values() 
                           if m.metadata.get("user_id") == user_id]
            count = len(user_memories)
        else:
            count = len(self.memories)
            user_memories = list(self.memories.values())
        
        return {
            "total_memories": count,
            "index_size": self.faiss_index.ntotal if self.faiss_index else 0,
            "embedding_dim": self.embedding_model.get_sentence_embedding_dimension() if self.embedding_model else 0,
            "oldest_memory": min((m.created_at for m in user_memories), default=None),
            "newest_memory": max((m.created_at for m in user_memories), default=None),
            "model": self.config.embedding_model
        }
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embedding_model.encode,
                text
            )
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embedding: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if service is ready"""
        return self.is_initialized and self.embedding_model is not None and self.faiss_index is not None
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up memory service...")
        
        # In a production system, we'd save the current state to disk here
        self.memories.clear()
        self.id_to_faiss_id.clear()
        self.faiss_id_to_id.clear()
        
        # Reset FAISS index
        if self.faiss_index:
            self.faiss_index.reset()
        
        logger.info("✅ Memory service cleanup complete")