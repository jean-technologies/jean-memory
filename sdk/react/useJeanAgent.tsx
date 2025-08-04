/**
 * Jean Memory React SDK - Working Integration
 * Matches Python SDK functionality with Assistant-UI components
 */
import React, { useState, useCallback } from 'react';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

export interface JeanAgentConfig {
  apiKey?: string;
  systemPrompt?: string;
}

export interface JeanUser {
  user_id: string;
  email: string;
  access_token: string;
}

export interface JeanAgentHook {
  agent: any;
  user: JeanUser | null;
  isLoading: boolean;
  error: string | null;
  signIn: () => Promise<JeanUser | undefined>;
  signOut: () => void;
}

export function useJeanAgent(config: JeanAgentConfig = {}): JeanAgentHook {
  const [user, setUser] = useState<JeanUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sign in with Jean Memory - matches Python SDK auth flow
  const signIn = useCallback(async (): Promise<JeanUser | undefined> => {
    const email = prompt('Enter your Jean Memory email:');
    const password = prompt('Enter your password:');
    
    if (!email || !password) return;

    setIsLoading(true);
    setError(null);

    try {
      // Actually, let's use the same pattern as Python SDK - authenticate directly with Supabase
      // then use the access token for MCP calls (this matches the working Python implementation)
      const response = await fetch(`${JEAN_API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Authentication failed');
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
  }, [config.apiKey]);

  // Create agent when user is authenticated
  const agent = user ? {
    user,
    config,
    sendMessage: async (message: string) => {
      if (!user) throw new Error('User not authenticated');
      
      // Inject system prompt like Python SDK does
      const systemPrompt = config.systemPrompt || 'You are a helpful assistant';
      const enhancedMessage = `[SYSTEM: ${systemPrompt}]\n\n${message}`;
      
      // Use same MCP endpoint as Python SDK - this matches the working implementation!
      const mcpPayload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
          "name": "jean_memory",
          "arguments": {
            "user_message": enhancedMessage,
            "is_new_conversation": false,
            "needs_context": true
          }
        },
        "id": Date.now()
      };

      const response = await fetch(`${JEAN_API_BASE}/mcp/messages/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mcpPayload)
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      const result = await response.json();
      return result.result || 'No response received';
    }
  } : null;

  return {
    agent,
    user,
    isLoading,
    error,
    signIn,
    signOut: () => setUser(null)
  };
}

// SignInWithJean component - matches business case vision
export function SignInWithJean({ 
  onSuccess, 
  apiKey, 
  className = "px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
}: { 
  onSuccess?: (user: JeanUser) => void;
  apiKey?: string;
  className?: string;
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleSignIn = async () => {
    const email = prompt('Enter your Jean Memory email:');
    const password = prompt('Enter your password:');
    
    if (!email || !password) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${JEAN_API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const userData = await response.json();
      onSuccess?.(userData);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Authentication failed');
      console.error('Sign in failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <button
        onClick={handleSignIn}
        disabled={isLoading}
        className={className}
      >
        🧠 {isLoading ? 'Signing in...' : 'Sign in with Jean'}
      </button>
      {error && (
        <p className="text-red-500 text-sm mt-2">{error}</p>
      )}
    </div>
  );
}

// JeanChat component - Simplified version for MVP
export function JeanChat({ 
  agent, 
  className = "h-96 border rounded-lg p-4"
}: { 
  agent: any;
  className?: string;
}) {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  if (!agent) {
    return (
      <div className={className + " flex items-center justify-center bg-gray-50"}>
        <p className="text-gray-500">Please sign in to start chatting</p>
      </div>
    );
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await agent.sendMessage(input);
      const assistantMessage = { role: 'assistant', content: response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={className + " flex flex-col"}>
      <div className="flex-1 overflow-y-auto mb-4 space-y-2">
        {messages.map((msg, idx) => (
          <div key={idx} className={`p-2 rounded ${
            msg.role === 'user' 
              ? 'bg-blue-100 ml-8' 
              : 'bg-gray-100 mr-8'
          }`}>
            <div className="text-xs text-gray-500 mb-1">
              {msg.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div>{msg.content}</div>
          </div>
        ))}
        {isLoading && (
          <div className="bg-gray-100 mr-8 p-2 rounded">
            <div className="text-xs text-gray-500 mb-1">Assistant</div>
            <div>Thinking...</div>
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          className="flex-1 p-2 border border-gray-300 rounded"
          disabled={isLoading}
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}

// Main export for 5-line integration
export { useJeanAgent as default };