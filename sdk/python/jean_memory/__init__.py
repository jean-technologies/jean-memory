"""
Jean Memory Python SDK
Add long-term memory to your Python agents and backend services

Example usage:
    from jean_memory import JeanMemoryClient
    
    client = JeanMemoryClient(api_key="jean_sk_...")
    client.store_memory("I prefer morning meetings")
    memories = client.retrieve_memories("meeting preferences")
"""

from .client import JeanMemoryClient, JeanMemoryError
from .auth import JeanMemoryAuth

# Alias for documentation compatibility  
from .client import JeanMemoryClient as JeanClient
from .models import (
    Memory,
    MemorySearchResult,
    MemoryCreateRequest,
    MemoryCreateResponse,
    UserInfo,
    APIResponse,
    HealthStatus,
    MemoryListResponse,
    MemoryStatus,
    ContextResponse
)

__version__ = "1.2.9"
__author__ = "Jean Memory"
__email__ = "support@jeanmemory.com"

__all__ = [
    # Core client
    "JeanMemoryClient",
    "JeanMemoryError",
    
    # Documentation compatibility alias
    "JeanClient", 
    
    # Authentication
    "JeanMemoryAuth",
    
    # Data models
    "Memory",
    "MemorySearchResult", 
    "MemoryCreateRequest",
    "MemoryCreateResponse",
    "UserInfo",
    "APIResponse",
    "HealthStatus",
    "MemoryListResponse",
    "MemoryStatus",
    "ContextResponse",
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__"
]