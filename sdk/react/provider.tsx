/**
 * Jean Memory React SDK - Provider Component
 * Manages authentication state and API client
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { JEAN_API_BASE } from './config';
import { makeMCPRequest } from './mcp';

const JEAN_API_BASE_OLD = 'https://jean-memory-api-virginia.onrender.com';

export interface JeanUser {
  user_id: string;
  email: string;
  name?: string;
  access_token: string;
}

export interface JeanMessage {
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
  setError: (error: string | null) => void;
  
  // Tools
  tools: {
    add_memory: (content: string) => Promise<any>;
    search_memory: (query: string) => Promise<any>;
  };
  
  // Config
  apiKey?: string;
}

export interface MessageOptions {
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
  const [rawError, setRawError] = useState<string | null>(null);

  // Validate API key on mount
  useEffect(() => {
    if (!apiKey) {
      setRawError('API key is required');
      return;
    }
    
    if (!apiKey.startsWith('jean_sk_')) {
      setRawError('Invalid API key format');
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
    setRawError(null);

    // Extract configuration options with defaults
    const { speed = 'balanced', tool = 'jean_memory', format = 'enhanced' } = options;

    try {
      // Add user message to conversation
      const userMessage: JeanMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: message,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);

      const response = await makeMCPRequest(
        user,
        apiKey,
        options.tool || 'jean_memory',
        {
          user_message: message,
          is_new_conversation: messages.length <= 1,
          needs_context: true
          // Removed ...options spread - backend doesn't support speed/format yet
        }
      );

      if (response.error) {
        throw new Error(response.error.message);
      }
      
      const assistantMessage: JeanMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.result?.content?.[0]?.text || 'I understood and saved that information.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setRawError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const storeDocument = async (title: string, content: string): Promise<void> => {
    if (!user) {
      throw new Error("User not authenticated");
    }
    const response = await makeMCPRequest(user, apiKey, 'store_document', {
      title,
      content,
      document_type: 'markdown'
    });
    if (response.error) {
      throw new Error(response.error.message);
    }
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

  const setError = (error: string | null) => {
    setRawError(error);
  };

  const tools = {
    add_memory: async (content: string) => {
      if (!user) throw new Error('User not authenticated');
      const response = await makeMCPRequest(user, apiKey, 'add_memories', { text: content });
      if (response.error) {
        throw new Error(response.error.message);
      }
      return response;
    },
    
    search_memory: async (query: string) => {
      if (!user) throw new Error('User not authenticated');
      const response = await makeMCPRequest(user, apiKey, 'search_memory', { query });
      if (response.error) {
        throw new Error(response.error.message);
      }
      return response;
    }
  };

  const contextValue: JeanContextValue = {
    // State
    isAuthenticated: !!user,
    user,
    messages,
    isLoading,
    error: rawError,
    
    // Methods
    sendMessage,
    storeDocument,
    connect,
    clearConversation,
    setUser: handleSetUser,
    signOut,
    setError: setRawError,
    
    // Tools
    tools,
    
    // Config
    apiKey
  };

  return (
    <JeanContext.Provider value={contextValue}>
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