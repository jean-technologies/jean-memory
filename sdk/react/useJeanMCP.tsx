/**
 * Jean Memory React SDK - Advanced MCP Hook
 * Direct access to MCP tools for advanced users
 * Uses the jean_memory MCP tool directly (same as Claude Desktop/Cursor)
 */
import { useCallback } from 'react';
import { JEAN_API_BASE } from './config';
import { makeMCPRequest } from './mcp';

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
  const callJeanMemory = useCallback(
    async (
      user: JeanUser,
      message: string,
      isNewConversation: boolean = false
    ): Promise<string> => {
      const response = await makeMCPRequest(
        user,
        apiKey,
        'jean_memory',
        {
          user_message: message,
          is_new_conversation: isNewConversation,
          needs_context: true
        },
        clientName
      );
      if (response.error) {
        throw new Error(`MCP Error: ${response.error.message}`);
      }
      return response.result?.content?.[0]?.text || 'No response from tool';
    },
    [apiKey, clientName]
  );

  const addMemory = useCallback(
    async (user: JeanUser, content: string): Promise<string> => {
      const response = await makeMCPRequest(
        user,
        apiKey,
        'add_memories',
        { text: content },
        clientName
      );
      if (response.error) {
        throw new Error(`MCP Error: ${response.error.message}`);
      }
      return response.result?.content?.[0]?.text || 'No response from tool';
    },
    [apiKey, clientName]
  );

  const searchMemory = useCallback(
    async (user: JeanUser, query: string): Promise<string> => {
      const response = await makeMCPRequest(
        user,
        apiKey,
        'search_memory',
        { query },
        clientName
      );
      if (response.error) {
        throw new Error(`MCP Error: ${response.error.message}`);
      }
      return response.result?.content?.[0]?.text || 'No response from tool';
    },
    [apiKey, clientName]
  );

  const storeDocument = useCallback(
    async (
      user: JeanUser,
      title: string,
      content: string,
      type: string = 'markdown'
    ): Promise<string> => {
      const response = await makeMCPRequest(
        user,
        apiKey,
        'store_document',
        {
          title,
          content,
          document_type: type
        },
        clientName
      );
      if (response.error) {
        throw new Error(`MCP Error: ${response.error.message}`);
      }
      return response.result?.content?.[0]?.text || 'No response from tool';
    },
    [apiKey, clientName]
  );

  return {
    callJeanMemory,
    addMemory,
    searchMemory,
    storeDocument
  };
}