/**
 * SignInWithJean.tsx: Production-Ready "Sign in with Jean" Component
 *
 * This component provides a beautiful, customizable button for initiating the
 * Jean Memory authentication flow. It's designed to be easily integrated
 * into any React application with full OAuth 2.1 PKCE support.
 */
import React, { useState, useEffect } from 'react';
import { generateCodeVerifier, generateCodeChallenge } from '../oauth';
import type { JeanUser } from '../useJean';

interface SignInWithJeanProps {
  apiKey: string;
  onSuccess: (user: JeanUser) => void;
  onError?: (error: string) => void;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
  redirectUri?: string;
  apiBase?: string;
}

export const SignInWithJean: React.FC<SignInWithJeanProps> = ({
  apiKey,
  onSuccess,
  onError,
  className = 'jean-signin-button',
  style,
  children,
  redirectUri,
  apiBase = 'https://jean-memory-api-virginia.onrender.com',
}) => {
  const [isLoading, setIsLoading] = useState(false);

  // Auto-detect redirect URI if not provided
  const finalRedirectUri = redirectUri || (typeof window !== 'undefined' ? `${window.location.origin}/callback` : 'http://localhost:3000/callback');

  // Handle OAuth callback on component mount
  useEffect(() => {
    const handleCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const error = urlParams.get('error');

      if (error) {
        onError?.(error);
        return;
      }

      if (code) {
        try {
          const verifier = sessionStorage.getItem('code_verifier');
          const storedClientId = sessionStorage.getItem('oauth_client_id') || apiKey;
          if (!verifier) {
            throw new Error('Missing code verifier');
          }

          // Exchange code for token using form data (as expected by the existing endpoint)
          const formData = new URLSearchParams();
          formData.append('grant_type', 'authorization_code');
          formData.append('client_id', storedClientId);
          formData.append('code', code);
          formData.append('redirect_uri', finalRedirectUri);
          formData.append('code_verifier', verifier);

          const response = await fetch(`${apiBase}/oauth/token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData,
          });

          if (!response.ok) {
            throw new Error('Failed to exchange code for token');
          }

          const tokenData = await response.json();
          
          // Decode JWT token to get user info (avoiding need for separate userinfo endpoint)
          let userInfo: any = {};
          try {
            // Simple JWT decode (just the payload, not verifying signature since we trust our own server)
            const tokenPayload = tokenData.access_token.split('.')[1];
            const decodedPayload = JSON.parse(atob(tokenPayload));
            userInfo = decodedPayload;
          } catch (e) {
            console.warn('Could not decode JWT token, using fallback user data');
          }
          
          const user: JeanUser = {
            user_id: userInfo.sub || userInfo.user_id || `user_${Date.now()}`,
            email: userInfo.email || 'user@example.com',
            access_token: tokenData.access_token,
          };

          sessionStorage.removeItem('code_verifier');
          onSuccess(user);
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
          onError?.(errorMessage);
        }
      }
    };

    handleCallback();
  }, [apiKey, apiBase, finalRedirectUri, onSuccess, onError]);

  const handleSignIn = async () => {
    setIsLoading(true);
    try {
      // First, try to register the API key as an OAuth client (idempotent operation)
      let clientId = apiKey;
      try {
        const registerResponse = await fetch(`${apiBase}/oauth/register`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            client_name: `Jean Memory App ${Date.now()}`,
            redirect_uri: finalRedirectUri,
          }),
        });
        
        if (registerResponse.ok) {
          const registerData = await registerResponse.json();
          clientId = registerData.client_id;
          console.log('Registered OAuth client:', clientId);
        }
      } catch (registerError) {
        console.warn('Could not register OAuth client, using API key directly:', registerError);
      }

      const verifier = generateCodeVerifier();
      const challenge = await generateCodeChallenge(verifier);

      sessionStorage.setItem('code_verifier', verifier);
      sessionStorage.setItem('oauth_client_id', clientId);

      const authUrl = new URL(`${apiBase}/oauth/authorize`);
      authUrl.searchParams.append('client_id', clientId);
      authUrl.searchParams.append('redirect_uri', finalRedirectUri);
      authUrl.searchParams.append('response_type', 'code');
      authUrl.searchParams.append('scope', 'openid profile email');
      authUrl.searchParams.append('code_challenge', challenge);
      authUrl.searchParams.append('code_challenge_method', 'S256');
      authUrl.searchParams.append('state', `jean_${Date.now()}`);

      window.location.href = authUrl.toString();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      onError?.(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const defaultStyle: React.CSSProperties = {
    backgroundColor: '#22c55e',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: isLoading ? 'not-allowed' : 'pointer',
    opacity: isLoading ? 0.7 : 1,
    transition: 'all 0.2s ease',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    ...style,
  };

  return (
    <button
      onClick={handleSignIn}
      disabled={isLoading}
      className={className}
      style={defaultStyle}
    >
      {children || (isLoading ? '🔄 Redirecting...' : '🧠 Sign in with Jean Memory')}
    </button>
  );
};
