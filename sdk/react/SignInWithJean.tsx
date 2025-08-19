/**
 * Jean Memory React SDK - Sign In With Jean Component
 * OAuth 2.1 PKCE authentication flow - Backend-driven Universal OAuth
 */
import React, { useEffect, useState, useRef } from 'react';
import { 
  initiateOAuth, 
  getUserSession, 
  clearUserSession, 
  isAuthenticated,
  JeanUser
} from './oauth';
import { useJean } from './provider';

interface SignInWithJeanProps {
  onSuccess: (user: any) => void;
  onError?: (error: Error) => void;
  apiKey?: string;
  className?: string;
  children?: React.ReactNode;
  redirectUri?: string;
  asChild?: boolean;
}

// Utility function to sign out and clear session
export const signOutFromJean = () => {
  clearUserSession();
  console.log('✅ Jean OAuth: Signed out successfully');
};


export function SignInWithJean({ 
  onSuccess, 
  onError, 
  apiKey: propApiKey,
  className = '', 
  children,
  redirectUri,
  asChild = false
}: SignInWithJeanProps) {
  const [isLoading, setIsLoading] = useState(false);
  const hasHandledCallback = useRef(false);
  
  // Get context safely
  let context: any = null;
  let isInProvider = false;
  try {
    context = useJean();
    isInProvider = true;
  } catch {
    // Not inside a JeanProvider
    isInProvider = false;
  }

  const contextApiKey = context?.apiKey;

  // Handle API key resolution with warnings
  if (propApiKey && contextApiKey && propApiKey !== contextApiKey) {
    console.warn('Jean SDK Warning: The `apiKey` provided to SignInWithJean conflicts with the one from JeanProvider. The prop value will be used.');
  }

  const apiKey = propApiKey || contextApiKey;

  if (!apiKey) {
    throw new Error('Jean SDK Error: API key is missing. Please pass it as a prop to SignInWithJean or wrap your component in a JeanProvider with an apiKey.');
  }

  useEffect(() => {
    // If we're inside a JeanProvider, subscribe to its auth state
    if (isInProvider && context?.isAuthenticated && context?.user && !hasHandledCallback.current) {
      console.log('✅ Jean OAuth: User authenticated via Provider');
      onSuccess(context.user);
      hasHandledCallback.current = true;
    } else if (!isInProvider) {
      // Standalone usage - check for existing session
      const existingUser = getUserSession();
      if (existingUser && !hasHandledCallback.current) {
        console.log('✅ Jean OAuth: Recovered existing session for user:', existingUser.email);
        onSuccess(existingUser);
        hasHandledCallback.current = true;
      }
    }
  }, [onSuccess, isInProvider, context?.isAuthenticated, context?.user]);


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
      
      // If we're in a Provider context, use its signIn method for better state coordination
      if (isInProvider && context?.signIn) {
        await context.signIn();
      } else {
        // Standalone usage
        await initiateOAuth({
          apiKey,
          redirectUri
        });
      }
      
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

  // If asChild is true, clone the child element and add onClick handler
  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children, {
      onClick: handleSignIn,
      disabled: isLoading,
      ...children.props
    });
  }

  // Default button implementation
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