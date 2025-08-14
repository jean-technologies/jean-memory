/**
 * Jean Memory React SDK - Sign In With Jean Component
 * OAuth 2.1 PKCE authentication flow
 */
import React, { useEffect, useState } from 'react';
import { JEAN_API_BASE, JEAN_OAUTH_BASE } from './config';

interface SignInWithJeanProps {
  onSuccess: (user: any) => void;
  onError?: (error: Error) => void;
  apiKey?: string;
  className?: string;
  children?: React.ReactNode;
}

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

export function SignInWithJean({ 
  onSuccess, 
  onError, 
  apiKey,
  className = '', 
  children 
}: SignInWithJeanProps) {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Handle OAuth callback
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    
    if (code && state) {
      handleOAuthCallback(code, state);
    }
  }, []);

  const handleOAuthCallback = async (code: string, state: string) => {
    try {
      // Retrieve PKCE verifier from sessionStorage
      const storedState = sessionStorage.getItem('jean_oauth_state');
      const verifier = sessionStorage.getItem('jean_oauth_verifier');
      
      if (state !== storedState) {
        throw new Error('State mismatch - possible CSRF attack');
      }
      
      if (!verifier) {
        throw new Error('Missing PKCE verifier');
      }

      // Exchange code for token
      const response = await fetch(`${JEAN_API_BASE}/oauth/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          grant_type: 'authorization_code',
          code,
          redirect_uri: window.location.origin + window.location.pathname,
          code_verifier: verifier,
          client_id: apiKey || 'default_client'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to exchange code for token');
      }

      const data = await response.json();
      
      // Get user info
      const userResponse = await fetch(`${JEAN_API_BASE}/api/v1/user/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`
        }
      });

      if (!userResponse.ok) {
        throw new Error('Failed to get user info');
      }

      const user = await userResponse.json();
      user.access_token = data.access_token;

      // Clean up
      sessionStorage.removeItem('jean_oauth_state');
      sessionStorage.removeItem('jean_oauth_verifier');
      
      // Remove OAuth params from URL
      const url = new URL(window.location.href);
      url.searchParams.delete('code');
      url.searchParams.delete('state');
      window.history.replaceState({}, '', url.toString());

      onSuccess(user);
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
      window.location.href = `${JEAN_OAUTH_BASE}/oauth/authorize?${params.toString()}`;
    } catch (error) {
      setIsLoading(false);
      console.error('Sign in error:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('Sign in failed'));
      }
    }
  };

  return (
    <button
      onClick={handleSignIn}
      disabled={isLoading}
      className={`inline-flex items-center gap-2 px-4 py-2.5 bg-white text-black font-medium text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      {children || (
        <>
          <span>Sign In with Jean</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z" 
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </>
      )}
    </button>
  );
}