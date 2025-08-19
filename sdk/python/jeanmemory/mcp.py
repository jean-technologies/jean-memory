"""
Jean Memory Python SDK - MCP Utility
Model Context Protocol request handling
"""

import requests
import json
from typing import Dict, Any, Optional


class MCPResponse:
    def __init__(self, jsonrpc: str, id: int, result: Optional[Dict] = None, error: Optional[Dict] = None):
        self.jsonrpc = jsonrpc
        self.id = id
        self.result = result
        self.error = error


class ContextResponse:
    def __init__(self, text: str, metadata: Optional[Any] = None):
        self.text = text
        self.metadata = metadata


_request_id = 0


def make_mcp_request(
    user_token: str,
    api_key: str,
    tool_name: str,
    arguments: Dict[str, Any],
    api_base: str = "https://jean-memory-api-virginia.onrender.com",
    client_name: str = "python-sdk"
) -> MCPResponse:
    """Make an MCP request to Jean Memory API"""
    global _request_id
    _request_id += 1

    # Extract user_id from token (handles both test_user_ and user_ prefixes)
    user_id = user_token.replace('test_user_', '').replace('user_', '')

    mcp_request = {
        "jsonrpc": "2.0",
        "id": _request_id,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    url = f"{api_base}/mcp/{client_name}/messages/{user_id}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {user_token}',  # Use user's JWT token
        'X-Client-Name': client_name,
        'X-API-Key': api_key  # API key for app identification
    }

    response = requests.post(url, json=mcp_request, headers=headers)

    if not response.ok:
        raise Exception(f"MCP request failed: {response.status_code} - {response.text}")

    response_data = response.json()
    return MCPResponse(
        jsonrpc=response_data.get('jsonrpc', ''),
        id=response_data.get('id', 0),
        result=response_data.get('result'),
        error=response_data.get('error')
    )