"""
MCP v2 Request/Response Type Definitions

Defines the exact structure for MCP v2 calls to jean_memory tool,
matching Claude Desktop's request format for consistent communication.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from enum import Enum


class MCPMethod(str, Enum):
    """MCP v2 method types"""
    TOOLS_CALL = "tools/call"


class MCPToolName(str, Enum):
    """Supported MCP tool names"""
    JEAN_MEMORY = "jean_memory"


class MCPArguments(BaseModel):
    """Arguments for jean_memory tool calls"""
    user_message: str
    is_new_conversation: bool
    needs_context: Optional[bool] = True
    speed: Optional[str] = "balanced"
    format: Optional[str] = "enhanced"
    
    class Config:
        extra = "allow"  # Allow additional arguments


class MCPToolCall(BaseModel):
    """MCP tool call structure"""
    name: MCPToolName
    arguments: MCPArguments


class MCPRequest(BaseModel):
    """Complete MCP v2 request structure matching Claude Desktop format"""
    method: MCPMethod
    params: MCPToolCall
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "method": self.method.value,
            "params": {
                "name": self.params.name.value,
                "arguments": self.params.arguments.dict(exclude_unset=True)
            }
        }


class MCPMemoryResult(BaseModel):
    """Individual memory result from jean_memory tool"""
    id: str
    content: str
    category: Optional[str] = None
    source_app: Optional[str] = None
    created_at: Optional[str] = None
    relevance_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class MCPToolResult(BaseModel):
    """Tool execution result"""
    content: List[Dict[str, Any]]
    isError: bool = False
    
    @classmethod
    def from_memories(cls, memories: List[MCPMemoryResult]) -> "MCPToolResult":
        """Create tool result from memory list"""
        return cls(
            content=[{
                "type": "text",
                "text": f"Found {len(memories)} memories"
            }] + [memory.dict() for memory in memories],
            isError=False
        )
    
    @classmethod
    def from_error(cls, error_message: str) -> "MCPToolResult":
        """Create error tool result"""
        return cls(
            content=[{
                "type": "text", 
                "text": f"Error: {error_message}"
            }],
            isError=True
        )


class MCPResponse(BaseModel):
    """Complete MCP v2 response structure"""
    result: MCPToolResult
    error: Optional[Dict[str, Any]] = None
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return self.error is None and not self.result.isError
    
    @property
    def memories(self) -> List[MCPMemoryResult]:
        """Extract memories from response content"""
        memories = []
        if self.result and self.result.content:
            # Skip the first content item (summary text)
            for item in self.result.content[1:]:
                if isinstance(item, dict) and "id" in item:
                    try:
                        memories.append(MCPMemoryResult(**item))
                    except Exception:
                        continue
        return memories
    
    @property
    def summary_text(self) -> Optional[str]:
        """Extract summary text from response"""
        if self.result and self.result.content and len(self.result.content) > 0:
            first_item = self.result.content[0]
            if isinstance(first_item, dict) and "text" in first_item:
                return first_item["text"]
        return None


class MCPError(Exception):
    """Custom exception for MCP-related errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class MCPNetworkError(MCPError):
    """Network-related MCP errors"""
    pass


class MCPAuthenticationError(MCPError):
    """Authentication-related MCP errors"""
    pass


class MCPTimeoutError(MCPError):
    """Timeout-related MCP errors"""
    pass


class MCPRateLimitError(MCPError):
    """Rate limiting MCP errors"""
    pass


# Utility functions for creating common requests
def create_jean_memory_request(
    user_message: str, 
    is_new_conversation: bool = False,
    needs_context: bool = True,
    speed: str = "balanced",
    format: str = "enhanced"
) -> MCPRequest:
    """Create a jean_memory tool request"""
    return MCPRequest(
        method=MCPMethod.TOOLS_CALL,
        params=MCPToolCall(
            name=MCPToolName.JEAN_MEMORY,
            arguments=MCPArguments(
                user_message=user_message,
                is_new_conversation=is_new_conversation,
                needs_context=needs_context,
                speed=speed,
                format=format
            )
        )
    )

# Backward compatibility alias
def create_memory_search_request(query: str, user_id: Optional[str] = None, limit: int = 10) -> MCPRequest:
    """Create a memory search request (backward compatibility)"""
    return create_jean_memory_request(
        user_message=query,
        is_new_conversation=False,
        needs_context=True
    )


def parse_mcp_response(response_data: Dict[str, Any]) -> MCPResponse:
    """Parse raw response data into MCPResponse"""
    try:
        return MCPResponse(**response_data)
    except Exception as e:
        # If parsing fails, create an error response
        return MCPResponse(
            result=MCPToolResult.from_error(f"Failed to parse response: {str(e)}"),
            error={"type": "parse_error", "message": str(e)}
        )