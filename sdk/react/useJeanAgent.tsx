/**
 * Jean Memory React SDK - MCP Direct Integration
 * Uses the jean_memory MCP tool directly (same as Claude Desktop/Cursor integration)
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';

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

export const useJeanAgent = (config: JeanAgentConfig = {}) => {
  const [user, setUser] = useState<JeanUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isFirstMessage, setIsFirstMessage] = useState(true);

  const apiKey = config.apiKey;
  const systemPrompt = config.systemPrompt || 'You are a helpful assistant';
  const clientName = config.clientName || 'claude';

  // Validate API key on initialization
  useEffect(() => {
    if (!apiKey) {
      setError('API key is required. Please provide your Jean Memory API key.');
      return;
    }

    if (!apiKey.startsWith('jean_sk_')) {
      setError('Invalid API key format. Jean Memory API keys start with "jean_sk_".');
      return;
    }

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

  const synthesizeNaturalResponse = useCallback(async (
    userMessage: string, 
    context: string, 
    systemPrompt: string, 
    hasRichContext: boolean
  ): Promise<string> => {
    try {
      // Create messages for LLM synthesis
      const messages = [
        {
          role: 'system',
          content: `${systemPrompt}${context ? `\n\nPersonal context about the user:\n${context}` : ''}

IMPORTANT: Respond naturally as the persona described in the system prompt. Do NOT mention that you retrieved context or accessed memories. Act as if you naturally know this information about the user. Be conversational and helpful.`
        },
        {
          role: 'user', 
          content: userMessage
        }
      ];

      // Call backend synthesis endpoint (uses server-side OpenAI key)
      const response = await fetch(`${JEAN_API_BASE}/sdk/synthesize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          api_key: apiKey,
          messages,
          user_id: user?.user_id
        })
      });

      if (!response.ok) {
        throw new Error(`Synthesis API error: ${response.statusText}`);
      }

      const data = await response.json();
      return data.response || 'I\'m here to help!';
      
    } catch (error) {
      console.error('LLM synthesis error:', error);
      // Fallback to basic response if LLM fails
      if (hasRichContext) {
        return `As your ${systemPrompt.toLowerCase()}, I can see from our previous interactions that I can help you with many things. What would you like to work on?`;
      } else {
        return `As your ${systemPrompt.toLowerCase()}, I'm ready to help! What can I assist you with?`;
      }
    }
  }, [apiKey, user]);

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

      // Synthesize natural conversational response using context
      let assistantResponse: string;
      
      if (memoryResponse.startsWith('---\n[Your Life Context]')) {
        // New conversation with full narrative context - respond naturally as the persona
        const context = memoryResponse.replace('---\n[Your Life Context]\n', '').replace('\n---', '');
        assistantResponse = await synthesizeNaturalResponse(message, context, systemPrompt, true);
      } else if (memoryResponse.includes('Context is not required')) {
        // No context needed - respond as persona without personal context
        assistantResponse = await synthesizeNaturalResponse(message, '', systemPrompt, false);
      } else if (memoryResponse.toLowerCase().includes('new conversation')) {
        // First conversation without cached context
        assistantResponse = await synthesizeNaturalResponse(message, '', systemPrompt, false);
      } else {
        // Standard context response - use retrieved memories naturally
        assistantResponse = await synthesizeNaturalResponse(message, memoryResponse, systemPrompt, false);
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
  }, [user, systemPrompt, callJeanMemoryTool, synthesizeNaturalResponse]);

  const storeDocument = useCallback(async (title: string, content: string, documentType: string = 'markdown'): Promise<string> => {
    return await callStoreDocumentTool(title, content, documentType);
  }, [callStoreDocumentTool]);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setIsFirstMessage(true);
    console.log('🗑️ Conversation cleared');
  }, []);

  // Create a simple runtime interface for compatibility
  const runtime = useMemo(() => {
    if (!user) return null;
    return {
      messages,
      isLoading,
      sendMessage,
      user,
      userId: user.user_id
    };
  }, [user, messages, isLoading, sendMessage]);

  return {
    user,
    isLoading,
    error,
    messages,
    signIn,
    sendMessage,
    storeDocument,
    clearConversation,
    // Assistant-UI runtime
    runtime,
    // Computed properties
    isAuthenticated: !!user,
    conversationHistory: messages,
    // Legacy interface compatibility
    agent: user ? {
      user,
      config,
      sendMessage,
      runtime,
      userId: user.user_id
    } : null,
    signOut: () => setUser(null)
  };
};

// Sign In Component - Enhanced MCP Version
interface SignInWithJeanProps {
  onSuccess: (email: string, password: string) => Promise<any>;
  className?: string;
}

export const SignInWithJean: React.FC<SignInWithJeanProps> = ({ onSuccess, className = '' }) => {
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

// Chat Component - Professional Assistant-UI Style
interface JeanChatProps {
  agent: ReturnType<typeof useJeanAgent>;
  className?: string;
}

export const JeanChat: React.FC<JeanChatProps> = ({ agent, className = '' }) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [agent.messages]);

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

  // If not authenticated, show sign in prompt
  if (!agent.runtime) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center text-gray-500 p-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            🧠
          </div>
          <p className="text-lg font-medium">Sign in to start chatting</p>
          <p className="text-sm text-gray-400">Connect with your Jean Memory assistant</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Header - Professional Assistant UI Style */}
      <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
            🧠
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Jean Memory Assistant</h3>
            <p className="text-xs text-gray-500">Powered by assistant-ui</p>
          </div>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleStoreConversation}
            disabled={agent.messages.length === 0}
            className="px-3 py-1.5 text-xs font-medium bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            📄 Save
          </button>
          <button
            onClick={agent.clearConversation}
            disabled={agent.messages.length === 0}
            className="px-3 py-1.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Messages - Professional Assistant UI Style */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {agent.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center mb-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                💬
              </div>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Start a conversation</h3>
            <p className="text-gray-500 text-sm max-w-sm">
              Ask me anything! I have access to your personal context and can help with a wide range of topics.
            </p>
          </div>
        ) : (
          <>
            {agent.messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] lg:max-w-[70%] ${
                    message.role === 'user'
                      ? 'order-2'
                      : 'order-1'
                  }`}
                >
                  {/* Avatar */}
                  <div className={`flex items-end space-x-2 ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
                  }`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {message.role === 'user' ? '👤' : '🧠'}
                    </div>
                    
                    {/* Message Bubble */}
                    <div
                      className={`px-4 py-2 rounded-2xl ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-md'
                          : 'bg-gray-100 text-gray-900 rounded-bl-md'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </p>
                    </div>
                  </div>
                  
                  {/* Timestamp */}
                  <div className={`mt-1 px-10 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    <span className="text-xs text-gray-400">
                      {message.timestamp.toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {agent.isLoading && (
              <div className="flex justify-start">
                <div className="flex items-end space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center text-sm">
                    🧠
                  </div>
                  <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl rounded-bl-md">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-xs text-gray-500">Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input - Professional Assistant UI Style */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        {agent.error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{agent.error}</p>
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1 min-w-0">
            <div className="relative">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type your message..."
                disabled={agent.isLoading}
                className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed resize-none text-sm"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={agent.isLoading || !inputMessage.trim()}
            className="w-10 h-10 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {agent.isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

// JeanAgent Component - Business Case 5-line Integration
interface JeanAgentProps {
  apiKey?: string;
  systemPrompt?: string;
  clientName?: string;
  className?: string;
}

export const JeanAgent: React.FC<JeanAgentProps> = ({ 
  apiKey, 
  systemPrompt, 
  clientName, 
  className = "h-96" 
}) => {
  const agent = useJeanAgent({ apiKey, systemPrompt, clientName });
  const [showLoginForm, setShowLoginForm] = useState(false);

  // Show "Sign In with Jean" button first
  if (!agent.isAuthenticated && !showLoginForm) {
    return (
      <div className={`flex items-center justify-center ${className}`}>
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gray-50 flex items-center justify-center border">
            <img 
              src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBzdHJva2U9IiM2MzYzNjMiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo="
              alt="Jean" 
              className="w-8 h-8"
            />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Connect with Jean Memory</h3>
          <p className="text-gray-600 text-sm mb-6 max-w-sm">
            Access your personalized AI assistant with persistent memory across all your applications.
          </p>
          <button
            onClick={() => setShowLoginForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-black font-medium text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
          >
            Sign In with Jean
            <img 
              src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBzdHJva2U9IiMwMDAwMDAiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo="
              alt="Jean Logo" 
              className="w-4 h-4"
            />
          </button>
        </div>
      </div>
    );
  }

  // Show login form after button click
  if (!agent.isAuthenticated && showLoginForm) {
    return (
      <div className={`p-4 border rounded-lg ${className}`}>
        <div className="max-w-md mx-auto">
          <button 
            onClick={() => setShowLoginForm(false)}
            className="text-sm text-gray-500 hover:text-gray-700 mb-4 flex items-center gap-1"
          >
            ← Back
          </button>
          <SignInWithJean 
            onSuccess={agent.signIn}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <JeanChat agent={agent} className="h-full" />
    </div>
  );
};

// Export types for TypeScript users
export type { JeanUser, JeanAgentConfig, Message };

// Main export for 5-line integration
export { useJeanAgent as default };
