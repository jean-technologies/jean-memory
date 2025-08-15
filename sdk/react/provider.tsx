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
  // Essential state
  isAuthenticated: boolean;
  isLoading: boolean;
  user: JeanUser | null;
  messages: JeanMessage[];
  error: string | null;
  
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

// Generate code verifier and challenge for PKCE
function generatePKCE() {
  const verifier = generateRandomString(128);
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  
  return crypto.subtle.digest('SHA-256', data).then(digest => {
    const challenge = btoa(String.fromCharCode(...new Uint8Array(digest)))
      .replace(/=/g, '')
      .replace(/\+/g, '-')
      .replace(/\//g, '_');
    return { verifier, challenge };
  });
}

function generateRandomString(length: number): string {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  const values = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(values)
    .map(x => charset[x % charset.length])
    .join('');
}

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

    // Handle OAuth redirect
    const handleOAuthRedirect = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get('code');
      const state = params.get('state');
      const storedState = sessionStorage.getItem('jean_oauth_state');
      const verifier = sessionStorage.getItem('jean_oauth_verifier');

      if (code && state && storedState && verifier) {
        setIsLoading(true);
        if (state !== storedState) {
          setRawError('Invalid OAuth state');
          setIsLoading(false);
          return;
        }

        try {
          // Exchange code for token
          const tokenResponse = await fetch(`${JEAN_API_BASE}/sdk/oauth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              grant_type: 'authorization_code',
              code,
              client_id: apiKey,
              redirect_uri: window.location.origin + window.location.pathname,
              code_verifier: verifier
            }),
          });

          if (!tokenResponse.ok) {
            const errorData = await tokenResponse.json();
            throw new Error(errorData.detail || 'Token exchange failed');
          }

          const { access_token } = await tokenResponse.json();

          // Get user info
          const userInfoResponse = await fetch(`${JEAN_API_BASE}/sdk/oauth/userinfo`, {
            headers: { Authorization: `Bearer ${access_token}` },
          });

          if (!userInfoResponse.ok) {
            throw new Error('Failed to fetch user info');
          }

          const userInfo = await userInfoResponse.json();
          
          const user: JeanUser = {
            user_id: userInfo.sub,
            email: userInfo.email,
            name: userInfo.name,
            access_token,
          };

          handleSetUser(user);

          // Clean up URL
          window.history.replaceState({}, document.title, window.location.pathname);
          sessionStorage.removeItem('jean_oauth_state');
          sessionStorage.removeItem('jean_oauth_verifier');

        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'OAuth flow failed';
          setRawError(errorMessage);
        } finally {
          setIsLoading(false);
        }
      }
    };

    handleOAuthRedirect();
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
        { query }
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

  const signIn = async () => {
    setIsLoading(true);
    
    try {
      // Generate PKCE parameters
      const { verifier, challenge } = await generatePKCE();
      const state = generateRandomString(32);
      
      // Store for callback
      sessionStorage.setItem('jean_oauth_state', state);
      sessionStorage.setItem('jean_oauth_verifier', verifier);
      
      // Build OAuth URL
      const params = new URLSearchParams({
        response_type: 'code',
        client_id: apiKey || 'default_client',
        redirect_uri: window.location.origin + window.location.pathname,
        state,
        code_challenge: challenge,
        code_challenge_method: 'S256',
        scope: 'read write'
      });
      
      // Redirect to OAuth provider
      window.location.href = `${JEAN_API_BASE}/oauth/authorize?${params.toString()}`;
    } catch (error) {
      setIsLoading(false);
      const errorMessage = error instanceof Error ? error.message : 'Sign in failed';
      setRawError(errorMessage);
    }
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

  const contextValue: JeanContextValue = {
    // Essential state
    isAuthenticated: !!user,
    isLoading,
    user,
    messages,
    error: rawError,
    
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