/**
 * Jean Memory React SDK - Provider Component
 * Manages authentication state and API client
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { JEAN_API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY } from './config';
import { makeMCPRequest } from './mcp';

// Declare Supabase types (will be loaded from CDN)
declare global {
  interface Window {
    supabase: any;
  }
}

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
  const [supabase, setSupabase] = useState<any>(null);

  // Initialize Supabase client
  useEffect(() => {
    const initSupabase = async () => {
      // Load Supabase from CDN if not already loaded
      if (!window.supabase) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
        script.onload = () => {
          const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            auth: {
              detectSessionInUrl: true,
              flowType: 'pkce'
            }
          });
          setSupabase(client);
        };
        document.head.appendChild(script);
      } else {
        const client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
          auth: {
            detectSessionInUrl: true,
            flowType: 'pkce'
          }
        });
        setSupabase(client);
      }
    };

    initSupabase();
  }, []);

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

    // Check if this is a test API key and auto-initialize test user
    if (apiKey.includes('test')) {
      console.log('🧪 Test API key detected - initializing test user mode');
      initializeTestUser();
      return;
    }

    // Handle OAuth completion from bridge
    const handleOAuthCompletion = async () => {
      const params = new URLSearchParams(window.location.search);
      const authSuccess = params.get('auth_success');
      const authToken = params.get('auth_token');
      const authError = params.get('auth_error');
      
      if (authSuccess === 'true' && authToken) {
        setIsLoading(true);
        try {
          // Get user info from Jean Memory API using the token
          const userResponse = await fetch(`${JEAN_API_BASE}/oauth/userinfo`, {
            headers: { Authorization: `Bearer ${authToken}` }
          });
          
          if (userResponse.ok) {
            const userInfo = await userResponse.json();
            const user: JeanUser = {
              user_id: userInfo.sub,
              email: userInfo.email,
              name: userInfo.name,
              access_token: authToken
            };
            
            handleSetUser(user);
            console.log('✅ OAuth authentication completed');
            
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
          } else {
            throw new Error('Failed to get user info');
          }
        } catch (error) {
          console.error('OAuth completion error:', error);
          setRawError('Authentication completed but failed to get user info');
        } finally {
          setIsLoading(false);
        }
      } else if (authError) {
        setRawError(`Authentication failed: ${authError}`);
        setIsLoading(false);
      }
    };

    handleOAuthCompletion();

    // Handle OAuth redirect (legacy PKCE flow - kept for backward compatibility)
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
          const tokenResponse = await fetch(`${JEAN_API_BASE}/oauth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              grant_type: 'authorization_code',
              code,
              client_id: apiKey,
              redirect_uri: 'https://jeanmemory.com/oauth-bridge.html',  // Must match the redirect_uri used in authorization
              code_verifier: verifier
            }),
          });

          if (!tokenResponse.ok) {
            const errorData = await tokenResponse.json();
            throw new Error(errorData.detail || 'Token exchange failed');
          }

          const { access_token } = await tokenResponse.json();

          // Get user info
          const userInfoResponse = await fetch(`${JEAN_API_BASE}/oauth/userinfo`, {
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
          console.error('OAuth callback error:', errorMessage);
          
          // Fallback to test user if OAuth fails and we have a test API key
          if (apiKey.includes('test')) {
            console.log('🧪 OAuth failed with test API key - falling back to test user mode');
            await initializeTestUser();
          } else {
            setRawError(errorMessage);
          }
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
        user_id: testUserId,
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
    if (!supabase) {
      setRawError('Authentication system not ready. Please try again.');
      return;
    }

    setIsLoading(true);
    setRawError(null);
    
    try {
      // Generate session ID for bridge coordination
      const sessionId = generateRandomString(32);
      sessionStorage.setItem('jean_oauth_session', sessionId);
      sessionStorage.setItem('jean_api_key', apiKey);
      
      // Use Supabase OAuth with bridge coordination (like Claude)
      const bridgeUrl = `https://jeanmemory.com/oauth-bridge.html?oauth_session=${sessionId}&flow=sdk_oauth`;
      
      const { error: signInError } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: bridgeUrl,
          queryParams: {
            oauth_session: sessionId,
            flow: 'sdk_oauth',
            api_key: apiKey
          }
        }
      });

      if (signInError) {
        console.error('Supabase OAuth error:', signInError);
        setRawError('Sign in failed. Please try again.');
        setIsLoading(false);
      }
      // Loading will be cleared when auth completes
    } catch (error) {
      setIsLoading(false);
      const errorMessage = error instanceof Error ? error.message : 'Sign in failed';
      setRawError(errorMessage);
    }
  };

  const handleSetUser = (newUser: JeanUser) => {
    setUser(newUser);
    localStorage.setItem('jean_user', JSON.stringify(newUser));
    setRawError(null); // Clear any auth errors
  };

  const signOut = () => {
    setUser(null);
    setMessages([]);
    setRawError(null);
    localStorage.removeItem('jean_user');
    sessionStorage.removeItem('jean_oauth_state');
    sessionStorage.removeItem('jean_oauth_verifier');
    console.log('👋 User signed out');
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