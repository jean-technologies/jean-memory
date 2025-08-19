/**
 * Jean Memory React SDK - Authentication Guard Component
 * Automatically handles authentication flow with customizable fallbacks
 */
import React from 'react';
import { useJean } from './provider';
import { SignInWithJean } from './SignInWithJean';

interface JeanAuthGuardProps {
  children: React.ReactNode;
  /** Custom loading component while checking authentication */
  loadingComponent?: React.ReactNode;
  /** Custom sign-in component when not authenticated */
  signInComponent?: React.ReactNode;
  /** Custom fallback when not authenticated (overrides signInComponent) */
  fallback?: React.ReactNode;
  /** Show default sign-in UI (default: true) */
  showDefaultSignIn?: boolean;
}

/**
 * AuthGuard component that automatically handles authentication state
 * 
 * @example
 * ```jsx
 * <JeanProvider apiKey="your-key">
 *   <JeanAuthGuard>
 *     <YourApp />
 *   </JeanAuthGuard>
 * </JeanProvider>
 * ```
 */
export function JeanAuthGuard({
  children,
  loadingComponent,
  signInComponent,
  fallback,
  showDefaultSignIn = true
}: JeanAuthGuardProps) {
  const { isAuthenticated, isLoading, user, apiKey } = useJean();

  // Show loading state
  if (isLoading) {
    return (
      loadingComponent || (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          flexDirection: 'column',
          gap: '16px'
        }}>
          <div style={{ fontSize: '24px' }}>🧠</div>
          <div>Connecting to Jean Memory...</div>
        </div>
      )
    );
  }

  // Show authenticated content
  if (isAuthenticated) {
    return <>{children}</>;
  }

  // Show custom fallback if provided
  if (fallback) {
    return <>{fallback}</>;
  }

  // Show custom sign-in component
  if (signInComponent) {
    return <>{signInComponent}</>;
  }

  // Show default sign-in UI
  if (showDefaultSignIn) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column',
        gap: '24px',
        padding: '40px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🧠</div>
        <h1 style={{ margin: 0, fontSize: '32px', fontWeight: 'bold' }}>Jean Memory</h1>
        <p style={{ margin: 0, fontSize: '18px', color: '#666', maxWidth: '400px' }}>
          Sign in to access your personalized AI that remembers everything
        </p>
        <div style={{
          padding: '12px 24px',
          fontSize: '16px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontWeight: 'bold',
          display: 'inline-block'
        }}>
          <SignInWithJean 
            apiKey={apiKey}
            onSuccess={(user) => console.log('✅ Authentication successful:', user.email)}
            onError={(error) => console.error('❌ Authentication failed:', error)}
          >
            Sign In with Jean
          </SignInWithJean>
        </div>
      </div>
    );
  }

  // Fallback: show nothing
  return null;
}