/**
 * Jean Memory React SDK - Sign In With Jean Component
 * OAuth 2.1 PKCE authentication flow
 */
import React, { useEffect, useState } from 'react';
import { JEAN_API_BASE, SUPABASE_URL, SUPABASE_ANON_KEY } from './config';

interface SignInWithJeanProps {
  onSuccess: (user: any) => void;
  onError?: (error: Error) => void;
  apiKey?: string;
  className?: string;
  children?: React.ReactNode;
}

export interface JeanUser {
  sub?: string;
  id?: string;
  email?: string;
  name?: string;
  full_name?: string;
  access_token?: string;
  [key: string]: any;
}

// Utility function to sign out and clear session
export const signOutFromJean = () => {
  // Clear all Jean Memory session data
  localStorage.removeItem('auth_completed');
  localStorage.removeItem('userInfo');
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('userEmail');
  localStorage.removeItem('userName');
  localStorage.removeItem('userId');
  localStorage.removeItem('userAvatar');
  localStorage.removeItem('authProvider');
  localStorage.removeItem('tempUserInfo');
  localStorage.removeItem('using_demo_mode');
  
  // Clear any Supabase session data
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('sb-masapxpxcwvsjpuymbmd-auth-token')) {
      localStorage.removeItem(key);
    }
  });
  
  console.log('✅ SDK OAuth: Signed out successfully');
};

// Generate random string for OAuth session IDs

function generateRandomString(length: number): string {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  const values = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(values)
    .map(x => charset[x % charset.length])
    .join('');
}

// Declare Supabase types (will be loaded from CDN)
declare global {
  interface Window {
    supabase: any;
  }
}

export function SignInWithJean({ 
  onSuccess, 
  onError, 
  apiKey,
  className = '', 
  children 
}: SignInWithJeanProps) {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Handle OAuth callback or SDK auth success
    const params = new URLSearchParams(window.location.search);
    const authSuccess = params.get('auth_success');
    const authToken = params.get('auth_token');
    const authError = params.get('auth_error');
    
    // Only process bridge results if we have explicit auth parameters
    if (authSuccess === 'true' && authToken) {
      handleSDKAuthSuccess(authToken);
    } else if (authSuccess === 'false' && authError) {
      handleSDKAuthError(authError);
    } else if (authSuccess || authToken || authError) {
      // We have some auth params but they're malformed - this is an error
      console.error('Malformed auth parameters from bridge');
      if (onError) {
        onError(new Error('Invalid authentication response'));
      }
    } else {
      // No auth parameters - check for existing session only
      const authCompleted = localStorage.getItem('auth_completed');
      const userInfo = localStorage.getItem('userInfo');
      
      if (authCompleted === 'true' && userInfo) {
        try {
          const user = JSON.parse(userInfo);
          console.log('✅ SDK OAuth: Recovered existing session for user:', user.email);
          onSuccess(user);
          return;
        } catch (error) {
          console.warn('Failed to parse stored user info:', error);
          localStorage.removeItem('auth_completed');
          localStorage.removeItem('userInfo');
        }
      }
      
      // No existing session - this is normal during initialization
      console.log('ℹ️ SDK ready for authentication');
      
      // Legacy OAuth callback support (only if we have both code and state)
      const code = params.get('code');
      const state = params.get('state');
      if (code && state) {
        handleOAuthCallback(code, state);
      }
    }
  }, []);

  const handleSDKAuthSuccess = async (token: string) => {
    try {
      // Parse JWT token directly instead of API call
      const payload = JSON.parse(atob(token.split('.')[1]));
      const user = {
        sub: payload.sub || payload.user_id,
        id: payload.sub || payload.user_id,
        email: payload.email,
        name: payload.name || payload.email?.split('@')[0] || 'User',
        full_name: payload.name,
        access_token: token
      };

      // Store session data in localStorage for persistence (matching bridge format)
      localStorage.setItem('auth_completed', 'true');
      localStorage.setItem('userInfo', JSON.stringify(user));
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('userEmail', user.email || '');
      localStorage.setItem('userName', user.name || user.full_name || '');
      localStorage.setItem('userId', user.sub || user.id || '');
      
      // Clean up URL params
      const url = new URL(window.location.href);
      url.searchParams.delete('auth_success');
      url.searchParams.delete('auth_token');
      url.searchParams.delete('auth_error');
      window.history.replaceState({}, '', url.toString());

      console.log('✅ SDK OAuth: Authentication successful for user:', user.email);
      onSuccess(user);
    } catch (error) {
      console.error('SDK auth success handling error:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('SDK auth handling failed'));
      }
    }
  };

  const handleSDKAuthError = (error: string) => {
    // Clean up URL params
    const url = new URL(window.location.href);
    url.searchParams.delete('auth_success');
    url.searchParams.delete('auth_token');
    url.searchParams.delete('auth_error');
    window.history.replaceState({}, '', url.toString());

    console.error('SDK auth error:', error);
    if (onError) {
      onError(new Error(error));
    }
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    // Legacy OAuth callback - keeping for backward compatibility
    // This should rarely be used with the new SDK OAuth flow
    console.warn('Using legacy OAuth callback - consider updating to SDK OAuth flow');
    
    try {
      // Basic fallback handling
      const url = new URL(window.location.href);
      url.searchParams.delete('code');
      url.searchParams.delete('state');
      window.history.replaceState({}, '', url.toString());
      
      if (onError) {
        onError(new Error('Legacy OAuth callback not fully supported - please use SDK OAuth flow'));
      }
    } catch (error) {
      console.error('OAuth callback error:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('OAuth callback failed'));
      }
    }
  };

  const handleSignIn = async () => {
    setIsLoading(true);
    
    try {
      // Load Supabase SDK if not already loaded
      if (!window.supabase) {
        await loadSupabaseSDK();
      }

      // Initialize Supabase client
      const supabaseClient = window.supabase.createClient(
        SUPABASE_URL,
        SUPABASE_ANON_KEY,
        {
          auth: {
            detectSessionInUrl: false,
            flowType: 'pkce'
          }
        }
      );

      // Store redirect info for the bridge
      sessionStorage.setItem('jean_final_redirect', window.location.origin + window.location.pathname);
      
      // Generate OAuth session ID
      const oauthSession = generateRandomString(32);
      
      // Build redirect URL with SDK OAuth flow parameters
      const bridgeUrl = new URL('https://jeanmemory.com/oauth-bridge.html');
      bridgeUrl.searchParams.set('oauth_session', oauthSession);
      bridgeUrl.searchParams.set('flow', 'sdk_oauth');
      bridgeUrl.searchParams.set('api_key', apiKey || 'default_client');
      
      console.log('🔄 SDK OAuth: Redirecting to bridge URL:', bridgeUrl.toString());
      
      // Sign in with Supabase - this will redirect to the bridge with auth tokens
      const { error } = await supabaseClient.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: bridgeUrl.toString()
        }
      });

      if (error) {
        throw error;
      }
      
      // If we get here, the redirect is happening
      // The bridge will handle the token exchange and redirect back
    } catch (error) {
      setIsLoading(false);
      console.error('Sign in error:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('Sign in failed'));
      }
    }
  };

  const loadSupabaseSDK = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (window.supabase) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Supabase SDK'));
      document.head.appendChild(script);
    });
  };

  return (
    <button
      onClick={handleSignIn}
      disabled={isLoading}
      className={`inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-sm rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-300 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {isLoading ? (
        <>
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
          <span>Signing in...</span>
        </>
      ) : children || (
        <>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z" 
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>Sign In with Jean</span>
        </>
      )}
    </button>
  );
}