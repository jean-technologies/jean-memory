/**
 * Jean Memory Node.js SDK - Ultimate Minimal Implementation
 * For Next.js API routes and backend integration
 */
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

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

  /**
   * Process a message with Jean Memory context enhancement
   */
  async process(message: string, userToken: string): Promise<any> {
    try {
      // Extract user from token
      const user = await this.getUserFromToken(userToken);
      
      // Enhance message with Jean Memory context
      const contextResponse = await fetch(`${JEAN_API_BASE}/sdk/chat/enhance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: this.config.apiKey,
          client_name: 'Node.js App',
          user_id: user.user_id,
          messages: [{ role: 'user', content: message }],
          system_prompt: this.config.systemPrompt
        })
      });

      const { enhanced_messages, user_context } = await contextResponse.json() as {
        enhanced_messages: any[];
        user_context: string;
      };
      
      // Use enhanced messages with AI SDK
      const result = streamText({
        model: openai(this.config.model!),
        messages: enhanced_messages,
        system: user_context ? 
          `${this.config.systemPrompt}\n\nUser Context: ${user_context}` : 
          this.config.systemPrompt
      });

      return result.toDataStreamResponse();
    } catch (error) {
      throw new Error(`Jean Memory processing failed: ${error}`);
    }
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

// Convenience function for quick setup
export function createJeanHandler(config: JeanAgentConfig) {
  const agent = new JeanAgent(config);
  return agent.createHandler();
}