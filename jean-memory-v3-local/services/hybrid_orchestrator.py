"""
Hybrid Memory Orchestrator for Jean Memory V3
Intelligent three-tier memory routing: Google ADK (Tier 1) -> Jean V3 STM (Tier 2) -> Jean V2 Production (Tier 3)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from services.google_memory_service import GoogleADKMemoryService
from services.stm_service import STMService
from services.ltm_service import LTMService
from services.memory_shuttle import MemoryShuttle

logger = logging.getLogger(__name__)

class MemoryTier(Enum):
    """Memory tier definitions"""
    TIER_1_GOOGLE_ADK = 1  # 2-5ms - Google ADK InMemory
    TIER_2_JEAN_STM = 2    # 5-15ms - Jean V3 STM FAISS
    TIER_3_JEAN_V2 = 3     # 100-250ms - Jean V2 Production

class HybridMemoryOrchestrator:
    """Routes memory operations across three tiers intelligently"""
    
    def __init__(self):
        self.google_service: Optional[GoogleADKMemoryService] = None
        self.stm_service: Optional[STMService] = None
        self.ltm_service: Optional[LTMService] = None
        self.shuttle: Optional[MemoryShuttle] = None
        
        # Performance tracking
        self.tier_performance = {
            MemoryTier.TIER_1_GOOGLE_ADK: {"total_calls": 0, "total_time_ms": 0, "avg_time_ms": 0},
            MemoryTier.TIER_2_JEAN_STM: {"total_calls": 0, "total_time_ms": 0, "avg_time_ms": 0},
            MemoryTier.TIER_3_JEAN_V2: {"total_calls": 0, "total_time_ms": 0, "avg_time_ms": 0}
        }
        
        # Configuration
        self.tier_1_enabled = True
        self.tier_2_enabled = True
        self.tier_3_enabled = True
        self.auto_background_sync = True
        self.max_memory_size_tier_1 = 10000  # bytes
        self.background_tasks = set()
        
        self.initialized = False
    
    async def initialize(self, google_service: Optional[GoogleADKMemoryService] = None,
                        stm_service: Optional[STMService] = None,
                        ltm_service: Optional[LTMService] = None,
                        shuttle: Optional[MemoryShuttle] = None):
        """Initialize the hybrid orchestrator with available services"""
        self.google_service = google_service
        self.stm_service = stm_service
        self.ltm_service = ltm_service
        self.shuttle = shuttle
        
        # Initialize services
        if self.google_service:
            google_ready = await self.google_service.initialize()
            if not google_ready:
                logger.warning("Google ADK service initialization failed - Tier 1 disabled")
                self.tier_1_enabled = False
        else:
            self.tier_1_enabled = False
            
        if not self.stm_service:
            self.tier_2_enabled = False
            
        if not self.ltm_service:
            self.tier_3_enabled = False
        
        self.initialized = True
        
        logger.info("🔗 Hybrid Memory Orchestrator initialized", extra={
            "tier_1_google_adk": self.tier_1_enabled,
            "tier_2_jean_stm": self.tier_2_enabled, 
            "tier_3_jean_v2": self.tier_3_enabled,
            "background_sync": self.auto_background_sync
        })
    
    def _should_use_tier_1(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> bool:
        """Determine if memory should use Tier 1 (Google ADK)"""
        if not self.tier_1_enabled:
            return False
            
        # Check memory size
        if len(content.encode('utf-8')) > self.max_memory_size_tier_1:
            return False
            
        # Check user activity pattern (future enhancement)
        # For now, always use Tier 1 if available
        return True
    
    def _update_performance_stats(self, tier: MemoryTier, execution_time_ms: float):
        """Update performance statistics for a tier"""
        stats = self.tier_performance[tier]
        stats["total_calls"] += 1
        stats["total_time_ms"] += execution_time_ms
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["total_calls"]
    
    async def add_memory_hybrid(self, content: Union[str, List], user_id: str, 
                               metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add memory with intelligent tier routing"""
        if not self.initialized:
            raise Exception("Hybrid orchestrator not initialized")
            
        content_str = content if isinstance(content, str) else str(content)
        start_time = time.time()
        
        # Tier 1: Google ADK (Instant)
        if self._should_use_tier_1(content_str, user_id, metadata):
            try:
                tier_1_start = time.time()
                google_result = await self.google_service.add_memory_to_google_adk(
                    content_str, user_id, metadata
                )
                tier_1_time = (time.time() - tier_1_start) * 1000
                self._update_performance_stats(MemoryTier.TIER_1_GOOGLE_ADK, tier_1_time)
                
                if google_result:
                    # Background sync to other tiers
                    if self.auto_background_sync:
                        task = asyncio.create_task(
                            self._background_sync(content_str, user_id, metadata, google_result)
                        )
                        self.background_tasks.add(task)
                        task.add_done_callback(self.background_tasks.discard)
                    
                    total_time = (time.time() - start_time) * 1000
                    
                    logger.info("🔗 Hybrid memory added (Tier 1)", extra={
                        "operation": "add_memory_hybrid",
                        "user_id": user_id,
                        "tier": "tier_1_google_adk",
                        "execution_time_ms": total_time,
                        "tier_1_time_ms": tier_1_time,
                        "memory_size_bytes": len(content_str),
                        "background_sync": self.auto_background_sync
                    })
                    
                    return google_result
            except Exception as e:
                logger.error(f"Tier 1 (Google ADK) failed, falling back: {e}")
        
        # Fallback to Tier 2: Jean V3 STM
        if self.tier_2_enabled:
            try:
                tier_2_start = time.time()
                stm_memory = await self.stm_service.add_memory(
                    content=content_str,
                    user_id=user_id,
                    metadata=metadata
                )
                tier_2_time = (time.time() - tier_2_start) * 1000
                self._update_performance_stats(MemoryTier.TIER_2_JEAN_STM, tier_2_time)
                
                # Background sync to Tier 3
                if self.auto_background_sync and self.tier_3_enabled and self.shuttle:
                    task = asyncio.create_task(
                        self.shuttle.queue_for_upload(user_id, stm_memory.id)
                    )
                    self.background_tasks.add(task)
                    task.add_done_callback(self.background_tasks.discard)
                
                total_time = (time.time() - start_time) * 1000
                
                logger.info("🔗 Hybrid memory added (Tier 2)", extra={
                    "operation": "add_memory_hybrid",
                    "user_id": user_id,
                    "tier": "tier_2_jean_stm",
                    "execution_time_ms": total_time,
                    "tier_2_time_ms": tier_2_time,
                    "memory_id": stm_memory.id
                })
                
                return stm_memory.to_v2_format()
                
            except Exception as e:
                logger.error(f"Tier 2 (Jean STM) failed, falling back: {e}")
        
        # Final fallback to Tier 3: Jean V2 Production
        if self.tier_3_enabled:
            try:
                tier_3_start = time.time()
                ltm_result = await self.ltm_service.upload_memory(
                    content=content_str,
                    user_id=user_id,
                    metadata=metadata
                )
                tier_3_time = (time.time() - tier_3_start) * 1000
                self._update_performance_stats(MemoryTier.TIER_3_JEAN_V2, tier_3_time)
                
                total_time = (time.time() - start_time) * 1000
                
                logger.info("🔗 Hybrid memory added (Tier 3)", extra={
                    "operation": "add_memory_hybrid",
                    "user_id": user_id,
                    "tier": "tier_3_jean_v2",
                    "execution_time_ms": total_time,
                    "tier_3_time_ms": tier_3_time
                })
                
                return ltm_result
                
            except Exception as e:
                logger.error(f"All tiers failed for memory addition: {e}")
                raise Exception("Failed to add memory to any tier")
        
        raise Exception("No available memory tiers")
    
    async def search_memory_hybrid(self, query: str, user_id: str, 
                                  limit: int = 10) -> Dict[str, Any]:
        """Search across all tiers with intelligent result merging"""
        if not self.initialized:
            raise Exception("Hybrid orchestrator not initialized")
            
        start_time = time.time()
        all_results = []
        tier_results = {}
        
        # Parallel search across all available tiers
        search_tasks = []
        
        # Tier 1: Google ADK
        if self.tier_1_enabled:
            search_tasks.append(self._search_tier_1(query, user_id, limit))
        
        # Tier 2: Jean V3 STM
        if self.tier_2_enabled:
            search_tasks.append(self._search_tier_2(query, user_id, limit))
        
        # Tier 3: Jean V2 Production
        if self.tier_3_enabled:
            search_tasks.append(self._search_tier_3(query, user_id, limit))
        
        # Execute all searches in parallel
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Search failed for tier {i+1}: {result}")
                    continue
                    
                tier_name, memories, execution_time = result
                tier_results[tier_name] = {
                    "memories": memories,
                    "count": len(memories),
                    "execution_time_ms": execution_time
                }
                all_results.extend(memories)
        
        # Intelligent result merging and ranking
        merged_results = self._merge_and_rank_results(all_results, query)
        
        # Limit final results
        final_results = merged_results[:limit]
        
        total_time = (time.time() - start_time) * 1000
        
        logger.info("🔗 Hybrid memory search completed", extra={
            "operation": "search_memory_hybrid",
            "user_id": user_id,
            "query": query,
            "total_execution_time_ms": total_time,
            "total_results": len(final_results),
            "tier_results": {k: v["count"] for k, v in tier_results.items()}
        })
        
        return {
            "memories": final_results,
            "total": len(final_results),
            "source": "hybrid",
            "execution_time_ms": total_time,
            "tier_breakdown": tier_results
        }
    
    async def _search_tier_1(self, query: str, user_id: str, limit: int) -> tuple:
        """Search Tier 1 (Google ADK)"""
        start_time = time.time()
        try:
            memories = await self.google_service.search_google_memories(query, user_id, limit)
            execution_time = (time.time() - start_time) * 1000
            self._update_performance_stats(MemoryTier.TIER_1_GOOGLE_ADK, execution_time)
            return ("tier_1_google_adk", memories, execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tier 1 search failed: {e}")
            return ("tier_1_google_adk", [], execution_time)
    
    async def _search_tier_2(self, query: str, user_id: str, limit: int) -> tuple:
        """Search Tier 2 (Jean STM)"""
        start_time = time.time()
        try:
            memories = await self.stm_service.search_memories(query, user_id, limit)
            execution_time = (time.time() - start_time) * 1000
            self._update_performance_stats(MemoryTier.TIER_2_JEAN_STM, execution_time)
            return ("tier_2_jean_stm", memories, execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tier 2 search failed: {e}")
            return ("tier_2_jean_stm", [], execution_time)
    
    async def _search_tier_3(self, query: str, user_id: str, limit: int) -> tuple:
        """Search Tier 3 (Jean V2)"""
        start_time = time.time()
        try:
            memories = await self.ltm_service.search_memories(query, user_id, limit)
            execution_time = (time.time() - start_time) * 1000
            self._update_performance_stats(MemoryTier.TIER_3_JEAN_V2, execution_time)
            return ("tier_3_jean_v2", memories, execution_time)
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tier 3 search failed: {e}")
            return ("tier_3_jean_v2", [], execution_time)
    
    def _merge_and_rank_results(self, all_results: List[Dict], query: str) -> List[Dict]:
        """Intelligent result merging and ranking"""
        # Deduplicate by content
        seen_content = set()
        unique_results = []
        
        for memory in all_results:
            content = memory.get("content", "")
            if content and content not in seen_content:
                seen_content.add(content)
                unique_results.append(memory)
        
        # Rank by relevance score (if available) and tier priority
        def rank_key(memory):
            score = memory.get("score", 0.0)
            tier_bonus = 0.0
            
            # Give slight bonus to higher tiers (more recent/relevant)
            source = memory.get("metadata", {}).get("source", "")
            if source == "google_adk":
                tier_bonus = 0.1
            elif source == "jean_v3_stm":
                tier_bonus = 0.05
            
            return score + tier_bonus
        
        unique_results.sort(key=rank_key, reverse=True)
        return unique_results
    
    async def _background_sync(self, content: str, user_id: str, metadata: Optional[Dict], 
                              google_result: Dict):
        """Background synchronization to lower tiers"""
        try:
            # Sync to Tier 2 (STM)
            if self.tier_2_enabled:
                stm_metadata = {**(metadata or {}), "google_adk_id": google_result.get("id")}
                await self.stm_service.add_memory(content, user_id, stm_metadata)
            
            # Sync to Tier 3 (LTM) via shuttle
            if self.tier_3_enabled and self.shuttle:
                ltm_metadata = {**(metadata or {}), "google_adk_id": google_result.get("id")}
                await self.ltm_service.upload_memory(content, user_id, ltm_metadata)
            
            logger.debug(f"Background sync completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Background sync failed: {e}")
    
    async def get_memory_by_id(self, memory_id: str, user_id: str) -> Optional[Dict]:
        """Get memory by ID from appropriate tier"""
        # Try to determine tier from ID prefix
        if "google" in memory_id.lower() and self.tier_1_enabled:
            return await self.google_service.get_memory_by_id(memory_id, user_id)
        elif memory_id.startswith("stm_") and self.tier_2_enabled:
            memory = await self.stm_service.get_memory(memory_id)
            if memory and memory.user_id == user_id:
                return memory.to_v2_format()
        elif self.tier_3_enabled:
            return await self.ltm_service.get_memory(memory_id, user_id)
        
        return None
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from all tiers"""
        success = False
        
        # Try all tiers
        if self.tier_1_enabled:
            try:
                if await self.google_service.delete_memory(memory_id, user_id):
                    success = True
            except Exception as e:
                logger.error(f"Failed to delete from Tier 1: {e}")
        
        if self.tier_2_enabled:
            try:
                memory = await self.stm_service.get_memory(memory_id)
                if memory and memory.user_id == user_id:
                    if await self.stm_service.delete_memory(memory_id):
                        success = True
            except Exception as e:
                logger.error(f"Failed to delete from Tier 2: {e}")
        
        if self.tier_3_enabled:
            try:
                if await self.ltm_service.delete_memory(memory_id, user_id):
                    success = True
            except Exception as e:
                logger.error(f"Failed to delete from Tier 3: {e}")
        
        return success
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "service": "hybrid_memory_orchestrator",
            "initialized": self.initialized,
            "tiers_enabled": {
                "tier_1_google_adk": self.tier_1_enabled,
                "tier_2_jean_stm": self.tier_2_enabled,
                "tier_3_jean_v2": self.tier_3_enabled
            },
            "performance": {
                tier.name.lower(): stats 
                for tier, stats in self.tier_performance.items()
            },
            "configuration": {
                "auto_background_sync": self.auto_background_sync,
                "max_memory_size_tier_1": self.max_memory_size_tier_1
            },
            "background_tasks": len(self.background_tasks)
        }
    
    async def force_sync_user(self, user_id: str) -> Dict[str, Any]:
        """Force synchronization of user memories across all tiers"""
        sync_results = {"tier_1_to_2": 0, "tier_1_to_3": 0, "tier_2_to_3": 0}
        
        # This would be enhanced with actual sync logic
        # For now, just trigger existing shuttle sync
        if self.shuttle:
            shuttle_result = await self.shuttle.force_upload_user_memories(user_id)
            sync_results["tier_2_to_3"] = shuttle_result.get("uploaded_count", 0)
        
        return sync_results

# Global instance
hybrid_orchestrator = HybridMemoryOrchestrator()