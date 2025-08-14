/**
 * Jean Memory Node.js SDK
 * Power your Next.js and other Node.js backends with a perfect memory
 */

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

interface JeanClientConfig {
  apiKey: string;
}

interface GetContextOptions {
  user_token: string;
  message: string;
  speed?: 'fast' | 'balanced' | 'comprehensive';
  tool?: 'jean_memory' | 'search_memory';
  format?: 'simple' | 'enhanced';
}

interface ContextResponse {
  text: string;
  enhanced: boolean;
  memories_used: number;
}

export class JeanClient {
  private apiKey: string;
  public tools: Tools;
  
  constructor(config: JeanClientConfig) {
    if (!config.apiKey) {
      throw new Error('API key is required');
    }
    
    if (!config.apiKey.startsWith('jean_sk_')) {
      throw new Error('Invalid API key format. Jean Memory API keys start with "jean_sk_"');
    }
    
    this.apiKey = config.apiKey;
    this.tools = new Tools(this);
    
    // Validate API key
    this.validateApiKey();
  }
  
  private async validateApiKey(): Promise<void> {
    try {
      // Use MCP health endpoint to validate connectivity
      const response = await fetch(`${JEAN_API_BASE}/mcp`, {
        headers: { 'X-API-Key': this.apiKey }
      });
      
      if (![200, 404].includes(response.status)) {
        throw new Error('Invalid API key or connection failed');
      }
      
      console.log('✅ Jean Memory client initialized');
    } catch (error) {
      throw new Error(`API key validation failed: ${error}`);
    }
  }

  /**
   * Get context from Jean Memory for a user message
   */
  async getContext(options: GetContextOptions): Promise<ContextResponse> {
    const { user_token, message, speed = 'balanced', tool = 'jean_memory', format = 'enhanced' } = options;
    
    try {
      // Extract user_id from token (simplified)
      let user_id: string;
      try {
        const payload = JSON.parse(atob(user_token.split('.')[1]));
        user_id = payload.sub || user_token;
      } catch {
        user_id = user_token; // Fallback
      }
      
      // Use MCP endpoint with configuration
      const mcpRequest = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: tool,
          arguments: tool === 'jean_memory' ? {
            user_message: message,
            is_new_conversation: false,
            needs_context: true,
            speed: speed,  // Pass speed parameter
            format: format  // Pass format parameter
          } : {
            query: message,
            speed: speed,
            format: format
          }
        }
      };
      
      const response = await fetch(`${JEAN_API_BASE}/mcp/messages/${user_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify(mcpRequest)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to get context: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.error) {
        throw new Error(`MCP Error: ${data.error.message}`);
      }
      
      const resultText = data.result?.content?.[0]?.text || '';
      
      return {
        text: resultText,
        enhanced: format === 'enhanced',
        memories_used: 1
      };
    } catch (error) {
      throw new Error(`Failed to get context: ${error}`);
    }
  }
}

/**
 * Direct access to memory manipulation tools
 */
class Tools {
  constructor(private client: JeanClient) {}
  
  async add_memory(options: { user_token: string; content: string }): Promise<any> {
    const { user_token, content } = options;
    
    try {
      // Extract user_id from token
      let user_id: string;
      try {
        const payload = JSON.parse(atob(user_token.split('.')[1]));
        user_id = payload.sub || user_token;
      } catch {
        user_id = user_token;
      }
      
      const mcpRequest = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: 'add_memories',
          arguments: { text: content }
        }
      };
      
      const response = await fetch(`${JEAN_API_BASE}/mcp/messages/${user_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.client['apiKey']
        },
        body: JSON.stringify(mcpRequest)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to add memory: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error) {
      throw new Error(`Failed to add memory: ${error}`);
    }
  }
  
  async search_memory(options: { user_token: string; query: string; limit?: number }): Promise<any> {
    const { user_token, query, limit = 10 } = options;
    
    try {
      // Extract user_id from token
      let user_id: string;
      try {
        const payload = JSON.parse(atob(user_token.split('.')[1]));
        user_id = payload.sub || user_token;
      } catch {
        user_id = user_token;
      }
      
      const mcpRequest = {
        jsonrpc: '2.0',
        id: Date.now(),
        method: 'tools/call',
        params: {
          name: 'search_memory',
          arguments: { query }
        }
      };
      
      const response = await fetch(`${JEAN_API_BASE}/mcp/messages/${user_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.client['apiKey']
        },
        body: JSON.stringify(mcpRequest)
      });
      
      if (!response.ok) {
        throw new Error(`Failed to search memory: ${response.statusText}`);
      }
      
      return response.json();
    } catch (error) {
      throw new Error(`Failed to search memory: ${error}`);
    }
  }
}

// Legacy JeanAgent class for backward compatibility
interface JeanAgentConfig {
  apiKey?: string;
  systemPrompt?: string;
  model?: string;
}

export class JeanAgent {
  private config: JeanAgentConfig;
  
  constructor(config: JeanAgentConfig) {
    this.config = {
      model: 'gpt-4o-mini',
      systemPrompt: 'You are a helpful assistant.',
      ...config
    };
  }
  
  tools = {
    add_memory: async (userToken: string, content: string): Promise<any> => {
      console.log(`[JeanSDK] Adding memory for user...`, { content });
      return Promise.resolve({ success: true, message: "Memory will be added." });
    },
    search_memory: async (userToken: string, query: string): Promise<any> => {
      console.log(`[JeanSDK] Searching memory for user...`, { query });
      return Promise.resolve({ results: [] });
    },
    deep_memory_query: async (userToken: string, query: string): Promise<any> => {
      console.log(`[JeanSDK] Performing deep memory query for user...`, { query });
      return Promise.resolve({ results: [] });
    }
  };

  async process(message: string, userToken: string): Promise<any> {
    // Legacy method - not implemented in new SDK
    throw new Error('process() is deprecated. Use JeanClient.getContext() instead.');
  }

  /**
   * Create Next.js API route handler
   */
  createHandler() {
    return async (req: any, res: any) => {
      if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
      }

      try {
        const { message } = req.body;
        const userToken = req.headers.authorization;

        if (!userToken) {
          return res.status(401).json({ error: 'Authorization required' });
        }

        const response = await this.process(message, userToken);
        return response;
      } catch (error) {
        console.error('Jean Memory API error:', error);
        return res.status(500).json({ error: 'Internal server error' });
      }
    };
  }

  private async getUserFromToken(token: string) {
    // Extract user info from the Jean Memory token
    // This would validate the token and return user details
    const cleanToken = token.replace('Bearer ', '');
    
    // For now, we'll extract from JWT payload (simplified)
    const payload = JSON.parse(atob(cleanToken.split('.')[1]));
    return {
      user_id: payload.sub,
      email: payload.email
    };
  }
}

// Export types
export type { JeanClientConfig, GetContextOptions, ContextResponse, JeanAgentConfig };

// Default export
export default JeanClient;