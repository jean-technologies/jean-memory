"""
Minimal MCP Client for Direct HTTP Calls

Direct HTTP client that calls the jean_memory MCP tool endpoint,
mimicking Claude Desktop's exact request format without SDK dependencies.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .mcp_types import (
    MCPRequest, MCPResponse, MCPError, MCPNetworkError, 
    MCPAuthenticationError, MCPTimeoutError, MCPRateLimitError,
    create_memory_search_request, create_jean_memory_request, parse_mcp_response
)
from .config import get_auth_headers, is_authenticated


class MinimalMCPClient:
    """
    Minimal MCP client for direct HTTP calls to jean_memory tool.
    
    Replicates Claude Desktop's exact request format for consistent
    communication with the MCP v2 endpoint.
    """
    
    def __init__(
        self,
        base_url: str = "https://jean-memory-api-virginia.onrender.com",
        timeout: float = 30.0,
        max_retries: int = 3,
        log_requests: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.log_requests = log_requests
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if log_requests and not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_mcp_endpoint(self, user_id: str) -> str:
        """Construct MCP v2 endpoint URL"""
        return f"{self.base_url}/mcp/v2/claude/{user_id}"
    
    def _log_request(self, method: str, url: str, headers: Dict[str, str], payload: Dict[str, Any]):
        """Log outgoing request details"""
        if self.log_requests:
            # Don't log sensitive authorization headers
            safe_headers = {k: v for k, v in headers.items() if k.lower() != 'authorization'}
            if 'authorization' in headers:
                safe_headers['authorization'] = 'Bearer [REDACTED]'
            
            self.logger.info(f"MCP Request: {method} {url}")
            self.logger.debug(f"Headers: {safe_headers}")
            self.logger.debug(f"Payload: {payload}")
    
    def _log_response(self, status_code: int, response_data: Any, duration_ms: float):
        """Log incoming response details"""
        if self.log_requests:
            self.logger.info(f"MCP Response: {status_code} ({duration_ms:.1f}ms)")
            if status_code >= 400:
                self.logger.error(f"Error response: {response_data}")
            else:
                self.logger.debug(f"Response data: {response_data}")
    
    def _handle_http_error(self, response: httpx.Response) -> MCPError:
        """Convert HTTP errors to appropriate MCP exceptions"""
        status_code = response.status_code
        
        try:
            error_data = response.json()
        except:
            error_data = {"message": response.text or "Unknown error"}
        
        if status_code == 401:
            return MCPAuthenticationError(
                f"Authentication failed: {error_data.get('message', 'Invalid token')}",
                status_code=status_code,
                response_data=error_data
            )
        elif status_code == 429:
            return MCPRateLimitError(
                f"Rate limit exceeded: {error_data.get('message', 'Too many requests')}",
                status_code=status_code,
                response_data=error_data
            )
        elif status_code >= 500:
            return MCPNetworkError(
                f"Server error ({status_code}): {error_data.get('message', 'Internal server error')}",
                status_code=status_code,
                response_data=error_data
            )
        else:
            return MCPError(
                f"HTTP {status_code}: {error_data.get('message', 'Request failed')}",
                status_code=status_code,
                response_data=error_data
            )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((MCPNetworkError, MCPTimeoutError)),
        reraise=True
    )
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                self._log_request(method, url, headers, payload or {})
                
                if method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=payload)
                else:
                    response = await client.get(url, headers=headers)
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code >= 400:
                    self._log_response(response.status_code, response.text, duration_ms)
                    raise self._handle_http_error(response)
                
                response_data = response.json()
                self._log_response(response.status_code, response_data, duration_ms)
                
                return response_data
                
        except httpx.TimeoutException:
            duration_ms = (time.time() - start_time) * 1000
            self._log_response(0, "Timeout", duration_ms)
            raise MCPTimeoutError(f"Request timed out after {self.timeout}s")
        
        except httpx.NetworkError as e:
            duration_ms = (time.time() - start_time) * 1000
            self._log_response(0, f"Network error: {e}", duration_ms)
            raise MCPNetworkError(f"Network error: {str(e)}")
    
    async def call_tool(
        self,
        request: MCPRequest,
        user_id: Optional[str] = None
    ) -> MCPResponse:
        """
        Call MCP tool with the given request.
        
        Args:
            request: MCP request object
            user_id: User ID for endpoint (if not provided, tries to extract from auth)
            
        Returns:
            MCPResponse object with parsed results
            
        Raises:
            MCPAuthenticationError: If authentication fails
            MCPNetworkError: If network request fails
            MCPTimeoutError: If request times out
            MCPError: For other MCP-related errors
        """
        # Check authentication
        if not is_authenticated():
            raise MCPAuthenticationError("No authentication token available. Run token setup first.")
        
        # Get auth headers
        headers = get_auth_headers()
        
        # If user_id not provided, try to extract from token or use default
        if not user_id:
            # For now, we'll need the user_id to be provided
            # In a real implementation, we might extract it from the JWT token
            raise MCPError("user_id is required for MCP endpoint calls")
        
        # Construct endpoint URL
        url = self._get_mcp_endpoint(user_id)
        
        # Convert request to JSON payload
        payload = request.to_dict()
        
        try:
            # Make the HTTP request
            response_data = await self._make_request("POST", url, headers, payload)
            
            # Parse response
            mcp_response = parse_mcp_response(response_data)
            
            return mcp_response
            
        except MCPError:
            # Re-raise MCP-specific errors
            raise
        except Exception as e:
            # Convert unexpected errors to MCPError
            raise MCPError(f"Unexpected error: {str(e)}")
    
    async def search_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10
    ) -> MCPResponse:
        """
        Convenience method for searching memories (backward compatibility).
        
        Args:
            query: Search query string
            user_id: User ID for the request
            limit: Maximum number of results (ignored, kept for compatibility)
            
        Returns:
            MCPResponse with memory search results
        """
        request = create_memory_search_request(query, user_id, limit)
        return await self.call_tool(request, user_id)
    
    async def call_jean_memory(
        self,
        user_message: str,
        user_id: str,
        is_new_conversation: bool = False,
        needs_context: bool = True,
        speed: str = "balanced",
        format: str = "enhanced"
    ) -> MCPResponse:
        """
        Call jean_memory tool with correct parameters.
        
        Args:
            user_message: The user's message/query
            user_id: User ID for the request
            is_new_conversation: Whether this is a new conversation
            needs_context: Whether personal context is needed
            speed: Processing speed ("balanced", "fast", etc.)
            format: Response format ("enhanced", etc.)
            
        Returns:
            MCPResponse with jean_memory results
        """
        request = create_jean_memory_request(
            user_message=user_message,
            is_new_conversation=is_new_conversation,
            needs_context=needs_context,
            speed=speed,
            format=format
        )
        return await self.call_tool(request, user_id)
    
    async def health_check(self, user_id: str) -> bool:
        """
        Check if MCP endpoint is accessible.
        
        Args:
            user_id: User ID for the health check
            
        Returns:
            True if endpoint is accessible, False otherwise
        """
        try:
            response = await self.call_jean_memory("test", user_id, needs_context=False)
            return response.is_success
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False


# Global client instance
_mcp_client: Optional[MinimalMCPClient] = None


def get_mcp_client(
    base_url: str = "https://jean-memory-api-virginia.onrender.com",
    timeout: float = 30.0,
    max_retries: int = 3,
    log_requests: bool = True
) -> MinimalMCPClient:
    """Get global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MinimalMCPClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            log_requests=log_requests
        )
    return _mcp_client


# Convenience functions for common operations
async def search_memories(
    query: str,
    user_id: str,
    limit: int = 10,
    client: Optional[MinimalMCPClient] = None
) -> MCPResponse:
    """Search memories using global client (backward compatibility)"""
    if client is None:
        client = get_mcp_client()
    return await client.search_memories(query, user_id, limit)


async def call_jean_memory(
    user_message: str,
    user_id: str,
    is_new_conversation: bool = False,
    needs_context: bool = True,
    speed: str = "balanced",
    format: str = "enhanced",
    client: Optional[MinimalMCPClient] = None
) -> MCPResponse:
    """Call jean_memory tool using global client"""
    if client is None:
        client = get_mcp_client()
    return await client.call_jean_memory(
        user_message=user_message,
        user_id=user_id,
        is_new_conversation=is_new_conversation,
        needs_context=needs_context,
        speed=speed,
        format=format
    )


async def call_jean_memory_tool(
    request: MCPRequest,
    user_id: str,
    client: Optional[MinimalMCPClient] = None
) -> MCPResponse:
    """Call jean_memory tool using global client"""
    if client is None:
        client = get_mcp_client()
    return await client.call_tool(request, user_id)


async def test_mcp_connection(user_id: str) -> bool:
    """Test MCP connection using global client"""
    client = get_mcp_client()
    return await client.health_check(user_id)