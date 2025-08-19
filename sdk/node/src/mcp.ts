/**
 * Jean Memory Node.js SDK - MCP Utility
 * Model Context Protocol request handling
 */

interface MCPRequest {
  jsonrpc: string;
  id: number;
  method: string;
  params: {
    name: string;
    arguments: any;
  };
}

export interface MCPResponse {
  jsonrpc: string;
  id: number;
  result?: {
    content: Array<{
      type: string;
      text: string;
    }>;
  };
  error?: {
    code: number;
    message: string;
  };
}

export interface ContextResponse {
  text: string;
  metadata?: any;
}

let requestId = 0;

export async function makeMCPRequest(
  userToken: string,
  apiKey: string,
  toolName: string,
  arguments_: any,
  apiBase: string = 'https://jean-memory-api-virginia.onrender.com',
  clientName: string = 'node-sdk'
): Promise<MCPResponse> {
  const id = ++requestId;

  const mcpRequest: MCPRequest = {
    jsonrpc: '2.0',
    id,
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: arguments_
    }
  };

  // Extract user_id from token (handles both test_user_ and user_ prefixes)
  const userId = userToken.replace('test_user_', '').replace('user_', '');

  const response = await fetch(`${apiBase}/mcp/${clientName}/messages/${userId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${userToken}`,  // Use user's JWT token
      'X-Client-Name': clientName,
      'X-API-Key': apiKey  // API key for app identification
    },
    body: JSON.stringify(mcpRequest)
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`MCP request failed: ${response.statusText} - ${errorBody}`);
  }

  return response.json() as Promise<MCPResponse>;
}