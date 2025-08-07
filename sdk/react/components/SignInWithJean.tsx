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
          if (!verifier) {
            throw new Error('Missing code verifier');
          }

          // Exchange code for token
          const response = await fetch(`${apiBase}/sdk/oauth/token`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              grant_type: 'authorization_code',
              client_id: apiKey,
              code,
              redirect_uri: finalRedirectUri,
              code_verifier: verifier,
            }),
          });

          if (!response.ok) {
            throw new Error('Failed to exchange code for token');
          }

          const tokenData = await response.json();
          
          // Get user info
          const userResponse = await fetch(`${apiBase}/sdk/oauth/userinfo`, {
            headers: {
              Authorization: `Bearer ${tokenData.access_token}`,
            },
          });

          if (!userResponse.ok) {
            throw new Error('Failed to get user info');
          }

          const userData = await userResponse.json();
          
          const user: JeanUser = {
            user_id: userData.sub,
            email: userData.email,
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
      const verifier = generateCodeVerifier();
      const challenge = await generateCodeChallenge(verifier);

      sessionStorage.setItem('code_verifier', verifier);

      const authUrl = new URL(`${apiBase}/sdk/oauth/authorize`);
      authUrl.searchParams.append('client_id', apiKey);
      authUrl.searchParams.append('redirect_uri', finalRedirectUri);
      authUrl.searchParams.append('response_type', 'code');
      authUrl.searchParams.append('scope', 'openid profile email');
      authUrl.searchParams.append('code_challenge', challenge);
      authUrl.searchParams.append('code_challenge_method', 'S256');

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
