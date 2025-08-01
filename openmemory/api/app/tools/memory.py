"""
Memory tools main interface.
Provides a clean API for memory operations by importing from modularized components.
"""

# Import from modularized components
from .memory_modules.utils import safe_json_dumps, track_tool_usage
from .memory_modules.search_operations import (
    search_memory, search_memory_v2, ask_memory, smart_memory_query
)
from .memory_modules.crud_operations import (
    add_memories, add_observation, list_memories, 
    delete_all_memories, get_memory_details
)

# Re-export all functions for backward compatibility
__all__ = [
    'add_memories',
    'add_observation', 
    'search_memory',
    'search_memory_v2',
    'list_memories',
    'delete_all_memories',
    'get_memory_details',
    'ask_memory',
    'smart_memory_query',
    'safe_json_dumps',
    'track_tool_usage'
]
