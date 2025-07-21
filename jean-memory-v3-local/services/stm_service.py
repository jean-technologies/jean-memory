"""
STM (Short-Term Memory) Service for Jean Memory V3
Implements RAM-resident FAISS + ephemeral Neo4j with V2 production compatibility
"""

import asyncio
import logging
import os
import uuid
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# Core dependencies
try:
    from mem0 import Memory
    from mem0.configs.base import MemoryConfig
    from mem0.configs.vector_store import VectorStoreConfig, FaissConfig
    from mem0.configs.embedder import EmbedderConfig
    import numpy as np
except ImportError as e:
    logging.error(f"mem0 not installed: {e}")
    raise

from config import get_config, get_data_paths
from .graph_service import GraphService

logger = logging.getLogger(__name__)

class STMMemory:
    """STM memory item with V2 production compatibility"""
    
    def __init__(self,
                 id: str,
                 content: str,
                 user_id: str,
                 app_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 created_at: Optional[datetime] = None,
                 state: str = "active"):
        self.id = id
        self.content = content
        self.user_id = user_id
        self.app_id = app_id or "jean_memory_v3_stm"
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.state = state
        self.source = "stm"
        
        # STM-specific attributes
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.salience_score = 0.0
        self.upload_status = "pending"  # pending, uploaded, failed
        
    def to_v2_format(self) -> Dict[str, Any]:
        """Convert to V2 production API format"""
        return {
            "id": self.id,
            "content": self.content,
            "created_at": int(self.created_at.timestamp()),
            "state": self.state,
            "app_id": self.app_id,
            "app_name": "Jean Memory V3 STM",
            "categories": self.metadata.get("categories", []),
            "metadata_": {
                **self.metadata,
                "source": self.source,
                "last_accessed": self.last_accessed.isoformat(),
                "access_count": self.access_count,
                "salience_score": self.salience_score,
                "upload_status": self.upload_status
            }
        }
    
    def update_access(self):
        """Update access tracking for salience calculation"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        
    def calculate_salience(self) -> float:
        """Calculate memory salience for shuttle prioritization"""
        now = datetime.now()
        
        # Recency factor (more recent = higher score)
        hours_since_created = (now - self.created_at).total_seconds() / 3600
        recency_score = max(0, 1.0 - (hours_since_created / 168))  # Decay over 1 week
        
        # Usage factor
        usage_score = min(1.0, self.access_count / 10.0)  # Cap at 10 accesses
        
        # Combined salience
        self.salience_score = (recency_score * 0.6) + (usage_score * 0.4)
        return self.salience_score

class STMService:
    """Short-Term Memory service implementing V3 spec"""
    
    def __init__(self):
        self.config = get_config()
        self.data_paths = get_data_paths()
        
        # Core STM components
        self.memory_client: Optional[Memory] = None
        self.graph_service = GraphService()
        
        # STM-specific storage
        self.memories: Dict[str, STMMemory] = {}  # In-memory cache
        self.user_memories: Dict[str, List[str]] = {}  # User -> memory_ids mapping
        
        # Resource management
        self.max_memories = self.config.max_local_memories
        self.current_size_mb = 0.0
        self.max_size_mb = 512.0  # 512MB RAM budget for STM
        
        # State
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize STM with RAM-resident FAISS + ephemeral Neo4j"""
        try:
            logger.info("🧠 Initializing STM (Short-Term Memory)...")
            
            # Initialize mem0 with RAM-optimized FAISS
            await self._initialize_stm_memory_client()
            
            # Initialize ephemeral Neo4j for graph operations
            await self.graph_service.initialize()
            
            # Setup resource monitoring
            await self._setup_resource_governor()
            
            self.is_initialized = True
            logger.info("✅ STM initialized - RAM-resident FAISS + ephemeral Neo4j ready")
            
        except Exception as e:
            logger.error(f"❌ STM initialization failed: {e}")
            raise
    
    async def _initialize_stm_memory_client(self):
        """Initialize mem0 with RAM-optimized configuration"""
        try:
            # Create FAISS in-memory configuration
            stm_faiss_path = self.data_paths["faiss"] / "stm"
            stm_faiss_path.mkdir(exist_ok=True)
            
            vector_store_config = VectorStoreConfig(
                provider="faiss",
                config=FaissConfig(
                    collection_name="jean_memory_v3_stm",
                    path=str(stm_faiss_path),
                    # RAM optimizations
                    memory_budget_gb=0.5,  # 512MB budget
                    nlist=100,  # Smaller index for faster access
                    nprobe=10
                )
            )
            
            embedder_config = EmbedderConfig(
                provider="sentence_transformers",
                config={
                    "model": self.config.embedding_model,
                    "embedding_dim": self.config.embedding_dim
                }
            )
            
            memory_config = MemoryConfig(
                vector_store=vector_store_config,
                embedder=embedder_config
            )
            
            # Initialize in thread pool
            loop = asyncio.get_event_loop()
            self.memory_client = await loop.run_in_executor(
                None,
                Memory,
                memory_config
            )
            
            logger.info("✅ STM mem0 client initialized with RAM-optimized FAISS")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize STM memory client: {e}")
            raise
    
    async def _setup_resource_governor(self):
        """Setup resource monitoring and management"""
        # Initial resource assessment
        logger.info(f"📊 STM Resource Budget: {self.max_memories} memories, {self.max_size_mb}MB RAM")
    
    async def add_memory(self,
                        content: Union[str, List[str], List[Dict]],
                        user_id: str,
                        app_id: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> STMMemory:
        """Add memory to STM with V2 compatibility"""
        try:
            # Convert content to string if needed
            if isinstance(content, list):
                if content and isinstance(content[0], dict):
                    # Extract text from message format
                    content = " ".join([msg.get("content", str(msg)) for msg in content])
                else:
                    content = " ".join(str(item) for item in content)
            
            # Generate STM memory ID
            memory_id = f"stm_{user_id}_{uuid.uuid4().hex[:12]}"
            
            # Prepare metadata with STM tracking
            stm_metadata = {
                **(metadata or {}),
                "user_id": user_id,
                "app_id": app_id or "jean_memory_v3_stm",
                "source": "stm",
                "created_at": datetime.now().isoformat()
            }
            
            # Add to mem0 vector store
            loop = asyncio.get_event_loop()
            
            # Set OMP_NUM_THREADS to avoid threading issues
            os.environ['OMP_NUM_THREADS'] = '1'
            
            mem0_result = await loop.run_in_executor(
                None,
                self.memory_client.add,
                content,
                user_id,
                stm_metadata
            )
            
            # Create STM memory object
            stm_memory = STMMemory(
                id=memory_id,
                content=content,
                user_id=user_id,
                app_id=app_id,
                metadata=stm_metadata
            )
            
            # Store in local cache
            self.memories[memory_id] = stm_memory
            
            # Update user index
            if user_id not in self.user_memories:
                self.user_memories[user_id] = []
            self.user_memories[user_id].append(memory_id)
            
            # Add to graph service
            await self.graph_service.add_memory_to_graph(
                memory_id=memory_id,
                content=content,
                user_id=user_id
            )
            
            # Check resource limits
            await self._check_resource_limits(user_id)
            
            logger.info(f"✅ Added STM memory: {memory_id}")
            return stm_memory
            
        except Exception as e:
            logger.error(f"❌ Failed to add STM memory: {e}")
            raise
    
    async def search_memories(self,
                             query: str,
                             user_id: str,
                             limit: int = 10,
                             threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search STM memories with access tracking"""
        try:
            # Set OMP_NUM_THREADS to avoid threading issues
            os.environ['OMP_NUM_THREADS'] = '1'
            
            # Search using mem0
            loop = asyncio.get_event_loop()
            mem0_results = await loop.run_in_executor(
                None,
                self.memory_client.search,
                query,
                user_id,
                limit
            )
            
            results = []
            for mem0_result in mem0_results:
                # Find corresponding STM memory
                memory_content = mem0_result.get("memory", mem0_result.get("text", ""))
                
                # Find matching STM memory by content
                matching_memory = None
                for memory in self.memories.values():
                    if (memory.user_id == user_id and 
                        memory.content == memory_content):
                        matching_memory = memory
                        break
                
                if matching_memory:
                    # Update access tracking
                    matching_memory.update_access()
                    
                    # Convert to V2 format with score
                    result = matching_memory.to_v2_format()
                    result["score"] = mem0_result.get("score", 0.0)
                    
                    # Apply threshold
                    if result["score"] >= threshold:
                        results.append(result)
            
            logger.info(f"🔍 STM search found {len(results)} memories for: {query[:30]}...")
            return results
            
        except Exception as e:
            logger.error(f"❌ STM search failed: {e}")
            return []
    
    async def get_memory(self, memory_id: str) -> Optional[STMMemory]:
        """Get specific STM memory with access tracking"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.update_access()
        return memory
    
    async def get_user_memories(self,
                               user_id: str,
                               limit: int = 50,
                               state: str = "active") -> List[Dict[str, Any]]:
        """Get all STM memories for a user"""
        try:
            user_memory_ids = self.user_memories.get(user_id, [])
            memories = []
            
            for memory_id in user_memory_ids[-limit:]:  # Most recent first
                memory = self.memories.get(memory_id)
                if memory and memory.state == state:
                    memory.update_access()
                    memories.append(memory.to_v2_format())
            
            # Sort by created_at descending
            memories.sort(key=lambda x: x["created_at"], reverse=True)
            
            return memories
            
        except Exception as e:
            logger.error(f"❌ Failed to get user memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory from STM"""
        try:
            memory = self.memories.get(memory_id)
            if not memory:
                return False
            
            # Remove from mem0
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.memory_client.delete,
                memory_id
            )
            
            # Remove from graph
            await self.graph_service.delete_memory_from_graph(memory_id)
            
            # Remove from local storage
            user_id = memory.user_id
            if user_id in self.user_memories:
                if memory_id in self.user_memories[user_id]:
                    self.user_memories[user_id].remove(memory_id)
            
            del self.memories[memory_id]
            
            logger.info(f"✅ Deleted STM memory: {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete STM memory: {e}")
            return False
    
    async def _check_resource_limits(self, user_id: str):
        """Check and enforce STM resource limits"""
        try:
            # Check memory count limit
            total_memories = len(self.memories)
            if total_memories > self.max_memories:
                await self._evict_lru_memories(user_id, total_memories - self.max_memories)
            
            # TODO: Check RAM usage and evict if needed
            
        except Exception as e:
            logger.error(f"❌ Resource limit check failed: {e}")
    
    async def _evict_lru_memories(self, user_id: str, count: int):
        """Evict least recently used memories"""
        try:
            # Get user memories sorted by last_accessed
            user_memory_ids = self.user_memories.get(user_id, [])
            user_memories = [self.memories[mid] for mid in user_memory_ids if mid in self.memories]
            user_memories.sort(key=lambda m: m.last_accessed)
            
            # Evict oldest accessed memories
            for memory in user_memories[:count]:
                logger.info(f"🔄 Evicting LRU memory: {memory.id}")
                await self.delete_memory(memory.id)
                
        except Exception as e:
            logger.error(f"❌ LRU eviction failed: {e}")
    
    async def get_upload_candidates(self, user_id: str, limit: int = 50) -> List[STMMemory]:
        """Get memories ready for upload to LTM based on salience"""
        try:
            user_memory_ids = self.user_memories.get(user_id, [])
            candidates = []
            
            for memory_id in user_memory_ids:
                memory = self.memories.get(memory_id)
                if (memory and 
                    memory.upload_status == "pending" and
                    memory.state == "active"):
                    
                    # Calculate current salience
                    memory.calculate_salience()
                    candidates.append(memory)
            
            # Sort by salience score (highest first)
            candidates.sort(key=lambda m: m.salience_score, reverse=True)
            
            return candidates[:limit]
            
        except Exception as e:
            logger.error(f"❌ Failed to get upload candidates: {e}")
            return []
    
    async def mark_uploaded(self, memory_id: str, ltm_id: str):
        """Mark memory as uploaded to LTM"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.upload_status = "uploaded"
            memory.metadata["ltm_id"] = ltm_id
            logger.info(f"✅ Marked memory as uploaded: {memory_id} -> {ltm_id}")
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get STM statistics"""
        try:
            if user_id:
                user_memory_ids = self.user_memories.get(user_id, [])
                user_memories = [self.memories[mid] for mid in user_memory_ids if mid in self.memories]
                memory_count = len(user_memories)
                
                # Calculate average salience
                if user_memories:
                    avg_salience = sum(m.calculate_salience() for m in user_memories) / len(user_memories)
                else:
                    avg_salience = 0.0
            else:
                memory_count = len(self.memories)
                if self.memories:
                    avg_salience = sum(m.calculate_salience() for m in self.memories.values()) / len(self.memories)
                else:
                    avg_salience = 0.0
            
            return {
                "total_memories": memory_count,
                "max_memories": self.max_memories,
                "memory_utilization": memory_count / self.max_memories if self.max_memories else 0,
                "current_size_mb": self.current_size_mb,
                "max_size_mb": self.max_size_mb,
                "ram_utilization": self.current_size_mb / self.max_size_mb,
                "average_salience": avg_salience,
                "graph_stats": await self.graph_service.get_graph_stats(user_id),
                "source": "stm"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get STM stats: {e}")
            return {"error": str(e), "source": "stm"}
    
    def is_ready(self) -> bool:
        """Check if STM service is ready"""
        return (self.is_initialized and 
                self.memory_client is not None and
                self.graph_service.is_ready())
    
    async def cleanup(self):
        """Cleanup STM resources"""
        logger.info("🧹 Cleaning up STM service...")
        
        # Clear in-memory storage
        self.memories.clear()
        self.user_memories.clear()
        
        # Cleanup graph service
        await self.graph_service.cleanup()
        
        # mem0 handles its own cleanup
        self.memory_client = None
        
        logger.info("✅ STM service cleanup complete")