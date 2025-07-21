"""
Memory Shuttle Layer for Jean Memory V3
Orchestrates intelligent bidirectional memory movement between STM ↔ LTM
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .stm_service import STMService, STMMemory
from .ltm_service import LTMService

logger = logging.getLogger(__name__)

@dataclass
class ShuttleConfig:
    """Configuration for Memory Shuttle operations"""
    # Batch parameters
    batch_size: int = 10
    batch_timeout_seconds: int = 30
    max_batch_size_mb: float = 5.0
    
    # Upload thresholds
    min_salience_score: float = 0.3
    max_pending_uploads: int = 100
    
    # Preload parameters
    preload_hot_memories: int = 20
    preload_interval_minutes: int = 60
    
    # Sync intervals
    upload_interval_seconds: int = 60
    download_interval_seconds: int = 300
    
    # Deduplication
    enable_dedup: bool = True
    dedup_similarity_threshold: float = 0.95

class MemoryShuttle:
    """Memory Shuttle orchestrating STM ↔ LTM synchronization"""
    
    def __init__(self, stm_service: STMService, ltm_service: LTMService):
        self.stm = stm_service
        self.ltm = ltm_service
        self.config = ShuttleConfig()
        
        # Shuttle state
        self.is_running = False
        self.upload_queue: Dict[str, List[str]] = {}  # user_id -> memory_ids
        self.last_upload: Dict[str, datetime] = {}  # user_id -> timestamp
        self.last_preload: Dict[str, datetime] = {}  # user_id -> timestamp
        
        # Background tasks
        self.upload_task: Optional[asyncio.Task] = None
        self.preload_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "uploads_completed": 0,
            "uploads_failed": 0,
            "preloads_completed": 0,
            "bytes_uploaded": 0,
            "bytes_downloaded": 0,
            "dedup_saves": 0
        }
    
    async def start(self):
        """Start the Memory Shuttle background processes"""
        if self.is_running:
            return
            
        logger.info("🚀 Starting Memory Shuttle...")
        
        self.is_running = True
        
        # Start background tasks
        self.upload_task = asyncio.create_task(self._upload_worker())
        self.preload_task = asyncio.create_task(self._preload_worker())
        
        logger.info("✅ Memory Shuttle started - STM ↔ LTM sync active")
    
    async def stop(self):
        """Stop the Memory Shuttle background processes"""
        if not self.is_running:
            return
            
        logger.info("🔄 Stopping Memory Shuttle...")
        
        self.is_running = False
        
        # Cancel background tasks
        if self.upload_task:
            self.upload_task.cancel()
            try:
                await self.upload_task
            except asyncio.CancelledError:
                pass
                
        if self.preload_task:
            self.preload_task.cancel()
            try:
                await self.preload_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Memory Shuttle stopped")
    
    async def queue_for_upload(self, user_id: str, memory_id: str):
        """Queue memory for upload to LTM"""
        if user_id not in self.upload_queue:
            self.upload_queue[user_id] = []
        
        if memory_id not in self.upload_queue[user_id]:
            self.upload_queue[user_id].append(memory_id)
            logger.debug(f"📤 Queued memory for upload: {memory_id}")
    
    async def force_upload_user_memories(self, user_id: str) -> Dict[str, Any]:
        """Force immediate upload of all pending memories for a user"""
        if not self.ltm.is_ready():
            return {"error": "LTM not available", "uploaded": 0}
            
        try:
            # Get upload candidates
            candidates = await self.stm.get_upload_candidates(user_id, limit=100)
            
            uploaded_count = 0
            failed_count = 0
            
            for memory in candidates:
                success = await self._upload_memory(memory)
                if success:
                    uploaded_count += 1
                else:
                    failed_count += 1
            
            logger.info(f"🚀 Force upload completed for {user_id}: {uploaded_count} uploaded, {failed_count} failed")
            
            return {
                "uploaded": uploaded_count,
                "failed": failed_count,
                "total_candidates": len(candidates)
            }
            
        except Exception as e:
            logger.error(f"❌ Force upload failed for {user_id}: {e}")
            return {"error": str(e), "uploaded": 0}
    
    async def preload_hot_memories(self, user_id: str) -> Dict[str, Any]:
        """Preload high-salience memories from LTM to STM"""
        if not self.ltm.is_ready():
            return {"error": "LTM not available", "preloaded": 0}
            
        try:
            # Get hot memories from LTM
            hot_memories = await self.ltm.get_hot_memories(
                user_id, 
                limit=self.config.preload_hot_memories
            )
            
            preloaded_count = 0
            
            for ltm_memory in hot_memories:
                # Check if already in STM
                existing = await self._find_stm_memory_by_content(
                    user_id, 
                    ltm_memory.get("content", "")
                )
                
                if existing:
                    continue  # Already in STM
                
                # Add to STM
                try:
                    stm_memory = await self.stm.add_memory(
                        content=ltm_memory.get("content", ""),
                        user_id=user_id,
                        app_id=ltm_memory.get("app_id"),
                        metadata={
                            **ltm_memory.get("metadata_", {}),
                            "preloaded_from_ltm": True,
                            "ltm_id": ltm_memory.get("id"),
                            "preload_timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    # Mark as already uploaded
                    await self.stm.mark_uploaded(stm_memory.id, ltm_memory.get("id", ""))
                    preloaded_count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to preload memory {ltm_memory.get('id')}: {e}")
            
            # Update preload timestamp
            self.last_preload[user_id] = datetime.now()
            self.stats["preloads_completed"] += 1
            
            logger.info(f"🔥 Preloaded {preloaded_count} hot memories for {user_id}")
            
            return {
                "preloaded": preloaded_count,
                "total_hot": len(hot_memories)
            }
            
        except Exception as e:
            logger.error(f"❌ Hot memory preload failed for {user_id}: {e}")
            return {"error": str(e), "preloaded": 0}
    
    async def _upload_worker(self):
        """Background worker for uploading STM memories to LTM"""
        while self.is_running:
            try:
                # Process each user's upload queue
                for user_id in list(self.upload_queue.keys()):
                    if not self.upload_queue[user_id]:
                        continue
                        
                    # Check if it's time to upload for this user
                    last_upload = self.last_upload.get(user_id)
                    if (last_upload and 
                        datetime.now() - last_upload < timedelta(seconds=self.config.upload_interval_seconds)):
                        continue
                    
                    # Get upload candidates
                    candidates = await self.stm.get_upload_candidates(user_id, self.config.batch_size)
                    
                    if candidates:
                        await self._upload_batch(user_id, candidates)
                
                # Wait before next cycle
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"❌ Upload worker error: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _preload_worker(self):
        """Background worker for preloading hot memories from LTM"""
        while self.is_running:
            try:
                # Check each active user for preload needs
                for user_id in self.stm.user_memories.keys():
                    last_preload = self.last_preload.get(user_id)
                    
                    if (not last_preload or 
                        datetime.now() - last_preload > timedelta(minutes=self.config.preload_interval_minutes)):
                        
                        await self.preload_hot_memories(user_id)
                
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Preload worker error: {e}")
                await asyncio.sleep(300)  # Wait longer on error
    
    async def _upload_batch(self, user_id: str, memories: List[STMMemory]):
        """Upload a batch of memories to LTM"""
        if not self.ltm.is_ready():
            return
            
        try:
            # Apply deduplication if enabled
            if self.config.enable_dedup:
                memories = await self._deduplicate_memories(user_id, memories)
            
            uploaded_count = 0
            
            for memory in memories:
                success = await self._upload_memory(memory)
                if success:
                    uploaded_count += 1
            
            # Update last upload timestamp
            self.last_upload[user_id] = datetime.now()
            
            if uploaded_count > 0:
                logger.info(f"📤 Uploaded batch for {user_id}: {uploaded_count}/{len(memories)} memories")
                
        except Exception as e:
            logger.error(f"❌ Batch upload failed for {user_id}: {e}")
    
    async def _upload_memory(self, memory: STMMemory) -> bool:
        """Upload single memory to LTM"""
        try:
            # Upload to LTM
            ltm_result = await self.ltm.upload_memory(
                content=memory.content,
                user_id=memory.user_id,
                app_id=memory.app_id,
                metadata=memory.metadata
            )
            
            if ltm_result and ltm_result.get("id"):
                # Mark as uploaded in STM
                await self.stm.mark_uploaded(memory.id, ltm_result["id"])
                
                # Update statistics
                self.stats["uploads_completed"] += 1
                self.stats["bytes_uploaded"] += len(memory.content.encode('utf-8'))
                
                return True
            else:
                self.stats["uploads_failed"] += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to upload memory {memory.id}: {e}")
            self.stats["uploads_failed"] += 1
            return False
    
    async def _deduplicate_memories(self, user_id: str, memories: List[STMMemory]) -> List[STMMemory]:
        """Remove duplicate memories before upload"""
        if not memories:
            return memories
            
        try:
            # Get recent LTM memories for comparison
            recent_ltm = await self.ltm.get_user_memories(user_id, limit=50)
            ltm_contents = set(mem.get("content", "") for mem in recent_ltm)
            
            # Filter out duplicates
            unique_memories = []
            for memory in memories:
                if memory.content not in ltm_contents:
                    unique_memories.append(memory)
                else:
                    self.stats["dedup_saves"] += 1
                    logger.debug(f"🔄 Deduplicated memory: {memory.id}")
            
            return unique_memories
            
        except Exception as e:
            logger.error(f"❌ Deduplication failed: {e}")
            return memories  # Return original list on error
    
    async def _find_stm_memory_by_content(self, user_id: str, content: str) -> Optional[STMMemory]:
        """Find STM memory by content"""
        user_memory_ids = self.stm.user_memories.get(user_id, [])
        
        for memory_id in user_memory_ids:
            memory = self.stm.memories.get(memory_id)
            if memory and memory.content == content:
                return memory
        
        return None
    
    async def get_shuttle_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get Memory Shuttle statistics"""
        stats = {
            "is_running": self.is_running,
            "config": {
                "batch_size": self.config.batch_size,
                "upload_interval_seconds": self.config.upload_interval_seconds,
                "preload_interval_minutes": self.config.preload_interval_minutes
            },
            "global_stats": self.stats.copy(),
            "ltm_connected": self.ltm.is_ready()
        }
        
        if user_id:
            # Add user-specific stats
            pending_uploads = len(self.upload_queue.get(user_id, []))
            last_upload = self.last_upload.get(user_id)
            last_preload = self.last_preload.get(user_id)
            
            stats["user_stats"] = {
                "pending_uploads": pending_uploads,
                "last_upload": last_upload.isoformat() if last_upload else None,
                "last_preload": last_preload.isoformat() if last_preload else None
            }
        
        return stats