/**
 * Jean Memory React SDK - Ultimate Minimal Implementation
 * 5-line integration with full MCP + Assistant-UI support
 */
import { useState, useCallback, useEffect } from 'react';
import { useChatRuntime } from '@assistant-ui/react-ai-sdk';
import { createMCPClient } from 'ai/mcp';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

interface JeanAgentConfig {
  apiKey?: string;
  systemPrompt?: string;
  endpoint?: string;
}

interface JeanUser {
  user_id: string;
  email: string;
  access_token: string;
}

export function useJeanAgent(config: JeanAgentConfig = {}) {
  const [user, setUser] = useState<JeanUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sign in with Jean Memory
  const signIn = useCallback(async () => {
    const email = prompt('Enter your Jean Memory email:');
    const password = prompt('Enter your password:');
    
    if (!email || !password) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${JEAN_API_BASE}/sdk/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const userData = await response.json();
      setUser(userData);
      setIsLoading(false);
      return userData;
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Authentication failed');
      setIsLoading(false);
      throw error;
    }
  }, []);

  // Create MCP client pointing to Jean Memory server
  const mcpClient = createMCPClient({
    servers: {
      'jean-memory': {
        command: 'curl',
        args: [
          '-X', 'POST',
          `${JEAN_API_BASE}/mcp/messages/`,
          '-H', 'Content-Type: application/json',
          '-H', user ? `Authorization: Bearer ${user.access_token}` : '',
        ]
      }
    }
  });

  // Assistant-UI runtime with Jean Memory MCP integration
  const runtime = useChatRuntime({
    api: config.endpoint || '/api/jean-chat',
    tools: user ? await mcpClient.getTools() : [],
    initialMessages: config.systemPrompt ? [
      { role: 'system', content: config.systemPrompt }
    ] : []
  });

  // Agent configuration for assistant-ui
  const agent = user ? runtime : null;

  return {
    agent,
    user,
    isLoading,
    error,
    signIn,
    signOut: () => setUser(null)
  };
}

// Simple components for ultimate ease of use
export function SignInWithJean({ onSuccess }: { onSuccess?: () => void }) {
  const { signIn, isLoading } = useJeanAgent();
  
  const handleSignIn = async () => {
    try {
      await signIn();
      onSuccess?.();
    } catch (error) {
      console.error('Sign in failed:', error);
    }
  };

  return (
    <button
      onClick={handleSignIn}
      disabled={isLoading}
      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
    >
      🧠 {isLoading ? 'Signing in...' : 'Sign in with Jean'}
    </button>
  );
}

export function JeanChat({ agent }: { agent: any }) {
  if (!agent) return null;
  
  const { Thread } = require('@assistant-ui/react');
  return <Thread />;
}