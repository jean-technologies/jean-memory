/**
 * Jean Memory React SDK - Provider Component
 * Manages authentication state and API client
 */
import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { JEAN_API_BASE } from './config';
import { makeMCPRequest } from './mcp';
import { 
  getUserSession, 
  isAuthenticated as checkAuth, 
  initiateOAuth, 
  handleOAuthCallback,
  clearUserSession,
  storeUserSession,
  JeanUser
} from './oauth';

// Re-export JeanUser type
export type { JeanUser };

export interface JeanMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface JeanContextValue {
  // Essential state
  isAuthenticated: boolean;
  isLoading: boolean;
  user: JeanUser | null;
  messages: JeanMessage[];
  error: string | null;
  apiKey: string;
  
  // Essential methods
  signIn: () => void;
  signOut: () => void;
  sendMessage: (message: string, options?: MessageOptions) => Promise<void>;
  storeDocument: (title: string, content: string) => Promise<void>;
  connect: (service: 'notion' | 'slack' | 'gdrive') => void;
  clearConversation: () => void;
  setUser: (user: JeanUser) => void;
  
  // Tools for direct memory access
  tools: {
    add_memory: (content: string) => Promise<any>;
    search_memory: (query: string) => Promise<any>;
    deep_memory_query: (query: string) => Promise<any>;
    store_document: (title: string, content: string, document_type?: string) => Promise<any>;
  };
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
  const [isInitialized, setIsInitialized] = useState(false);
  const oAuthHandled = useRef(false);

  // Initialize OAuth and check for existing session
  useEffect(() => {
    
    const initAuth = async () => {
      setIsLoading(true);
      
      try {
        // Check for OAuth callback parameters - handle only once per page load
        const params = new URLSearchParams(window.location.search);
        if (params.has('code') && params.has('state') && !oAuthHandled.current) {
          // Mark as handled immediately to prevent re-entry
          oAuthHandled.current = true;
          
          console.log('🔄 Jean OAuth: Processing callback in Provider...');
          const callbackUser = await handleOAuthCallback();
          if (callbackUser) {
            setUser(callbackUser);
            console.log('✅ OAuth authentication completed');
            
            // Clean up URL parameters while preserving other query params
            const url = new URL(window.location.href);
            url.searchParams.delete('code');
            url.searchParams.delete('state');
            url.searchParams.delete('error');
            url.searchParams.delete('error_description');
            window.history.replaceState({}, document.title, url.toString());
            
            setIsInitialized(true);
            setIsLoading(false);
            return;
          }
        }
        
        // Check for existing session
        const existingSession = getUserSession();
        if (existingSession) {
          setUser(existingSession);
          console.log('✅ Restored existing session');
        }
        
        setIsInitialized(true);
      } catch (error) {
        console.error('Auth initialization error:', error);
        setRawError(error instanceof Error ? error.message : 'Authentication failed');
        oAuthHandled.current = false; // Reset on error for potential retry
      } finally {
        setIsLoading(false);
      }
    };
    
    initAuth();
  }, []);


  // Handle OAuth completion and API key validation
  useEffect(() => {
    if (!apiKey) {
      setRawError('API key is required');
      return;
    }
    
    if (!apiKey.startsWith('jean_sk_')) {
      setRawError('Invalid API key format');
      return;
    }

    console.log('✅ Jean Memory SDK initialized');

    // Check if this is a test API key and auto-initialize test user
    if (apiKey.includes('test')) {
      console.log('🧪 Test API key detected - initializing test user mode');
      initializeTestUser();
      return;
    }

    // Validate API key on mount
    if (!apiKey || !apiKey.startsWith('jean_sk_')) {
      setRawError('Invalid or missing API key');
    }
  }, [apiKey]);


  const sendMessage = async (message: string, options: MessageOptions = {}) => {
    if (!user) {
      throw new Error('User not authenticated');
    }

    setIsLoading(true);
    setRawError(null);

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

  // Direct memory tools
  const tools = {
    add_memory: async (content: string) => {
      if (!user) {
        throw new Error('User not authenticated');
      }
      
      const response = await makeMCPRequest(
        user,
        apiKey,
        'add_memory',
        { content }
      );
      
      if (response.error) {
        throw new Error(response.error.message);
      }
      
      return response.result;
    },
    
    search_memory: async (query: string) => {
      if (!user) {
        throw new Error('User not authenticated');
      }
      
      const response = await makeMCPRequest(
        user,
        apiKey,
        'search_memory',
        { query }
      );
      
      if (response.error) {
        throw new Error(response.error.message);
      }
      
      return response.result;
    },

    deep_memory_query: async (query: string) => {
      if (!user) {
        throw new Error('User not authenticated');
      }
      
      const response = await makeMCPRequest(
        user,
        apiKey,
        'deep_memory_query',
        { search_query: query }
      );
      
      if (response.error) {
        throw new Error(response.error.message);
      }
      
      return response.result;
    },

    store_document: async (title: string, content: string, document_type: string = 'markdown') => {
      if (!user) {
        throw new Error('User not authenticated');
      }
      
      const response = await makeMCPRequest(
        user,
        apiKey,
        'store_document',
        { title, content, document_type }
      );
      
      if (response.error) {
        throw new Error(response.error.message);
      }
      
      return response.result;
    }
  };

  // Initialize test user for development/testing
  const initializeTestUser = async () => {
    if (!apiKey.includes('test')) {
      setRawError('Test user initialization only available with test API keys');
      return;
    }
    
    try {
      setIsLoading(true);
      
      // Generate consistent test user ID from API key
      const encoder = new TextEncoder();
      const data = encoder.encode(apiKey);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map(b => {
        const hex = b.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
      }).join('').substring(0, 8);
      const testUserId = `test_user_${hashHex}`;
      
      // Create test user object
      const testUser: JeanUser = {
        email: 'test@example.com',
        name: 'Test User',
        access_token: `test_token_${hashHex}`
      };
      
      console.log('🧪 Test user initialized:', testUser);
      handleSetUser(testUser);
      
    } catch (error) {
      setRawError('Failed to initialize test user');
      console.error('Test user initialization error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const signIn = async () => {
    if (!isInitialized) {
      setRawError('Authentication system not ready. Please try again.');
      return;
    }

    setIsLoading(true);
    setRawError(null);
    
    try {
      // Use Universal OAuth 2.1 PKCE flow
      await initiateOAuth({ 
        apiKey,
        redirectUri: window.location.origin + window.location.pathname
      });
      // User will be redirected to Google OAuth
    } catch (error) {
      setIsLoading(false);
      const errorMessage = error instanceof Error ? error.message : 'Sign in failed';
      setRawError(errorMessage);
    }
  };

  const handleSetUser = (newUser: JeanUser) => {
    setUser(newUser);
    storeUserSession(newUser);
    setRawError(null); // Clear any auth errors
  };

  const signOut = async () => {
    // Clear all session data
    clearUserSession();
    setUser(null);
    setMessages([]);
    setRawError(null);
    console.log('👋 User signed out');
  };

  const contextValue: JeanContextValue = {
    // Essential state
    isAuthenticated: !!user,
    isLoading,
    user,
    messages,
    error: rawError,
    apiKey,
    
    // Essential methods
    signIn,
    signOut,
    sendMessage,
    storeDocument,
    connect,
    clearConversation,
    setUser: handleSetUser,
    
    // Tools
    tools
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