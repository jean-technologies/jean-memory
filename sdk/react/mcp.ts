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
  user: { user_id: string },
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

  const response = await fetch(`${JEAN_API_BASE}/mcp/${clientName}/messages/${user.user_id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': user.user_id,
      'X-Client-Name': clientName,
      'X-API-Key': apiKey
    },
    body: JSON.stringify(mcpRequest)
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`MCP request failed: ${response.statusText} - ${errorBody}`);
  }

  return response.json();
}
