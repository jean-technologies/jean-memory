"""
Jean Memory Python SDK Client
Provides access to Jean Memory API for storing and retrieving context-aware memories
"""

import requests
import json
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin
from .mcp import make_mcp_request, ContextResponse as MCPContextResponse
from .models import ContextResponse

class JeanMemoryError(Exception):
    """Base exception for Jean Memory API errors"""
    pass

class JeanMemoryClient:
    """
    Main client for interacting with Jean Memory API
    
    Example:
        client = JeanMemoryClient(api_key="jean_sk_...")
        client.store_memory("I like vanilla ice cream")
        memories = client.retrieve_memories("What do I like?")
    """
    
    def __init__(self, api_key: str, api_base: Optional[str] = None):
        """
        Initialize Jean Memory client
        
        Args:
            api_key: Your Jean Memory API key (starts with 'jean_sk_')
            api_base: Base URL for Jean Memory API (optional)
        """
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith('jean_sk_'):
            raise ValueError("Invalid API key format. Must start with 'jean_sk_'")
            
        self.api_key = api_key
        self.api_base = api_base or "https://jean-memory-api-virginia.onrender.com"
        self.version = "1.2.3"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': f'JeanMemory-Python-SDK/{self.version}'
        })
        
        # Initialize tools namespace
        self.tools = self.Tools(self)

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request to Jean Memory API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload
            
        Returns:
            Response data as dictionary
            
        Raises:
            JeanMemoryError: If request fails
        """
        url = urljoin(self.api_base, endpoint)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data)
            else:
                response = self.session.request(method, url, json=data)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise JeanMemoryError(f"Request failed: {e}")
        except json.JSONDecodeError as e:
            raise JeanMemoryError(f"Invalid JSON response: {e}")

    def store_memory(self, content: str, context: Optional[Dict] = None) -> Dict:
        """
        Store a new memory
        
        Args:
            content: The memory content to store
            context: Optional context metadata
            
        Returns:
            Dictionary with memory ID and confirmation
            
        Example:
            result = client.store_memory(
                "I prefer meetings in the morning",
                {"category": "work_preferences"}
            )
        """
        if not content or not content.strip():
            raise ValueError("Content cannot be empty")
            
        payload = {
            'content': content.strip(),
            'context': context or {}
        }
        
        return self._make_request('POST', '/api/v1/memories', payload)

    def retrieve_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve memories based on query
        
        Args:
            query: Search query
            limit: Maximum number of memories to return (default: 10)
            
        Returns:
            List of memory dictionaries
            
        Example:
            memories = client.retrieve_memories("work preferences", limit=5)
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
            
        params = {
            'query': query.strip(),
            'limit': limit
        }
        
        result = self._make_request('GET', '/api/v1/memories/search', params)
        return result.get('memories', [])

    def get_context_legacy(self, query: str) -> str:
        """
        Get contextual information based on query (legacy method)
        
        Args:
            query: Query to get context for
            
        Returns:
            Formatted context string
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
            
        memories = self.retrieve_memories(query, limit=5)
        
        if not memories:
            return "No relevant context found."
            
        context_parts = []
        for i, memory in enumerate(memories, 1):
            content = memory.get('content', '')
            timestamp = memory.get('created_at', '')
            context_parts.append(f"{i}. {content} ({timestamp})")
            
        return "Relevant context:\n" + "\n".join(context_parts)

    def _get_test_user_token(self) -> str:
        """Get or create auto test user for this API key"""
        import requests
        
        try:
            response = requests.get(
                f"{self.api_base}/api/v1/test-user",
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': f'JeanMemory-Python-SDK/{self.version}'
                }
            )
            
            if not response.ok:
                raise JeanMemoryError(f"Failed to get test user: {response.status_code} {response.text}")
            
            data = response.json()
            return data['user_token']
            
        except requests.RequestException as e:
            raise JeanMemoryError(f"Failed to create test user: {str(e)}")
        except KeyError:
            raise JeanMemoryError("Invalid response from test user endpoint")

    def get_context(self, user_token=None, message=None, query=None, 
                   speed="balanced", tool="jean_memory", format="enhanced") -> ContextResponse:
        """
        Get context from Jean Memory with full OAuth support and backward compatibility
        
        Args:
            user_token: OAuth token from frontend (production) or None for test user
            message: User message (preferred parameter name for new API)
            query: User query (backward compatibility with old API)
            speed: "fast" | "balanced" | "comprehensive" 
            tool: "jean_memory" | "search_memory"
            format: "simple" | "enhanced"
            
        Returns:
            ContextResponse object with .text property
            
        Examples:
            # New API (matches documentation):
            response = client.get_context(user_token=token, message="What's my schedule?")
            print(response.text)
            
            # Backward compatibility:
            response = client.get_context(query="What's my schedule?")
            print(response.text)
        """
        # Handle parameter flexibility
        user_message = message or query
        if not user_message:
            raise ValueError("Either 'message' or 'query' parameter is required")
        
        # Get user token (from parameter or create test user)
        final_user_token = user_token or self._get_test_user_token()
        
        # Make MCP request with enhanced options
        mcp_response = make_mcp_request(
            user_token=final_user_token,
            api_key=self.api_key,
            tool_name=tool,
            arguments={
                'user_message': user_message,
                'is_new_conversation': False,  # Reasonable default for SDK users
                'needs_context': True,         # SDK users always want context
                'speed': speed,
                'format': format
            },
            api_base=self.api_base
        )

        if mcp_response.error:
            raise JeanMemoryError(f"MCP request failed: {mcp_response.error.get('message', 'Unknown error')}")

        # Extract text from MCP response
        text = ""
        if mcp_response.result and mcp_response.result.get('content'):
            text = mcp_response.result['content'][0].get('text', '')

        return ContextResponse(text=text, metadata=mcp_response.result)

    def delete_memory(self, memory_id: str) -> Dict:
        """
        Delete a specific memory
        
        Args:
            memory_id: ID of the memory to delete
            
        Returns:
            Confirmation dictionary
        """
        if not memory_id:
            raise ValueError("Memory ID is required")
            
        return self._make_request('DELETE', f'/api/v1/memories/{memory_id}')

    def list_memories(self, limit: int = 20, offset: int = 0) -> Dict:
        """
        List all memories with pagination
        
        Args:
            limit: Number of memories to return (default: 20)
            offset: Number of memories to skip (default: 0)
            
        Returns:
            Dictionary with memories list and pagination info
        """
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        if offset < 0:
            raise ValueError("Offset must be non-negative")
            
        params = {
            'limit': limit,
            'offset': offset
        }
        
        return self._make_request('GET', '/api/v1/memories', params)

    def health_check(self) -> Dict:
        """
        Check API health and authentication
        
        Returns:
            Health status dictionary
        """
        return self._make_request('GET', '/api/v1/health')

    class Tools:
        """Direct tool access namespace (matching documentation)"""
        
        def __init__(self, client):
            self.client = client
            
        def add_memory(self, content: str, user_token=None) -> Dict:
            """
            Add memory using direct tool access
            
            Args:
                content: Memory content to add
                user_token: OAuth token from frontend or None for test user
                
            Returns:
                Memory creation result
            """
            final_user_token = user_token or self.client._get_test_user_token()
            mcp_response = make_mcp_request(
                user_token=final_user_token,
                api_key=self.client.api_key,
                tool_name='add_memories',
                arguments={'text': content},
                api_base=self.client.api_base
            )

            if mcp_response.error:
                raise JeanMemoryError(f"MCP request failed: {mcp_response.error.get('message', 'Unknown error')}")

            return mcp_response.result

        def search_memory(self, query: str, user_token=None) -> Dict:
            """
            Search memory using direct tool access
            
            Args:
                query: Search query
                user_token: OAuth token from frontend or None for test user
                
            Returns:
                Search results
            """
            final_user_token = user_token or self.client._get_test_user_token()
            mcp_response = make_mcp_request(
                user_token=final_user_token,
                api_key=self.client.api_key,
                tool_name='search_memory',
                arguments={'query': query},
                api_base=self.client.api_base
            )

            if mcp_response.error:
                raise JeanMemoryError(f"MCP request failed: {mcp_response.error.get('message', 'Unknown error')}")

            return mcp_response.result