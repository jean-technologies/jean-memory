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
from .models import (
    Memory,
    MemorySearchResult,
    MemoryCreateRequest,
    MemoryCreateResponse,
    UserInfo,
    APIResponse,
    HealthStatus,
    MemoryListResponse,
    MemoryStatus
)

__version__ = "1.0.1"
__author__ = "Jean Memory"
__email__ = "support@jeanmemory.com"

__all__ = [
    # Core client
    "JeanMemoryClient",
    "JeanMemoryError",
    
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
    
    # Package metadata
    "__version__",
    "__author__",
    "__email__"
]