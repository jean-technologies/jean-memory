/**
 * Jean Memory Node.js SDK Client
 * Main client for interacting with Jean Memory API
 */

import { JeanMemoryAuth } from './auth';
import { makeMCPRequest, ContextResponse as MCPContextResponse } from './mcp';
import { 
  Memory, 
  MemoryCreateRequest, 
  MemorySearchOptions, 
  MemoryListOptions,
  APIResponse,
  ClientConfig,
  ContextResponse,
  OAuthContextParams
} from './types';

export class JeanMemoryError extends Error {
  constructor(message: string, public statusCode?: number) {
    super(message);
    this.name = 'JeanMemoryError';
  }
}

export class JeanMemoryClient {
  private apiKey: string;
  private apiBase: string;
  private userAgent: string;

  constructor(config: ClientConfig) {
    if (!config.apiKey) {
      throw new Error('API key is required');
    }
    if (!config.apiKey.startsWith('jean_sk_')) {
      throw new Error('Invalid API key format. Must start with "jean_sk_"');
    }

    this.apiKey = config.apiKey;
    this.apiBase = config.apiBase || 'https://jean-memory-api-virginia.onrender.com';
    this.userAgent = config.userAgent || 'JeanMemory-Node-SDK/1.2.4';
  }

  /**
   * Make authenticated HTTP request to Jean Memory API
   */
  private async makeRequest<T>(
    method: string, 
    endpoint: string, 
    data?: any
  ): Promise<T> {
    const url = new URL(endpoint, this.apiBase).toString();
    
    const options: RequestInit = {
      method,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'User-Agent': this.userAgent,
      },
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(data);
    } else if (data && method === 'GET') {
      const searchParams = new URLSearchParams();
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      const urlWithParams = new URL(url);
      urlWithParams.search = searchParams.toString();
      const finalUrl = urlWithParams.toString();
      
      const response = await fetch(finalUrl, options);
      return this.handleResponse<T>(response);
    }

    const response = await fetch(url, options);
    return this.handleResponse<T>(response);
  }

  /**
   * Handle HTTP response and error cases
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      
      try {
        const errorData = await response.json() as any;
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch {
        // If JSON parsing fails, use status text
        errorMessage = response.statusText || errorMessage;
      }
      
      throw new JeanMemoryError(errorMessage, response.status);
    }

    try {
      return await response.json() as T;
    } catch {
      throw new JeanMemoryError('Invalid JSON response');
    }
  }

  /**
   * Store a new memory
   */
  async storeMemory(content: string, context?: Record<string, any>): Promise<Memory> {
    if (!content || !content.trim()) {
      throw new Error('Content cannot be empty');
    }

    const request: MemoryCreateRequest = {
      content: content.trim(),
      context: context || {}
    };

    return this.makeRequest<Memory>('POST', '/api/v1/memories', request);
  }

  /**
   * Retrieve memories based on search query
   */
  async retrieveMemories(query: string, options: MemorySearchOptions = {}): Promise<Memory[]> {
    if (!query || !query.trim()) {
      throw new Error('Query cannot be empty');
    }

    const { limit = 10, offset = 0 } = options;
    
    if (limit < 1 || limit > 100) {
      throw new Error('Limit must be between 1 and 100');
    }
    if (offset < 0) {
      throw new Error('Offset must be non-negative');
    }

    const params = {
      query: query.trim(),
      limit,
      offset
    };

    const response = await this.makeRequest<APIResponse<{ memories: Memory[] }>>
      ('GET', '/api/v1/memories/search', params);
    
    return response.data?.memories || [];
  }

  /**
   * Get formatted context for a query (legacy method)
   */
  async getContextLegacy(query: string): Promise<string> {
    if (!query || !query.trim()) {
      throw new Error('Query cannot be empty');
    }

    const memories = await this.retrieveMemories(query, { limit: 5 });
    
    if (memories.length === 0) {
      return 'No relevant context found.';
    }

    const contextParts = memories.map((memory, index) => {
      const content = memory.content || '';
      const timestamp = memory.created_at || '';
      return `${index + 1}. ${content} (${timestamp})`;
    });

    return 'Relevant context:\\n' + contextParts.join('\\n');
  }

  /**
   * Get or create auto test user for this API key
   */
  private async getTestUserToken(): Promise<string> {
    try {
      const response = await fetch(`${this.apiBase}/api/v1/test-user`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`,
          'Content-Type': 'application/json',
          'User-Agent': this.userAgent
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to get test user: ${response.statusText}`);
      }

      const data = await response.json() as { user_token: string };
      return data.user_token;
    } catch (error: any) {
      throw new JeanMemoryError(`Failed to create test user: ${error?.message || 'Unknown error'}`);
    }
  }

  /**
   * Get context from Jean Memory with OAuth support and backward compatibility
   * @overload
   * @param params Object with user_token and message for OAuth flow
   * @returns ContextResponse with enhanced metadata
   */
  async getContext(params: OAuthContextParams): Promise<ContextResponse>;
  /**
   * @overload
   * @param query Simple string query for backward compatibility
   * @returns Plain string response
   */
  async getContext(query: string): Promise<string>;
  async getContext(
    paramsOrQuery: string | OAuthContextParams
  ): Promise<string | ContextResponse> {
    // Handle backward compatibility - simple string query
    if (typeof paramsOrQuery === 'string') {
      const userToken = await this.getTestUserToken();
      const mcpResponse = await makeMCPRequest(
        userToken,
        this.apiKey,
        'jean_memory',
        {
          user_message: paramsOrQuery,
          is_new_conversation: false,
          needs_context: true
        },
        this.apiBase
      );

      if (mcpResponse.error) {
        throw new JeanMemoryError(mcpResponse.error.message, mcpResponse.error.code);
      }

      return mcpResponse.result?.content?.[0]?.text || '';
    }

    // Handle OAuth API - object with user_token and message
    const { user_token, message, speed = 'balanced', tool = 'jean_memory', format = 'enhanced' } = paramsOrQuery;
    
    const mcpResponse = await makeMCPRequest(
      user_token,
      this.apiKey,
      tool,
      {
        user_message: message,
        is_new_conversation: false,
        needs_context: true,
        speed,
        format
      },
      this.apiBase
    );

    if (mcpResponse.error) {
      throw new JeanMemoryError(mcpResponse.error.message, mcpResponse.error.code);
    }

    // Return ContextResponse object
    return {
      text: mcpResponse.result?.content?.[0]?.text || '',
      metadata: mcpResponse.result
    } as ContextResponse;
  }

  /**
   * List all memories with pagination
   */
  async listMemories(options: MemoryListOptions = {}): Promise<{
    memories: Memory[];
    total: number;
    hasNext: boolean;
    hasPrev: boolean;
  }> {
    const { limit = 20, offset = 0 } = options;
    
    if (limit < 1 || limit > 100) {
      throw new Error('Limit must be between 1 and 100');
    }
    if (offset < 0) {
      throw new Error('Offset must be non-negative');
    }

    const params = { limit, offset };
    
    const response = await this.makeRequest<APIResponse<{
      memories: Memory[];
      total: number;
      pagination: {
        has_next: boolean;
        has_prev: boolean;
      };
    }>>('GET', '/api/v1/memories', params);

    return {
      memories: response.data?.memories || [],
      total: response.data?.total || 0,
      hasNext: response.data?.pagination?.has_next || false,
      hasPrev: response.data?.pagination?.has_prev || false
    };
  }

  /**
   * Delete a specific memory
   */
  async deleteMemory(memoryId: string): Promise<void> {
    if (!memoryId) {
      throw new Error('Memory ID is required');
    }

    await this.makeRequest<APIResponse<any>>('DELETE', `/api/v1/memories/${memoryId}`);
  }

  /**
   * Stream memories (for large result sets)
   */
  async streamMemories(query: string): Promise<ReadableStream<Memory>> {
    if (!query || !query.trim()) {
      throw new Error('Query cannot be empty');
    }

    // For now, implement as a batch fetch with streaming interface
    // This can be enhanced when backend supports true streaming
    const memories = await this.retrieveMemories(query, { limit: 100 });
    
    return new ReadableStream<Memory>({
      start(controller) {
        memories.forEach(memory => controller.enqueue(memory));
        controller.close();
      }
    });
  }

  /**
   * Check API health and authentication
   */
  async healthCheck(): Promise<{
    status: string;
    authenticated: boolean;
    version?: string;
  }> {
    return this.makeRequest<{
      status: string;
      authenticated: boolean;
      version?: string;
    }>('GET', '/api/v1/health');
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<{
    user_id: string;
    email: string;
    name?: string;
    created_at: string;
  }> {
    return this.makeRequest<{
      user_id: string;
      email: string;
      name?: string;
      created_at: string;
    }>('GET', '/api/v1/user/me');
  }

  /**
   * Direct tool access namespace with OAuth support
   */
  tools = {
    add_memory: async (params: { user_token?: string; content: string } | string) => {
      // Handle both signatures for flexibility
      const isObject = typeof params === 'object';
      const content = isObject ? params.content : params;
      const userToken = isObject && params.user_token ? params.user_token : await this.getTestUserToken();
      
      const mcpResponse = await makeMCPRequest(
        userToken,
        this.apiKey,
        'add_memories',
        { 
          text: content,
          tags: [],
          priority: false
        },
        this.apiBase
      );

      if (mcpResponse.error) {
        throw new JeanMemoryError(mcpResponse.error.message, mcpResponse.error.code);
      }

      return mcpResponse.result;
    },

    search_memory: async (params: { user_token?: string; query: string } | string) => {
      // Handle both signatures for flexibility
      const isObject = typeof params === 'object';
      const query = isObject ? params.query : params;
      const userToken = isObject && params.user_token ? params.user_token : await this.getTestUserToken();
      
      const mcpResponse = await makeMCPRequest(
        userToken,
        this.apiKey,
        'search_memory',
        { 
          query: query,
          limit: 10,
          tags_filter: null,
          deep_search: false
        },
        this.apiBase
      );

      if (mcpResponse.error) {
        throw new JeanMemoryError(mcpResponse.error.message, mcpResponse.error.code);
      }

      return mcpResponse.result;
    },

    deep_memory_query: async (params: { user_token?: string; query: string } | string) => {
      // Handle both signatures for flexibility
      const isObject = typeof params === 'object';
      const query = isObject ? params.query : params;
      const userToken = isObject && params.user_token ? params.user_token : await this.getTestUserToken();
      
      const mcpResponse = await makeMCPRequest(
        userToken,
        this.apiKey,
        'deep_memory_query',
        { 
          query: query
        },
        this.apiBase
      );

      if (mcpResponse.error) {
        throw new JeanMemoryError(mcpResponse.error.message, mcpResponse.error.code);
      }

      return mcpResponse.result;
    },

    store_document: async (params: { user_token?: string; title: string; content: string; document_type?: string }) => {
      const { user_token, title, content, document_type = 'markdown' } = params;
      const userToken = user_token || await this.getTestUserToken();
      
      const mcpResponse = await makeMCPRequest(
        userToken,
        this.apiKey,
        'store_document',
        { 
          title,
          content,
          document_type
        },
        this.apiBase
      );

      if (mcpResponse.error) {
        throw new JeanMemoryError(mcpResponse.error.message, mcpResponse.error.code);
      }

      return mcpResponse.result;
    }
  };

  /**
   * Get authentication helper for OAuth flows
   */
  createAuth(config?: { oauthBase?: string; redirectPort?: number }): JeanMemoryAuth {
    return new JeanMemoryAuth({
      apiKey: this.apiKey,
      oauthBase: config?.oauthBase,
      redirectPort: config?.redirectPort
    });
  }
}