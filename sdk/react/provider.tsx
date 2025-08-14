/**
 * Jean Memory React SDK - Provider Component
 * Manages authentication state and API client
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

interface JeanUser {
  user_id: string;
  email: string;
  name?: string;
  access_token: string;
}

interface JeanMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface JeanContextValue {
  // State
  isAuthenticated: boolean;
  user: JeanUser | null;
  messages: JeanMessage[];
  isLoading: boolean;
  error: string | null;
  
  // Methods
  sendMessage: (message: string, options?: MessageOptions) => Promise<void>;
  storeDocument: (title: string, content: string) => Promise<void>;
  connect: (service: 'notion' | 'slack' | 'gdrive') => void;
  clearConversation: () => void;
  setUser: (user: JeanUser) => void;
  signOut: () => void;
  
  // Tools
  tools: {
    add_memory: (content: string) => Promise<any>;
    search_memory: (query: string) => Promise<any>;
  };
  
  // Config
  apiKey?: string;
}

interface MessageOptions {
  speed?: 'fast' | 'balanced' | 'comprehensive';
  tool?: 'jean_memory' | 'search_memory';
  format?: 'simple' | 'enhanced';
}

const JeanContext = createContext<JeanContextValue | null>(null);

interface JeanProviderProps {
  apiKey: string;
  children: ReactNode;
}

export function JeanProvider({ apiKey, children }: JeanProviderProps) {
  const [user, setUser] = useState<JeanUser | null>(null);
  const [messages, setMessages] = useState<JeanMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validate API key on mount
  useEffect(() => {
    if (!apiKey) {
      setError('API key is required');
      return;
    }
    
    if (!apiKey.startsWith('jean_sk_')) {
      setError('Invalid API key format');
      return;
    }

    // API key will be validated on first request
    console.log('✅ Jean Memory SDK initialized');
  }, [apiKey]);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem('jean_user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('jean_user');
      }
    }
  }, []);

  const sendMessage = async (message: string, options: MessageOptions = {}) => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    setIsLoading(true);
    setError(null);

    try {
      // Add user message to conversation
      const userMessage: JeanMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);

      // Use MCP endpoint to get context
      const response = await fetch(`${JEAN_API_BASE}/api/v1/sdk/mcp/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          messages: [{ role: 'user', content: message }],
          user_id: user.user_id
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get context');
      }

      const data = await response.json();
      
      // Add assistant response to conversation
      const assistantMessage: JeanMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || data.text || 'I understood and saved that information.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const storeDocument = async (title: string, content: string) => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    // Store as a memory with special formatting
    const formattedContent = `# ${title}\n\n${content}`;
    return tools.add_memory(formattedContent);
  };

  const connect = (service: 'notion' | 'slack' | 'gdrive') => {
    if (!user) {
      throw new Error('User not authenticated');
    }
    
    // Open OAuth flow for external service integration
    const integrationUrl = `${JEAN_API_BASE}/api/v1/integrations/${service}/connect?user_token=${user.access_token}`;
    
    // Open in new window for better UX
    const popup = window.open(
      integrationUrl,
      `connect-${service}`,
      'width=600,height=700,scrollbars=yes,resizable=yes'
    );
    
    // Listen for completion
    const checkClosed = setInterval(() => {
      if (popup?.closed) {
        clearInterval(checkClosed);
        console.log(`${service} integration window closed`);
        // Could refresh integrations list here
      }
    }, 1000);
  };

  const clearConversation = () => {
    setMessages([]);
  };

  const handleSetUser = (newUser: JeanUser) => {
    setUser(newUser);
    localStorage.setItem('jean_user', JSON.stringify(newUser));
  };

  const signOut = () => {
    setUser(null);
    setMessages([]);
    localStorage.removeItem('jean_user');
  };

  const tools = {
    add_memory: async (content: string) => {
      if (!user) throw new Error('User not authenticated');
      
      // Use MCP tool endpoint
      const response = await fetch(`${JEAN_API_BASE}/mcp/messages/${user.user_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'tools/call',
          params: {
            name: 'add_memories',
            arguments: { text: content }
          }
        })
      });
      
      if (!response.ok) throw new Error('Failed to add memory');
      return response.json();
    },
    
    search_memory: async (query: string) => {
      if (!user) throw new Error('User not authenticated');
      
      // Use MCP tool endpoint
      const response = await fetch(`${JEAN_API_BASE}/mcp/messages/${user.user_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          id: Date.now(),
          method: 'tools/call',
          params: {
            name: 'search_memory',
            arguments: { query }
          }
        })
      });
      
      if (!response.ok) throw new Error('Failed to search memory');
      return response.json();
    }
  };

  const value: JeanContextValue = {
    // State
    isAuthenticated: !!user,
    user,
    messages,
    isLoading,
    error,
    
    // Methods
    sendMessage,
    storeDocument,
    connect,
    clearConversation,
    setUser: handleSetUser,
    signOut,
    
    // Tools
    tools,
    
    // Config
    apiKey
  };

  return (
    <JeanContext.Provider value={value}>
      {children}
    </JeanContext.Provider>
  );
}

export function useJean() {
  const context = useContext(JeanContext);
  if (!context) {
    throw new Error('useJean must be used within a JeanProvider');
  }
  return context;
}