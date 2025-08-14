/**
 * Jean Memory Node.js SDK
 * Power your Next.js and other Node.js backends with a perfect memory
 */

const DEFAULT_JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

interface JeanClientConfig {
  apiKey: string;
  apiBase?: string;
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
  raw_data: any;
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

export class JeanClient {
  protected apiKey: string;
  protected apiBase: string;
  public tools: Tools;
  private requestId: number = 0;
  
  constructor(config: JeanClientConfig) {
    if (!config.apiKey) {
      throw new Error('API key is required');
    }
    
    if (!config.apiKey.startsWith('jean_sk_')) {
      throw new Error('Invalid API key format. Jean Memory API keys start with "jean_sk_"');
    }
    
    this.apiKey = config.apiKey;
    this.apiBase = config.apiBase || process.env.JEAN_API_BASE || DEFAULT_JEAN_API_BASE;
    this.tools = new Tools(this);
  }

  protected _getUserIdFromToken = (user_token: string): string => {
    /**
     * WARNING: This method does not validate the JWT signature. In a production
     * environment, you should use a library like `jose` or `jsonwebtoken` to
     * decode and validate the token against the appropriate public key.
     */
    try {
      const payload = JSON.parse(Buffer.from(user_token.split('.')[1], 'base64').toString('utf8'));
      if (!payload.sub) {
        throw new Error("No 'sub' claim in JWT payload");
      }
      return payload.sub;
    } catch (error) {
      return user_token;
    }
  }
  
  protected _makeMcpRequest = async (user_id: string, tool_name: string, args: any): Promise<any> => {
    this.requestId++;
    const mcpRequest = {
      jsonrpc: '2.0',
      id: this.requestId,
      method: 'tools/call',
      params: {
        name: tool_name,
        arguments: args
      }
    };
    
    try {
      const response = await fetch(`${this.apiBase}/mcp/node-sdk/messages/${user_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
          'X-User-Id': user_id,
        },
        body: JSON.stringify(mcpRequest)
      });
      
      if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`MCP request failed: ${response.statusText} - ${errorBody}`);
      }
      
      const data = (await response.json()) as MCPResponse;
      if (data.error) {
        throw new Error(`MCP Error: ${data.error.message}`);
      }
      
      return data;
    } catch (error) {
      throw new Error(`MCP request failed: ${error}`);
    }
  }

  public getContext = async (options: GetContextOptions): Promise<ContextResponse> => {
    const { user_token, message, speed = 'balanced', tool = 'jean_memory', format = 'enhanced' } = options;
    const user_id = this._getUserIdFromToken(user_token);

    let args: any;
    if (tool === 'jean_memory') {
      args = {
        user_message: message,
        is_new_conversation: false,
        needs_context: true,
        speed,
        format
      };
    } else {
      args = {
        query: message,
        speed,
        format
      };
    }

    const data = await this._makeMcpRequest(user_id, tool, args);
    const resultText = data.result?.content?.[0]?.text || '';
      
    return {
      text: resultText,
      enhanced: format === 'enhanced',
      memories_used: 1,
      raw_data: data
    };
  }
}

class Tools {
  constructor(private client: JeanClient) {}
  
  public add_memory = async (options: { user_token: string; content: string }): Promise<any> => {
    const { user_token, content } = options;
    const user_id = (this.client as any)._getUserIdFromToken(user_token);
    return (this.client as any)._makeMcpRequest(user_id, 'add_memories', { text: content });
  }
  
  public search_memory = async (options: { user_token: string; query: string; limit?: number }): Promise<any> => {
    const { user_token, query, limit = 10 } = options;
    const user_id = (this.client as any)._getUserIdFromToken(user_token);
    return (this.client as any)._makeMcpRequest(user_id, 'search_memory', { query, limit });
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
    const cleanToken = token.replace('Bearer ', '');
    const payload = JSON.parse(Buffer.from(cleanToken.split('.')[1], 'base64').toString('utf8'));
    return {
      user_id: payload.sub,
      email: payload.email
    };
  }
}

export type { JeanClientConfig, GetContextOptions, ContextResponse, JeanAgentConfig };
export default JeanClient;