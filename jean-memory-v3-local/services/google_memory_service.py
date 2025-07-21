"""
Google ADK Memory Service Integration
Provides Google Cloud Memory Bank integration for Jean Memory V3 Hybrid
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from google.cloud import aiplatform
from google.ai import generativelanguage as glm
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError

from config import get_google_cloud_config

logger = logging.getLogger(__name__)

class GoogleADKMemoryService:
    """Google ADK Memory Service integration for Tier 1 memory operations"""
    
    def __init__(self):
        self.config = get_google_cloud_config()
        self.client = None
        self.memory_bank_id = None
        self.project_id = None
        self.location = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize Google ADK Memory Bank client"""
        try:
            if not self.config.get("enabled", False):
                logger.warning("Google ADK not enabled in configuration")
                return False
                
            # Initialize Vertex AI
            self.project_id = self.config["project_id"]
            self.location = self.config["location"]
            self.memory_bank_id = self.config["memory_bank_id"]
            
            # Set up credentials if path provided
            credentials_path = self.config.get("credentials_path")
            if credentials_path:
                import os
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            
            # Get default credentials
            try:
                credentials, project = default()
                if project:
                    self.project_id = project
            except DefaultCredentialsError:
                logger.warning("Google Cloud credentials not found - ADK will be disabled")
                return False
            
            # Initialize Vertex AI
            aiplatform.init(
                project=self.project_id,
                location=self.location,
                credentials=credentials
            )
            
            # Initialize Memory Bank client
            self.client = glm.MemoryServiceClient()
            
            self.initialized = True
            logger.info(f"🔗 Google ADK Memory Service initialized", extra={
                "project_id": self.project_id,
                "location": self.location,
                "memory_bank_id": self.memory_bank_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Google ADK Memory Service: {e}")
            return False
    
    def _get_user_memory_prefix(self, user_id: str) -> str:
        """Get user-specific memory prefix for isolation"""
        return f"jean_v3_user_{user_id}"
    
    def convert_to_google_format(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Dict:
        """Convert Jean Memory format to Google ADK Memory Bank format"""
        if metadata is None:
            metadata = {}
            
        google_memory = {
            "display_name": f"{self._get_user_memory_prefix(user_id)}_{int(time.time())}",
            "content": content,
            "metadata": {
                "user_id": user_id,
                "source": "jean_memory_v3",
                "tier": "google_adk",
                "created_at": datetime.utcnow().isoformat(),
                **metadata
            }
        }
        
        return google_memory
    
    def convert_from_google_format(self, google_memory: Dict) -> Dict:
        """Convert Google ADK Memory Bank format to Jean Memory format"""
        metadata = google_memory.get("metadata", {})
        
        jean_memory = {
            "id": google_memory.get("name", ""),
            "content": google_memory.get("content", ""),
            "user_id": metadata.get("user_id", ""),
            "metadata": {
                "source": "google_adk",
                "tier": "tier_1",
                "google_memory_id": google_memory.get("name", ""),
                "created_at": metadata.get("created_at"),
                **{k: v for k, v in metadata.items() if k not in ["user_id", "source", "tier", "created_at"]}
            },
            "timestamp": metadata.get("created_at", datetime.utcnow().isoformat())
        }
        
        return jean_memory
    
    async def add_memory_to_google_adk(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> Optional[Dict]:
        """Add memory to Google Memory Bank (Tier 1 - fastest)"""
        if not self.initialized:
            await self.initialize()
            if not self.initialized:
                return None
        
        start_time = time.time()
        
        try:
            # Convert to Google format
            google_memory = self.convert_to_google_format(content, user_id, metadata)
            
            # Create memory in Google Memory Bank
            parent = f"projects/{self.project_id}/locations/{self.location}/memoryBanks/{self.memory_bank_id}"
            
            memory_request = glm.CreateMemoryRequest(
                parent=parent,
                memory=glm.Memory(
                    display_name=google_memory["display_name"],
                    content=google_memory["content"],
                    metadata=google_memory["metadata"]
                )
            )
            
            # Execute the request
            response = self.client.create_memory(request=memory_request)
            
            # Convert back to Jean format
            result = self.convert_from_google_format({
                "name": response.name,
                "content": response.content,
                "metadata": response.metadata or {}
            })
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info("🔗 Google ADK memory added", extra={
                "operation": "add_memory",
                "user_id": user_id,
                "tier": "google_adk",
                "execution_time_ms": execution_time_ms,
                "memory_size_bytes": len(content),
                "google_memory_id": response.name
            })
            
            return result
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Google ADK memory addition failed: {e}", extra={
                "operation": "add_memory",
                "user_id": user_id,
                "execution_time_ms": execution_time_ms,
                "error": str(e)
            })
            return None
    
    async def search_google_memories(self, query: str, user_id: str, limit: int = 10) -> List[Dict]:
        """Search Google Memory Bank"""
        if not self.initialized:
            await self.initialize()
            if not self.initialized:
                return []
        
        start_time = time.time()
        
        try:
            # Prepare search request
            parent = f"projects/{self.project_id}/locations/{self.location}/memoryBanks/{self.memory_bank_id}"
            user_prefix = self._get_user_memory_prefix(user_id)
            
            # Create search filter for user isolation
            filter_str = f'metadata.user_id="{user_id}"'
            
            search_request = glm.SearchMemoriesRequest(
                parent=parent,
                query=query,
                filter=filter_str,
                page_size=limit
            )
            
            # Execute search
            response = self.client.search_memories(request=search_request)
            
            # Convert results to Jean format
            results = []
            for memory in response.memories:
                jean_memory = self.convert_from_google_format({
                    "name": memory.name,
                    "content": memory.content,
                    "metadata": memory.metadata or {}
                })
                results.append(jean_memory)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.info("🔗 Google ADK memory search completed", extra={
                "operation": "search_memories",
                "user_id": user_id,
                "tier": "google_adk",
                "execution_time_ms": execution_time_ms,
                "query": query,
                "results_count": len(results)
            })
            
            return results
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Google ADK memory search failed: {e}", extra={
                "operation": "search_memories",
                "user_id": user_id,
                "execution_time_ms": execution_time_ms,
                "query": query,
                "error": str(e)
            })
            return []
    
    async def get_memory_by_id(self, memory_id: str, user_id: str) -> Optional[Dict]:
        """Get specific memory by Google ADK ID"""
        if not self.initialized:
            await self.initialize()
            if not self.initialized:
                return None
        
        try:
            get_request = glm.GetMemoryRequest(name=memory_id)
            response = self.client.get_memory(request=get_request)
            
            # Verify user access
            metadata = response.metadata or {}
            if metadata.get("user_id") != user_id:
                logger.warning(f"Access denied: user {user_id} attempted to access memory {memory_id}")
                return None
            
            return self.convert_from_google_format({
                "name": response.name,
                "content": response.content,
                "metadata": metadata
            })
            
        except Exception as e:
            logger.error(f"Failed to get Google ADK memory {memory_id}: {e}")
            return None
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """Delete memory from Google Memory Bank"""
        if not self.initialized:
            await self.initialize()
            if not self.initialized:
                return False
        
        try:
            # First verify user access
            memory = await self.get_memory_by_id(memory_id, user_id)
            if not memory:
                return False
            
            delete_request = glm.DeleteMemoryRequest(name=memory_id)
            self.client.delete_memory(request=delete_request)
            
            logger.info(f"🔗 Google ADK memory deleted", extra={
                "operation": "delete_memory",
                "user_id": user_id,
                "memory_id": memory_id
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Google ADK memory {memory_id}: {e}")
            return False
    
    async def get_performance_stats(self) -> Dict:
        """Get performance statistics for monitoring"""
        return {
            "service": "google_adk_memory",
            "tier": 1,
            "initialized": self.initialized,
            "project_id": self.project_id,
            "location": self.location,
            "memory_bank_id": self.memory_bank_id,
            "target_latency_ms": 5,
            "status": "active" if self.initialized else "disabled"
        }

# Global instance
google_memory_service = GoogleADKMemoryService()