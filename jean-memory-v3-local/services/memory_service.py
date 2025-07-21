"""
Jean Memory V3 Main Service
Orchestrates STM + LTM + Memory Shuttle + ADK interfaces
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from config import get_config
from services.stm_service import STMService
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle
from services.google_memory_service import GoogleADKMemoryService
from services.hybrid_orchestrator import HybridMemoryOrchestrator
from adk.session_service import InMemorySessionService, CloudSessionService
from adk.memory_service import create_memory_service, BaseMemoryService

logger = logging.getLogger(__name__)

class JeanMemoryV3Service:
    """Main Jean Memory V3 service implementing the complete V3 architecture"""
    
    def __init__(self):
        self.config = get_config()
        
        # Core V3 components
        self.stm_service: Optional[STMService] = None
        self.ltm_service: Optional[LTMService] = None
        self.memory_shuttle: Optional[MemoryShuttle] = None
        
        # Google ADK integration
        self.google_service: Optional[GoogleADKMemoryService] = None
        self.hybrid_orchestrator: Optional[HybridMemoryOrchestrator] = None
        
        # ADK interfaces
        self.session_service: Optional[InMemorySessionService] = None
        self.cloud_session_service: Optional[CloudSessionService] = None
        self.memory_service: Optional[BaseMemoryService] = None
        
        # State
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the complete Jean Memory V3 system"""
        try:
            logger.info("🚀 Initializing Jean Memory V3 - STM + LTM + Memory Shuttle + ADK...")
            
            # 1. Initialize STM (Short-Term Memory)
            logger.info("🧠 Initializing STM (Short-Term Memory)...")
            self.stm_service = STMService()
            await self.stm_service.initialize()
            
            # 2. Initialize LTM (Long-Term Memory)
            logger.info("☁️  Initializing LTM (Long-Term Memory)...")
            self.ltm_service = LTMService()
            await self.ltm_service.initialize()
            
            # 3. Initialize Memory Shuttle
            logger.info("🚀 Initializing Memory Shuttle...")
            self.memory_shuttle = MemoryShuttle(self.stm_service, self.ltm_service)
            await self.memory_shuttle.start()
            
            # 4. Initialize Google ADK Service
            logger.info("🔗 Initializing Google ADK Service...")
            self.google_service = GoogleADKMemoryService()
            await self.google_service.initialize()
            
            # 5. Initialize Hybrid Memory Orchestrator
            logger.info("⚡ Initializing Hybrid Memory Orchestrator...")
            self.hybrid_orchestrator = HybridMemoryOrchestrator()
            await self.hybrid_orchestrator.initialize(
                google_service=self.google_service,
                stm_service=self.stm_service,
                ltm_service=self.ltm_service,
                shuttle=self.memory_shuttle
            )
            
            # 6. Initialize ADK Session Services
            logger.info("📝 Initializing ADK Session Services...")
            self.session_service = InMemorySessionService()
            if self.ltm_service.is_ready():
                self.cloud_session_service = CloudSessionService(self.ltm_service)
            
            # 7. Initialize ADK Memory Service
            logger.info("🔗 Initializing ADK Memory Service...")
            self.memory_service = create_memory_service(
                stm_service=self.stm_service,
                ltm_service=self.ltm_service,
                shuttle=self.memory_shuttle,
                google_service=self.google_service
            )
            
            self.is_initialized = True
            
            # Log system status
            await self._log_system_status()
            
            logger.info("🎉 Jean Memory V3 initialization complete!")
            
        except Exception as e:
            logger.error(f"❌ Jean Memory V3 initialization failed: {e}")
            raise
    
    async def _log_system_status(self):
        """Log the status of all V3 components"""
        try:
            logger.info("📊 Jean Memory V3 System Status:")
            logger.info(f"  🧠 STM Ready: {self.stm_service.is_ready() if self.stm_service else False}")
            logger.info(f"  ☁️  LTM Ready: {self.ltm_service.is_ready() if self.ltm_service else False}")
            logger.info(f"  🚀 Shuttle Running: {self.memory_shuttle.is_running if self.memory_shuttle else False}")
            logger.info(f"  🔗 Google ADK Ready: {self.google_service.initialized if self.google_service else False}")
            logger.info(f"  ⚡ Hybrid Orchestrator Ready: {self.hybrid_orchestrator.initialized if self.hybrid_orchestrator else False}")
            logger.info(f"  📝 Sessions Ready: {self.session_service is not None}")
            logger.info(f"  🔗 Memory Service: {type(self.memory_service).__name__ if self.memory_service else 'None'}")
            
            # Get initial stats
            if self.memory_service:
                stats = await self.memory_service.get_stats()
                logger.info(f"  📈 Service Type: {stats.get('service_type', 'unknown')}")
                
        except Exception as e:
            logger.error(f"❌ Failed to log system status: {e}")
    
    # V3 ADK Memory Interface Methods
    async def add_memory(self, 
                        content: Union[str, List], 
                        user_id: str,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add memory using V3 ADK Memory Service"""
        if not self.memory_service:
            raise Exception("Memory service not initialized")
            
        return await self.memory_service.add_memory(
            content=content,
            user_id=user_id,
            metadata=metadata
        )
    
    async def search_memories(self, 
                             query: str,
                             user_id: str,
                             limit: int = 10,
                             threshold: float = 0.3) -> Dict[str, Any]:
        """Search memories using V3 ADK Memory Service"""
        if not self.memory_service:
            raise Exception("Memory service not initialized")
            
        result = await self.memory_service.search_memories(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        # Filter by threshold and return in API format
        filtered_memories = []
        for memory in result.memories:
            score = memory.get("score", 0.0)
            if score >= threshold:
                filtered_memories.append(memory)
        
        return {
            "memories": filtered_memories,
            "total": len(filtered_memories),
            "source": result.source,
            "execution_time_ms": result.execution_time_ms,
            "query": query
        }
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific memory using V3 ADK Memory Service"""
        if not self.memory_service:
            return None
            
        return await self.memory_service.get_memory(memory_id, user_id)
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory using V3 ADK Memory Service"""
        if not self.memory_service:
            return False
            
        return await self.memory_service.delete_memory(memory_id, user_id)
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive V3 system statistics"""
        if not self.memory_service:
            return {"error": "Memory service not initialized"}
            
        return await self.memory_service.get_stats(user_id)
    
    # V3 ADK Session Interface Methods
    async def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new session using ADK Session Service"""
        if not self.session_service:
            raise Exception("Session service not initialized")
            
        return await self.session_service.create_session(user_id, metadata)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not self.session_service:
            return None
            
        session = await self.session_service.get_session(session_id)
        return session.to_dict() if session else None
    
    async def update_session_state(self, session_id: str, key: str, value: Any) -> bool:
        """Update session state"""
        if not self.session_service:
            return False
            
        return await self.session_service.update_session_state(session_id, key, value)
    
    # V3 Memory Shuttle Interface Methods
    async def force_sync_to_ltm(self, user_id: str) -> Dict[str, Any]:
        """Force immediate sync of user memories to LTM"""
        if not self.memory_shuttle:
            return {"error": "Memory shuttle not initialized"}
            
        return await self.memory_shuttle.force_upload_user_memories(user_id)
    
    async def preload_hot_memories(self, user_id: str) -> Dict[str, Any]:
        """Preload hot memories from LTM to STM"""
        if not self.memory_shuttle:
            return {"error": "Memory shuttle not initialized"}
            
        return await self.memory_shuttle.preload_hot_memories(user_id)
    
    async def get_shuttle_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Memory Shuttle statistics"""
        if not self.memory_shuttle:
            return {"error": "Memory shuttle not initialized"}
            
        return await self.memory_shuttle.get_shuttle_stats(user_id)
    
    def is_ready(self) -> bool:
        """Check if V3 service is ready"""
        return (self.is_initialized and 
                self.memory_service is not None and
                self.stm_service is not None)
    
    async def cleanup(self):
        """Cleanup V3 resources"""
        logger.info("🧹 Cleaning up Jean Memory V3...")
        
        # Stop memory shuttle
        if self.memory_shuttle:
            await self.memory_shuttle.stop()
        
        # Cleanup STM service
        if self.stm_service:
            await self.stm_service.cleanup()
        
        # Cleanup LTM service
        if self.ltm_service:
            await self.ltm_service.cleanup()
        
        logger.info("✅ Jean Memory V3 cleanup complete")

# Legacy alias for backward compatibility
MemoryService = JeanMemoryV3Service