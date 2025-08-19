/**
 * Jean Memory React SDK - MCP Utility
 * Shared logic for making MCP requests
 */
import { JEAN_API_BASE } from './config';

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

let requestId = 0;

export async function makeMCPRequest(
  user: { access_token: string },
  apiKey: string,
  toolName: string,
  arguments_: any,
  clientName: string = 'react-sdk'
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

  // Extract user_id from JWT token for URL path
  const payload = JSON.parse(atob(user.access_token.split('.')[1]));
  const userId = payload.sub;

  const response = await fetch(`${JEAN_API_BASE}/mcp/${clientName}/messages/${userId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${user.access_token}`,  // Use user's JWT token
      'X-Client-Name': clientName,
      'X-API-Key': apiKey  // API key for app identification
    },
    body: JSON.stringify(mcpRequest)
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`MCP request failed: ${response.statusText} - ${errorBody}`);
  }

  return response.json();
}
