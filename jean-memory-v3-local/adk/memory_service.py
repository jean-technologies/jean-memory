"""
ADK MemoryService for Jean Memory V3
Provides unified memory interface across STM and LTM with intelligent routing
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from abc import ABC, abstractmethod

from services.stm_service import STMService
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle
from services.google_memory_service import GoogleADKMemoryService

logger = logging.getLogger(__name__)

class MemoryResult:
    """Unified memory result container"""
    
    def __init__(self, memories: List[Dict[str, Any]], 
                 source: str, execution_time_ms: int = 0):
        self.memories = memories
        self.source = source  # "stm", "ltm", or "hybrid"
        self.execution_time_ms = execution_time_ms
        self.total = len(memories)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "memories": self.memories,
            "total": self.total,
            "source": self.source,
            "execution_time_ms": self.execution_time_ms
        }

class BaseMemoryService(ABC):
    """Abstract base for memory services"""
    
    @abstractmethod
    async def add_memory(self, content: Union[str, List], user_id: str, 
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add memory"""
        pass
    
    @abstractmethod
    async def search_memories(self, query: str, user_id: str, 
                             limit: int = 10) -> MemoryResult:
        """Search memories"""
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific memory"""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory"""
        pass

class InMemoryMemoryService(BaseMemoryService):
    """In-memory memory service wrapping STM (FAISS + Neo4j-RAM)"""
    
    def __init__(self, stm_service: STMService):
        self.stm = stm_service
    
    async def add_memory(self, content: Union[str, List], user_id: str, 
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add memory to STM only"""
        stm_memory = await self.stm.add_memory(
            content=content,
            user_id=user_id,
            metadata=metadata
        )
        
        return stm_memory.to_v2_format()
    
    async def search_memories(self, query: str, user_id: str, 
                             limit: int = 10) -> MemoryResult:
        """Search STM memories only"""
        start_time = datetime.now()
        
        memories = await self.stm.search_memories(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return MemoryResult(
            memories=memories,
            source="stm",
            execution_time_ms=execution_time
        )
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from STM"""
        memory = await self.stm.get_memory(memory_id)
        if memory and memory.user_id == user_id:
            return memory.to_v2_format()
        return None
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from STM"""
        memory = await self.stm.get_memory(memory_id)
        if memory and memory.user_id == user_id:
            return await self.stm.delete_memory(memory_id)
        return False

class CloudMemoryService(BaseMemoryService):
    """Cloud memory service wrapping LTM (Qdrant + Neo4j Aura)"""
    
    def __init__(self, ltm_service: LTMService):
        self.ltm = ltm_service
    
    async def add_memory(self, content: Union[str, List], user_id: str, 
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add memory to LTM only"""
        result = await self.ltm.upload_memory(
            content=content,
            user_id=user_id,
            metadata=metadata
        )
        
        if result:
            return result
        else:
            raise Exception("Failed to add memory to LTM")
    
    async def search_memories(self, query: str, user_id: str, 
                             limit: int = 10) -> MemoryResult:
        """Search LTM memories only"""
        start_time = datetime.now()
        
        memories = await self.ltm.search_memories(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return MemoryResult(
            memories=memories,
            source="ltm",
            execution_time_ms=execution_time
        )
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from LTM"""
        return await self.ltm.get_memory(memory_id, user_id)
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from LTM"""
        return await self.ltm.delete_memory(memory_id, user_id)

class HybridMemoryService(BaseMemoryService):
    """Hybrid memory service with intelligent STM/LTM routing"""
    
    def __init__(self, stm_service: STMService, ltm_service: LTMService, 
                 shuttle: MemoryShuttle):
        self.stm = stm_service
        self.ltm = ltm_service
        self.shuttle = shuttle
        
        # Configuration
        self.stm_first_search = True  # Search STM first for speed
        self.auto_upload = True       # Auto-queue memories for upload
        self.hybrid_search_limit = 20 # Max memories per source in hybrid search
    
    async def add_memory(self, content: Union[str, List], user_id: str, 
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add memory to STM and queue for LTM upload"""
        # Always add to STM first for instant access
        stm_memory = await self.stm.add_memory(
            content=content,
            user_id=user_id,
            metadata=metadata
        )
        
        # Queue for LTM upload if auto-upload enabled
        if self.auto_upload and self.ltm.is_ready():
            await self.shuttle.queue_for_upload(user_id, stm_memory.id)
        
        return stm_memory.to_v2_format()
    
    async def search_memories(self, query: str, user_id: str, 
                             limit: int = 10) -> MemoryResult:
        """Hybrid search across STM and LTM"""
        start_time = datetime.now()
        all_memories = []
        sources_used = []
        
        try:
            # Search STM first (fastest)
            if self.stm.is_ready():
                stm_memories = await self.stm.search_memories(
                    query=query,
                    user_id=user_id,
                    limit=min(limit, self.hybrid_search_limit)
                )
                all_memories.extend(stm_memories)
                if stm_memories:
                    sources_used.append("stm")
            
            # Search LTM if connected and we need more results
            remaining_limit = limit - len(all_memories)
            if remaining_limit > 0 and self.ltm.is_ready():
                ltm_memories = await self.ltm.search_memories(
                    query=query,
                    user_id=user_id,
                    limit=min(remaining_limit, self.hybrid_search_limit)
                )
                
                # Deduplicate by content
                existing_contents = set(mem.get("content", "") for mem in all_memories)
                for ltm_memory in ltm_memories:
                    if ltm_memory.get("content", "") not in existing_contents:
                        all_memories.append(ltm_memory)
                
                if ltm_memories:
                    sources_used.append("ltm")
            
            # Sort by score if available, otherwise by created_at
            all_memories.sort(key=lambda m: (
                m.get("score", 0.0),
                m.get("created_at", 0)
            ), reverse=True)
            
            # Limit results
            final_memories = all_memories[:limit]
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Determine source designation
            if len(sources_used) == 0:
                source = "none"
            elif len(sources_used) == 1:
                source = sources_used[0]
            else:
                source = "hybrid"
            
            return MemoryResult(
                memories=final_memories,
                source=source,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"❌ Hybrid search failed: {e}")
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return MemoryResult(
                memories=[],
                source="error",
                execution_time_ms=execution_time
            )
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from STM first, fallback to LTM"""
        # Try STM first
        if memory_id.startswith("stm_"):
            memory = await self.stm.get_memory(memory_id)
            if memory and memory.user_id == user_id:
                return memory.to_v2_format()
        
        # Fallback to LTM
        if self.ltm.is_ready():
            return await self.ltm.get_memory(memory_id, user_id)
        
        return None
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from both STM and LTM"""
        stm_success = False
        ltm_success = False
        
        # Try STM deletion
        if memory_id.startswith("stm_"):
            memory = await self.stm.get_memory(memory_id)
            if memory and memory.user_id == user_id:
                stm_success = await self.stm.delete_memory(memory_id)
                
                # Also try to delete from LTM if it was uploaded
                ltm_id = memory.metadata.get("ltm_id")
                if ltm_id and self.ltm.is_ready():
                    ltm_success = await self.ltm.delete_memory(ltm_id, user_id)
        
        # Try LTM deletion
        elif self.ltm.is_ready():
            ltm_success = await self.ltm.delete_memory(memory_id, user_id)
        
        return stm_success or ltm_success
    
    async def get_user_memories(self, user_id: str, limit: int = 50, 
                               source: str = "hybrid") -> MemoryResult:
        """Get user memories from specified source(s)"""
        start_time = datetime.now()
        all_memories = []
        sources_used = []
        
        try:
            if source in ["stm", "hybrid"]:
                stm_memories = await self.stm.get_user_memories(user_id, limit)
                all_memories.extend(stm_memories)
                if stm_memories:
                    sources_used.append("stm")
            
            if source in ["ltm", "hybrid"] and self.ltm.is_ready():
                ltm_memories = await self.ltm.get_user_memories(user_id, limit)
                
                # Deduplicate if hybrid
                if source == "hybrid":
                    existing_ids = set(mem.get("id", "") for mem in all_memories)
                    for ltm_memory in ltm_memories:
                        if ltm_memory.get("id", "") not in existing_ids:
                            all_memories.append(ltm_memory)
                else:
                    all_memories.extend(ltm_memories)
                
                if ltm_memories:
                    sources_used.append("ltm")
            
            # Sort by created_at descending
            all_memories.sort(key=lambda m: m.get("created_at", 0), reverse=True)
            
            # Limit results
            final_memories = all_memories[:limit]
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Determine source designation
            actual_source = source
            if source == "hybrid":
                if len(sources_used) == 0:
                    actual_source = "none"
                elif len(sources_used) == 1:
                    actual_source = sources_used[0]
                else:
                    actual_source = "hybrid"
            
            return MemoryResult(
                memories=final_memories,
                source=actual_source,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            logger.error(f"❌ Get user memories failed: {e}")
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            return MemoryResult(
                memories=[],
                source="error",
                execution_time_ms=execution_time
            )
    
    async def force_sync(self, user_id: str) -> Dict[str, Any]:
        """Force immediate sync of user memories to LTM"""
        return await self.shuttle.force_upload_user_memories(user_id)
    
    async def preload_hot_memories(self, user_id: str) -> Dict[str, Any]:
        """Preload hot memories from LTM to STM"""
        return await self.shuttle.preload_hot_memories(user_id)
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive memory service statistics"""
        stm_stats = await self.stm.get_stats(user_id)
        ltm_stats = await self.ltm.get_stats(user_id)
        shuttle_stats = await self.shuttle.get_shuttle_stats(user_id)
        
        return {
            "service_type": "hybrid",
            "stm": stm_stats,
            "ltm": ltm_stats,
            "shuttle": shuttle_stats,
            "configuration": {
                "stm_first_search": self.stm_first_search,
                "auto_upload": self.auto_upload,
                "hybrid_search_limit": self.hybrid_search_limit
            }
        }

class GoogleADKService(BaseMemoryService):
    """Google ADK Memory Service wrapper for Tier 1 operations"""
    
    def __init__(self, google_service: GoogleADKMemoryService):
        self.google = google_service
    
    async def add_memory(self, content: Union[str, List], user_id: str, 
                        metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add memory to Google ADK (Tier 1)"""
        content_str = content if isinstance(content, str) else str(content)
        result = await self.google.add_memory_to_google_adk(content_str, user_id, metadata)
        
        if result:
            return result
        else:
            raise Exception("Failed to add memory to Google ADK")
    
    async def search_memories(self, query: str, user_id: str, 
                             limit: int = 10) -> MemoryResult:
        """Search Google ADK memories"""
        start_time = datetime.now()
        
        memories = await self.google.search_google_memories(query, user_id, limit)
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return MemoryResult(
            memories=memories,
            source="google_adk",
            execution_time_ms=execution_time
        )
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get memory from Google ADK"""
        return await self.google.get_memory_by_id(memory_id, user_id)
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from Google ADK"""
        return await self.google.delete_memory(memory_id, user_id)

# Factory function for creating appropriate memory service
def create_memory_service(stm_service: STMService, 
                         ltm_service: Optional[LTMService] = None,
                         shuttle: Optional[MemoryShuttle] = None,
                         google_service: Optional[GoogleADKMemoryService] = None) -> BaseMemoryService:
    """Create appropriate memory service based on available components"""
    
    # Prioritize Google ADK if available (Tier 1)
    if google_service:
        return GoogleADKService(google_service)
    elif ltm_service and shuttle:
        # Full hybrid service (Tier 2 + 3)
        return HybridMemoryService(stm_service, ltm_service, shuttle)
    elif ltm_service:
        # Cloud-only service (Tier 3)
        return CloudMemoryService(ltm_service)
    else:
        # STM-only service (Tier 2)
        return InMemoryMemoryService(stm_service)