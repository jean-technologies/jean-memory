/**
 * Jean Memory React SDK v2.0 - Provider Component
 * Secure OAuth 2.1 PKCE with JWT-in-header authentication
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { JEAN_API_BASE } from './config';
import { getUserSession, isAuthenticated as checkAuth, getUserToken } from './oauth';

export interface JeanUser {
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

export interface MessageOptions {
  speed?: 'fast' | 'balanced' | 'comprehensive';
  format?: 'simple' | 'enhanced';
}

interface JeanContextValue {
  // Authentication state
  isAuthenticated: boolean;
  isLoading: boolean;
  user: JeanUser | null;
  error: string | null;
  
  // Messaging
  messages: JeanMessage[];
  sendMessage: (message: string, options?: MessageOptions) => Promise<string>;
  clearConversation: () => void;
  
  // Memory management
  addMemory: (content: string) => Promise<any>;
  searchMemory: (query: string) => Promise<any>;
  
  // Internal (used by SignInWithJean)
  setUser: (user: JeanUser) => void;
  apiKey: string;
}

const JeanContext = createContext<JeanContextValue | null>(null);

interface JeanProviderProps {
  apiKey: string;
  children: ReactNode;
}

export function JeanProvider({ apiKey, children }: JeanProviderProps) {
  const [user, setUserState] = useState<JeanUser | null>(null);
  const [messages, setMessages] = useState<JeanMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize authentication state from stored session
  useEffect(() => {
    const storedUser = getUserSession();
    if (storedUser && checkAuth()) {
      setUserState(storedUser);
    }
  }, []);

  const setUser = (newUser: JeanUser) => {
    setUserState(newUser);
    setError(null);
  };

  const sendMessage = async (message: string, options?: MessageOptions): Promise<string> => {
    if (!user) {
      throw new Error('User must be authenticated to send messages');
    }

    setIsLoading(true);
    setError(null);

    try {
      // SECURE: JWT token in Authorization header, API key in X-API-Key header
      const response = await fetch(`${JEAN_API_BASE}/api/jean-chat`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user.access_token}`,  // User identity (JWT)
          'X-API-Key': apiKey,  // App authentication
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message,
          format: options?.format || 'enhanced'
        })
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Request failed: ${response.status} - ${errorData}`);
      }

      const data = await response.json();
      
      // Add messages to conversation
      const userMessage: JeanMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: message,
        timestamp: new Date()
      };

      const assistantMessage: JeanMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant', 
        content: data.content || data.context || 'No response received',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage, assistantMessage]);
      
      return assistantMessage.content;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const addMemory = async (content: string): Promise<any> => {
    if (!user) {
      throw new Error('User must be authenticated to add memories');
    }

    const response = await fetch(`${JEAN_API_BASE}/mcp/tools/call`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.access_token}`,
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'add_memory',
        arguments: { content }
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to add memory: ${response.status}`);
    }

    return response.json();
  };

  const searchMemory = async (query: string): Promise<any> => {
    if (!user) {
      throw new Error('User must be authenticated to search memories');
    }

    const response = await fetch(`${JEAN_API_BASE}/mcp/tools/call`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.access_token}`,
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'search_memory',
        arguments: { query }
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to search memory: ${response.status}`);
    }

    return response.json();
  };

  const clearConversation = () => {
    setMessages([]);
    setError(null);
  };

  const contextValue: JeanContextValue = {
    // Authentication state
    isAuthenticated: !!user && checkAuth(),
    isLoading,
    user,
    error,
    
    // Messaging
    messages,
    sendMessage,
    clearConversation,
    
    // Memory management
    addMemory,
    searchMemory,
    
    // Internal
    setUser,
    apiKey
  };

  return (
    <JeanContext.Provider value={contextValue}>
      {children}
    </JeanContext.Provider>
  );
}

export function useJean(): JeanContextValue {
  const context = useContext(JeanContext);
  if (!context) {
    throw new Error('useJean must be used within a JeanProvider');
  }
  return context;
}