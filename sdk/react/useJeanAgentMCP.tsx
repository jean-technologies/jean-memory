/**
 * Jean Memory React SDK - MCP Direct Integration
 * Uses the jean_memory MCP tool directly (same as Claude Desktop/Cursor integration)
 */
import React, { useState, useEffect, useCallback } from 'react';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

interface JeanUser {
  user_id: string;
  email: string;
  access_token: string;
}

interface JeanAgentConfig {
  apiKey?: string;
  systemPrompt?: string;
  clientName?: string;
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

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export const useJeanAgentMCP = (config: JeanAgentConfig = {}) => {
  const [user, setUser] = useState<JeanUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isFirstMessage, setIsFirstMessage] = useState(true);

  const apiKey = config.apiKey || 'jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA';
  const systemPrompt = config.systemPrompt || 'You are a helpful assistant';
  const clientName = config.clientName || 'React MCP App';

  // Validate API key on initialization
  useEffect(() => {
    const validateApiKey = async () => {
      try {
        const response = await fetch(`${JEAN_API_BASE}/sdk/validate-developer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            api_key: apiKey,
            client_name: clientName
          })
        });

        if (response.ok) {
          const data = await response.json();
          console.log('✅ API key validated for developer:', data.developer_id);
        } else {
          throw new Error('Invalid API key');
        }
      } catch (err) {
        setError(`API key validation failed: ${err}`);
      }
    };

    validateApiKey();
  }, [apiKey, clientName]);

  const signIn = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${JEAN_API_BASE}/sdk/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const userData = await response.json();
      setUser(userData);
      console.log('✅ Authenticated as:', userData.email);
      return userData;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Authentication failed';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const callJeanMemoryTool = useCallback(async (userMessage: string): Promise<string> => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    const mcpRequest: MCPRequest = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: {
        name: 'jean_memory',
        arguments: {
          user_message: userMessage,
          is_new_conversation: isFirstMessage,
          needs_context: true
        }
      }
    };

    const response = await fetch(`${JEAN_API_BASE}/mcp/${clientName}/messages/${user.user_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': user.user_id,
        'x-client-name': clientName
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

    const content = data.result?.content?.[0]?.text || 'No response from jean_memory';
    
    // After first message, subsequent messages are continuing conversation
    if (isFirstMessage) {
      setIsFirstMessage(false);
    }

    return content;
  }, [user, clientName, isFirstMessage]);

  const callStoreDocumentTool = useCallback(async (title: string, content: string, documentType: string = 'markdown'): Promise<string> => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    const mcpRequest: MCPRequest = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: 'tools/call',
      params: {
        name: 'store_document',
        arguments: {
          title,
          content,
          document_type: documentType
        }
      }
    };

    const response = await fetch(`${JEAN_API_BASE}/mcp/${clientName}/messages/${user.user_id}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': user.user_id,
        'x-client-name': clientName
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

    return data.result?.content?.[0]?.text || 'Document stored successfully';
  }, [user, clientName]);

  const sendMessage = useCallback(async (message: string): Promise<string> => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    setIsLoading(true);
    setError(null);

    try {
      // Add user message to conversation
      const userMessage: Message = {
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);

      // Call jean_memory tool
      console.log('🧠 Using jean_memory MCP tool...');
      const memoryResponse = await callJeanMemoryTool(message);

      // Parse the memory response to provide user-friendly output
      let assistantResponse: string;
      
      if (memoryResponse.startsWith('---\n[Your Life Context]')) {
        // New conversation with cached narrative
        const contextLength = memoryResponse.length;
        assistantResponse = `✅ Retrieved ${contextLength} characters from your Jean Memory! As your ${systemPrompt.toLowerCase()}, I can see your personal context and am ready to help with: ${message}`;
      } else if (memoryResponse.includes('Context is not required')) {
        assistantResponse = `As your ${systemPrompt.toLowerCase()}, I can help with: ${message}`;
      } else if (memoryResponse.toLowerCase().includes('new conversation')) {
        assistantResponse = `Welcome! As your ${systemPrompt.toLowerCase()}, I'm ready to help. This conversation will be saved to your Jean Memory for future reference.`;
      } else {
        // Standard context response
        const contextLength = memoryResponse.length;
        assistantResponse = `✅ Retrieved ${contextLength} characters from your Jean Memory. As your ${systemPrompt.toLowerCase()}, I can help with: ${message}\n\nContext: ${memoryResponse.substring(0, 200)}...`;
      }

      // Add assistant response to conversation
      const assistantMessage: Message = {
        role: 'assistant',
        content: assistantResponse,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);

      return assistantResponse;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [user, systemPrompt, callJeanMemoryTool]);

  const storeDocument = useCallback(async (title: string, content: string, documentType: string = 'markdown'): Promise<string> => {
    return await callStoreDocumentTool(title, content, documentType);
  }, [callStoreDocumentTool]);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setIsFirstMessage(true);
    console.log('🗑️ Conversation cleared');
  }, []);

  return {
    user,
    isLoading,
    error,
    messages,
    signIn,
    sendMessage,
    storeDocument,
    clearConversation,
    // Computed properties
    isAuthenticated: !!user,
    conversationHistory: messages,
  };
};

// Sign In Component
interface SignInWithJeanMCPProps {
  onSuccess: (email: string, password: string) => Promise<any>;
  className?: string;
}

export const SignInWithJeanMCP: React.FC<SignInWithJeanMCPProps> = ({ onSuccess, className = '' }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await onSuccess(email, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      <div className="text-center mb-4">
        <h2 className="text-xl font-bold mb-2">🧠 Sign in with Jean Memory</h2>
        <p className="text-sm text-gray-600">Using MCP Tools (jean_memory + store_document)</p>
      </div>
      
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="your@email.com"
        />
      </div>
      
      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
          Password
        </label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="••••••••"
        />
      </div>
      
      {error && (
        <div className="text-red-600 text-sm bg-red-50 p-2 rounded">
          {error}
        </div>
      )}
      
      <button
        type="submit"
        disabled={isLoading || !email || !password}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Signing in...' : 'Sign in with Jean Memory'}
      </button>
    </form>
  );
};

// Chat Component
interface JeanChatMCPProps {
  agent: ReturnType<typeof useJeanAgentMCP>;
  className?: string;
}

export const JeanChatMCP: React.FC<JeanChatMCPProps> = ({ agent, className = '' }) => {
  const [inputMessage, setInputMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || agent.isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');

    try {
      await agent.sendMessage(message);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleStoreConversation = async () => {
    try {
      const conversationContent = agent.messages.map(msg => 
        `**${msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}:** ${msg.content}`
      ).join('\n\n');
      
      const title = `Conversation ${new Date().toLocaleString()}`;
      const result = await agent.storeDocument(title, conversationContent, 'markdown');
      console.log('✅', result);
    } catch (err) {
      console.error('Failed to store conversation:', err);
    }
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="font-semibold">Jean Memory MCP Chat</h3>
          <p className="text-sm text-gray-600">Using jean_memory + store_document tools</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleStoreConversation}
            disabled={agent.messages.length === 0}
            className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
          >
            📄 Store
          </button>
          <button
            onClick={agent.clearConversation}
            disabled={agent.messages.length === 0}
            className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {agent.messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p>🧠 Ready to chat with Jean Memory MCP tools!</p>
            <p className="text-sm">Your conversation will be analyzed and saved automatically.</p>
          </div>
        ) : (
          agent.messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <div className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        
        {agent.isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
              <p className="text-sm">🧠 Using jean_memory tool...</p>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        {agent.error && (
          <div className="text-red-600 text-sm mb-2 bg-red-50 p-2 rounded">
            {agent.error}
          </div>
        )}
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={agent.isLoading}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={agent.isLoading || !inputMessage.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {agent.isLoading ? '⏳' : '📤'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default useJeanAgentMCP;