"""
LTM (Long-Term Memory) Service for Jean Memory V3
Integrates with Jean Memory V2 production system (Qdrant + Neo4j Aura + Supabase)
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import httpx
import json

from config import get_config

logger = logging.getLogger(__name__)

class LTMService:
    """Long-Term Memory service integrating with V2 production system"""
    
    def __init__(self):
        self.config = get_config()
        
        # V2 Production API configuration
        self.base_url = self.config.jean_memory_v2_api_url or "https://api.jeanmemory.com"
        self.api_key = self.config.jean_memory_v2_api_key
        
        # HTTP client for V2 API calls
        self.client: Optional[httpx.AsyncClient] = None
        self.is_initialized = False
        
        # Rate limiting and retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.request_timeout = 30.0
        
    async def initialize(self):
        """Initialize LTM connection to V2 production system"""
        try:
            logger.info("☁️  Initializing LTM (Long-Term Memory) connection...")
            
            if not self.api_key:
                logger.warning("⚠️  No LTM API key configured - LTM features disabled")
                return
            
            # Initialize HTTP client with proper headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Jean-Memory-V3-STM/1.0"
            }
            
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.request_timeout,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
            
            # Test connection
            await self._test_connection()
            
            self.is_initialized = True
            logger.info("✅ LTM connection established with V2 production system")
            
        except Exception as e:
            logger.error(f"❌ LTM initialization failed: {e}")
            # Don't raise - allow V3 to work without LTM
            
    async def _test_connection(self):
        """Test connection to V2 production API"""
        try:
            response = await self.client.get("/health")
            if response.status_code != 200:
                raise Exception(f"LTM health check failed: {response.status_code}")
                
            logger.info("✅ LTM connection test successful")
            
        except Exception as e:
            logger.error(f"❌ LTM connection test failed: {e}")
            raise
    
    async def upload_memory(self,
                           content: Union[str, List[str], List[Dict]],
                           user_id: str,
                           app_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Upload memory to LTM (V2 production system)"""
        if not self.is_ready():
            logger.warning("LTM not available for upload")
            return None
            
        try:
            # Prepare V2 API request format
            request_data = {
                "messages": content,
                "user_id": user_id,
                "metadata": {
                    **(metadata or {}),
                    "source": "jean_memory_v3_stm",
                    "app_id": app_id or "jean_memory_v3_stm",
                    "uploaded_at": datetime.now().isoformat()
                }
            }
            
            # Upload to V2 production system
            response = await self._make_request(
                "POST",
                "/memories/",
                json=request_data
            )
            
            if response and response.get("id"):
                logger.info(f"✅ Uploaded memory to LTM: {response['id']}")
                return response
            else:
                logger.error("❌ LTM upload failed - no memory ID returned")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to upload memory to LTM: {e}")
            return None
    
    async def search_memories(self,
                             query: str,
                             user_id: str,
                             limit: int = 10) -> List[Dict[str, Any]]:
        """Search LTM memories via V2 production API"""
        if not self.is_ready():
            return []
            
        try:
            # Use V2 search endpoint
            response = await self._make_request(
                "GET",
                "/memories/",
                params={
                    "user_id": user_id,
                    "query": query,
                    "limit": limit,
                    "include_categories": True
                }
            )
            
            if response and "memories" in response:
                memories = response["memories"]
                
                # Add LTM source marker
                for memory in memories:
                    if "metadata_" not in memory:
                        memory["metadata_"] = {}
                    memory["metadata_"]["source"] = "ltm"
                
                logger.info(f"🔍 LTM search found {len(memories)} memories")
                return memories
            
            return []
            
        except Exception as e:
            logger.error(f"❌ LTM search failed: {e}")
            return []
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get specific memory from LTM"""
        if not self.is_ready():
            return None
            
        try:
            response = await self._make_request(
                "GET",
                f"/memories/{memory_id}",
                params={"user_id": user_id}
            )
            
            if response:
                # Add LTM source marker
                if "metadata_" not in response:
                    response["metadata_"] = {}
                response["metadata_"]["source"] = "ltm"
                
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get LTM memory {memory_id}: {e}")
            return None
    
    async def get_user_memories(self,
                               user_id: str,
                               limit: int = 50,
                               offset: int = 0) -> List[Dict[str, Any]]:
        """Get user memories from LTM"""
        if not self.is_ready():
            return []
            
        try:
            response = await self._make_request(
                "GET",
                "/memories/",
                params={
                    "user_id": user_id,
                    "limit": limit,
                    "offset": offset,
                    "state": "active"
                }
            )
            
            if response and "memories" in response:
                memories = response["memories"]
                
                # Add LTM source marker
                for memory in memories:
                    if "metadata_" not in memory:
                        memory["metadata_"] = {}
                    memory["metadata_"]["source"] = "ltm"
                
                return memories
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get LTM user memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from LTM"""
        if not self.is_ready():
            return False
            
        try:
            response = await self._make_request(
                "DELETE",
                f"/memories/{memory_id}",
                params={"user_id": user_id}
            )
            
            success = response is not None
            if success:
                logger.info(f"✅ Deleted LTM memory: {memory_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to delete LTM memory {memory_id}: {e}")
            return False
    
    async def get_hot_memories(self,
                              user_id: str,
                              limit: int = 20) -> List[Dict[str, Any]]:
        """Get high-salience memories recommended for STM preloading"""
        if not self.is_ready():
            return []
            
        try:
            # Use V2 API to get recent and frequently accessed memories
            response = await self._make_request(
                "GET",
                "/memories/",
                params={
                    "user_id": user_id,
                    "limit": limit,
                    "sort": "relevance",  # V2 API sorts by usage and recency
                    "state": "active"
                }
            )
            
            if response and "memories" in response:
                hot_memories = response["memories"]
                
                # Add LTM source marker and hot flag
                for memory in hot_memories:
                    if "metadata_" not in memory:
                        memory["metadata_"] = {}
                    memory["metadata_"]["source"] = "ltm"
                    memory["metadata_"]["is_hot"] = True
                
                logger.info(f"🔥 Retrieved {len(hot_memories)} hot memories from LTM")
                return hot_memories
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get hot memories from LTM: {e}")
            return []
    
    async def get_life_narrative(self, user_id: str) -> Optional[str]:
        """Get user's life narrative from LTM"""
        if not self.is_ready():
            return None
            
        try:
            response = await self._make_request(
                "GET",
                "/memories/narrative",
                params={"user_id": user_id}
            )
            
            if response and "narrative" in response:
                return response["narrative"]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get life narrative from LTM: {e}")
            return None
    
    async def get_categories(self, user_id: str) -> List[str]:
        """Get user's memory categories from LTM"""
        if not self.is_ready():
            return []
            
        try:
            response = await self._make_request(
                "GET",
                "/memories/categories",
                params={"user_id": user_id}
            )
            
            if response and "categories" in response:
                return response["categories"]
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get categories from LTM: {e}")
            return []
    
    async def _make_request(self,
                           method: str,
                           endpoint: str,
                           params: Optional[Dict] = None,
                           json: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to V2 API with retry logic"""
        if not self.client:
            return None
            
        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    # Not found - return None
                    return None
                else:
                    # Server error - retry
                    logger.warning(f"LTM API error {response.status_code}, attempt {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        logger.error(f"LTM API failed after {self.max_retries} attempts")
                        return None
                        
            except Exception as e:
                logger.warning(f"LTM request failed, attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"LTM request failed after {self.max_retries} attempts: {e}")
                    return None
        
        return None
    
    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get LTM statistics"""
        if not self.is_ready():
            return {
                "connected": False,
                "error": "LTM not available",
                "source": "ltm"
            }
            
        try:
            # Get basic stats from V2 API
            params = {}
            if user_id:
                params["user_id"] = user_id
                
            response = await self._make_request(
                "GET",
                "/memories/stats",
                params=params
            )
            
            if response:
                return {
                    **response,
                    "connected": True,
                    "source": "ltm"
                }
            
            return {
                "connected": True,
                "total_memories": 0,
                "source": "ltm"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get LTM stats: {e}")
            return {
                "connected": False,
                "error": str(e),
                "source": "ltm"
            }
    
    def is_ready(self) -> bool:
        """Check if LTM service is ready"""
        return self.is_initialized and self.client is not None
    
    async def cleanup(self):
        """Cleanup LTM resources"""
        logger.info("🧹 Cleaning up LTM service...")
        
        if self.client:
            await self.client.aclose()
            self.client = None
        
        logger.info("✅ LTM service cleanup complete")