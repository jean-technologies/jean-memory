/**
 * Jean Memory React SDK - Advanced MCP Hook
 * Direct access to MCP tools for advanced users
 * Uses the jean_memory MCP tool directly (same as Claude Desktop/Cursor)
 */
import { useState, useCallback } from 'react';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

interface JeanUser {
  user_id: string;
  email: string;
  access_token: string;
}

interface MCPRequest {
  jsonrpc: string;
  id: number;
  method: string;
  params: {
    name: string;
    arguments: any;
  };
}

interface MCPResponse {
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

interface UseJeanMCPOptions {
  apiKey: string;
  clientName?: string;
}

interface UseJeanMCPReturn {
  callJeanMemory: (user: JeanUser, message: string, isNewConversation?: boolean) => Promise<string>;
  addMemory: (user: JeanUser, content: string) => Promise<string>;
  searchMemory: (user: JeanUser, query: string) => Promise<string>;
  storeDocument: (user: JeanUser, title: string, content: string, type?: string) => Promise<string>;
}

/**
 * Advanced hook for direct MCP tool access
 * Use this when you need fine-grained control over Jean Memory tools
 */
export function useJeanMCP({ apiKey, clientName = 'react-app' }: UseJeanMCPOptions): UseJeanMCPReturn {
  const [requestId, setRequestId] = useState(0);

  const makeMCPRequest = useCallback(async (user: JeanUser, toolName: string, arguments_: any): Promise<string> => {
    const id = requestId + 1;
    setRequestId(id);

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
      throw new Error(`MCP request failed: ${response.statusText}`);
    }

    const data: MCPResponse = await response.json();

    if (data.error) {
      throw new Error(`MCP Error: ${data.error.message}`);
    }

    return data.result?.content?.[0]?.text || 'No response from tool';
  }, [apiKey, clientName, requestId]);

  const callJeanMemory = useCallback(async (
    user: JeanUser, 
    message: string, 
    isNewConversation: boolean = false
  ): Promise<string> => {
    return makeMCPRequest(user, 'jean_memory', {
      user_message: message,
      is_new_conversation: isNewConversation,
      needs_context: true
    });
  }, [makeMCPRequest]);

  const addMemory = useCallback(async (user: JeanUser, content: string): Promise<string> => {
    return makeMCPRequest(user, 'add_memories', {
      text: content
    });
  }, [makeMCPRequest]);

  const searchMemory = useCallback(async (user: JeanUser, query: string): Promise<string> => {
    return makeMCPRequest(user, 'search_memory', {
      query
    });
  }, [makeMCPRequest]);

  const storeDocument = useCallback(async (
    user: JeanUser, 
    title: string, 
    content: string, 
    type: string = 'markdown'
  ): Promise<string> => {
    return makeMCPRequest(user, 'store_document', {
      title,
      content,
      document_type: type
    });
  }, [makeMCPRequest]);

  return {
    callJeanMemory,
    addMemory,
    searchMemory,
    storeDocument
  };
}