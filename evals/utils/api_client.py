"""
API Client for Jean Memory Evaluation Framework
Supports both local function calls and production HTTP API calls
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

class JeanMemoryClient(ABC):
    """Abstract base class for Jean Memory clients"""
    
    @abstractmethod
    async def jean_memory_call(self, user_message: str, is_new_conversation: bool, 
                              needs_context: bool, user_id: str, client_name: str) -> str:
        """Make a jean_memory call"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check if the client is healthy and can make calls"""
        pass

class LocalJeanMemoryClient(JeanMemoryClient):
    """Local client that calls Jean Memory functions directly"""
    
    def __init__(self):
        self.name = "Local Function Calls"
        
    async def jean_memory_call(self, user_message: str, is_new_conversation: bool, 
                              needs_context: bool, user_id: str, client_name: str) -> str:
        """Call jean_memory function directly (current behavior)"""
        try:
            # Import here to avoid circular dependencies
            import sys
            from pathlib import Path
            
            # Add API path
            current_dir = Path(__file__).parent.parent
            project_root = current_dir.parent
            sys.path.insert(0, str(project_root / "openmemory" / "api"))
            
            from app.tools.orchestration import jean_memory
            from app.context import user_id_var, client_name_var, background_tasks_var
            from fastapi import BackgroundTasks
            
            # Set up context variables (simulating FastAPI context)
            user_token = user_id_var.set(user_id)
            client_token = client_name_var.set(client_name)
            bg_tasks = BackgroundTasks()
            bg_token = background_tasks_var.set(bg_tasks)
            
            try:
                # Call the actual jean_memory function
                context = await jean_memory(
                    user_message=user_message,
                    is_new_conversation=is_new_conversation,
                    needs_context=needs_context
                )
                return context
            finally:
                # Reset context variables
                user_id_var.reset(user_token)
                client_name_var.reset(client_token)
                background_tasks_var.reset(bg_token)
                
        except Exception as e:
            logger.error(f"Local jean_memory call failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if local functions are available"""
        try:
            # Try to import the main components
            import sys
            from pathlib import Path
            
            current_dir = Path(__file__).parent.parent
            project_root = current_dir.parent
            sys.path.insert(0, str(project_root / "openmemory" / "api"))
            
            from app.tools.orchestration import jean_memory
            from app.mcp_orchestration import get_smart_orchestrator
            
            # Try to get orchestrator
            orchestrator = get_smart_orchestrator()
            
            return {
                "client_type": "local",
                "status": "healthy",
                "jean_memory_available": True,
                "orchestrator_available": True,
                "description": "Local function calls are working"
            }
        except Exception as e:
            return {
                "client_type": "local", 
                "status": "unhealthy",
                "error": str(e),
                "jean_memory_available": False,
                "orchestrator_available": False,
                "description": "Local function calls failed"
            }

class ProductionAPIClient(JeanMemoryClient):
    """Production client that makes HTTP API calls to Jean Memory server"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.name = "Production HTTP API"
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def jean_memory_call(self, user_message: str, is_new_conversation: bool, 
                              needs_context: bool, user_id: str, client_name: str) -> str:
        """Make HTTP API call to jean_memory endpoint"""
        try:
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": f"JeanMemoryEvalFramework/{client_name}"
            }
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Prepare request body
            payload = {
                "user_message": user_message,
                "is_new_conversation": is_new_conversation,
                "needs_context": needs_context,
                "user_id": user_id,
                "client_name": client_name
            }
            
            # Make API call
            response = await self.client.post(
                f"{self.base_url}/api/v1/jean_memory",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("context", "")
            else:
                error_detail = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"API call failed: {error_detail}")
                raise Exception(f"API call failed: {error_detail}")
                
        except httpx.TimeoutException:
            raise Exception("API call timed out")
        except httpx.RequestError as e:
            raise Exception(f"API request error: {e}")
        except Exception as e:
            logger.error(f"Production API jean_memory call failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if production API is available"""
        try:
            headers = {"User-Agent": "JeanMemoryEvalFramework/HealthCheck"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            response = await self.client.get(
                f"{self.base_url}/health",
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "client_type": "production_api",
                    "status": "healthy",
                    "base_url": self.base_url,
                    "api_available": True,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "description": "Production API is responding"
                }
            else:
                return {
                    "client_type": "production_api",
                    "status": "unhealthy", 
                    "base_url": self.base_url,
                    "api_available": False,
                    "http_status": response.status_code,
                    "description": f"Production API returned {response.status_code}"
                }
                
        except Exception as e:
            return {
                "client_type": "production_api",
                "status": "unhealthy",
                "base_url": self.base_url,
                "api_available": False,
                "error": str(e),
                "description": "Production API connection failed"
            }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class JeanMemoryClientFactory:
    """Factory for creating Jean Memory clients"""
    
    @staticmethod
    def create_client(client_type: str, **kwargs) -> JeanMemoryClient:
        """Create a client based on type"""
        if client_type.lower() == "local":
            return LocalJeanMemoryClient()
        elif client_type.lower() == "production":
            base_url = kwargs.get("base_url")
            if not base_url:
                raise ValueError("base_url is required for production client")
            api_key = kwargs.get("api_key")
            return ProductionAPIClient(base_url, api_key)
        else:
            raise ValueError(f"Unknown client type: {client_type}")

# Configuration helper
class ClientConfig:
    """Configuration for different Jean Memory clients"""
    
    @staticmethod
    def get_local_config() -> Dict[str, Any]:
        """Get configuration for local client"""
        return {
            "client_type": "local",
            "description": "Direct function calls to local Jean Memory system",
            "use_case": "Development, debugging, fast iteration"
        }
    
    @staticmethod
    def get_production_config(base_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for production client"""
        return {
            "client_type": "production",
            "base_url": base_url,
            "api_key": api_key,
            "description": "HTTP API calls to production Jean Memory server",
            "use_case": "Production testing, realistic client simulation"
        }
    
    @staticmethod
    def get_claude_production_config() -> Dict[str, Any]:
        """Get configuration for Claude production testing"""
        return ClientConfig.get_production_config(
            base_url="https://api.jean-memory.com",  # Replace with actual production URL
            api_key=None  # Would need actual API key
        )

# Async context manager for client lifecycle
class JeanMemoryClientManager:
    """Manages Jean Memory client lifecycle"""
    
    def __init__(self, client: JeanMemoryClient):
        self.client = client
    
    async def __aenter__(self):
        # Perform any setup if needed
        health = await self.client.health_check()
        if health.get("status") != "healthy":
            logger.warning(f"Client health check warning: {health}")
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        if hasattr(self.client, 'close'):
            await self.client.close()