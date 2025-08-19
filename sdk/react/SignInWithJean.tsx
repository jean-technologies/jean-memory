/**
 * Jean Memory React SDK - Sign In With Jean Component
 * OAuth 2.1 PKCE authentication flow - Backend-driven Universal OAuth
 */
import React, { useEffect, useState } from 'react';
import { 
  initiateOAuth, 
  handleOAuthCallback, 
  getUserSession, 
  clearUserSession, 
  isAuthenticated,
  JeanUser
} from './oauth';

interface SignInWithJeanProps {
  onSuccess: (user: any) => void;
  onError?: (error: Error) => void;
  apiKey: string;
  className?: string;
  children?: React.ReactNode;
  redirectUri?: string;
}

// Utility function to sign out and clear session
export const signOutFromJean = () => {
  clearUserSession();
  console.log('✅ Jean OAuth: Signed out successfully');
};


export function SignInWithJean({ 
  onSuccess, 
  onError, 
  apiKey,
  className = '', 
  children,
  redirectUri
}: SignInWithJeanProps) {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check for existing session first
    const existingUser = getUserSession();
    if (existingUser) {
      console.log('✅ Jean OAuth: Recovered existing session for user:', existingUser.email);
      onSuccess(existingUser);
      return;
    }

    // Handle OAuth callback if present
    const handleCallback = async () => {
      try {
        const user = await handleOAuthCallback();
        if (user) {
          console.log('✅ Jean OAuth: Callback authentication successful');
          onSuccess(user);
        }
      } catch (error) {
        console.error('OAuth callback error:', error);
        if (onError) {
          onError(error instanceof Error ? error : new Error('OAuth callback failed'));
        }
      }
    };

    // Check for OAuth callback parameters
    const params = new URLSearchParams(window.location.search);
    if (params.get('code') && params.get('state')) {
      handleCallback();
    }
  }, [onSuccess, onError]);


  const handleSignIn = async () => {
    if (!apiKey) {
      const error = new Error('API key is required for authentication');
      console.error('Jean OAuth Error:', error.message);
      if (onError) {
        onError(error);
      }
      return;
    }

    setIsLoading(true);
    
    try {
      console.log('🔄 Jean OAuth: Initiating OAuth 2.1 PKCE flow...');
      
      await initiateOAuth({
        apiKey,
        redirectUri
      });
      
      // The OAuth flow will redirect to Google, so we won't reach this point
      // unless there's an error in the initiation
    } catch (error) {
      setIsLoading(false);
      console.error('Jean OAuth Error:', error);
      if (onError) {
        onError(error instanceof Error ? error : new Error('OAuth initiation failed'));
      }
    }
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