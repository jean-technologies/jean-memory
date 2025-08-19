/**
 * Jean Memory React SDK - OAuth 2.1 PKCE Utilities
 * Robust authentication flow with session persistence
 */

import { JEAN_API_BASE } from './config';

export interface OAuthConfig {
  apiKey: string;
  redirectUri?: string;
  scopes?: string[];
}

export interface JeanUser {
  email: string;
  name?: string;
  access_token: string;
}

export interface OAuthSession {
  codeVerifier: string;
  state: string;
  clientId: string;
  redirectUri: string;
  apiKey: string;
  timestamp: number;
}

// Session storage keys
const SESSION_KEYS = {
  OAUTH_SESSION: 'jean_oauth_session_v2',
  USER_TOKEN: 'jean_user_token_v2',
  USER_INFO: 'jean_user_info_v2',
  AUTH_STATE: 'jean_auth_state_v2'
} as const;

/**
 * Generate cryptographically secure random string
 */
function generateSecureRandom(length: number = 32): string {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  return Array.from(array, byte => charset[byte % charset.length]).join('');
}

/**
 * Generate PKCE code verifier and challenge
 */
async function generatePKCE(): Promise<{ verifier: string; challenge: string }> {
  const verifier = generateSecureRandom(128);
  
  // Generate code challenge
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest('SHA-256', data);
  const challenge = btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
    
  return { verifier, challenge };
}

/**
 * Store OAuth session securely with expiration
 */
function storeOAuthSession(session: OAuthSession): void {
  try {
    // Add 1 hour expiration
    const sessionWithExpiry = {
      ...session,
      expiresAt: Date.now() + (60 * 60 * 1000)
    };
    
    sessionStorage.setItem(SESSION_KEYS.OAUTH_SESSION, JSON.stringify(sessionWithExpiry));
  } catch (error) {
    console.error('Failed to store OAuth session:', error);
    throw new Error('Session storage failed');
  }
}

/**
 * Retrieve OAuth session with expiration check
 */
function getOAuthSession(): OAuthSession | null {
  try {
    const stored = sessionStorage.getItem(SESSION_KEYS.OAUTH_SESSION);
    if (!stored) return null;
    
    const session = JSON.parse(stored);
    
    // Check expiration
    if (session.expiresAt && Date.now() > session.expiresAt) {
      sessionStorage.removeItem(SESSION_KEYS.OAUTH_SESSION);
      return null;
    }
    
    return session;
  } catch (error) {
    console.error('Failed to retrieve OAuth session:', error);
    sessionStorage.removeItem(SESSION_KEYS.OAUTH_SESSION);
    return null;
  }
}

/**
 * Clear OAuth session
 */
function clearOAuthSession(): void {
  sessionStorage.removeItem(SESSION_KEYS.OAUTH_SESSION);
}

/**
 * Store user session with persistence options
 */
export function storeUserSession(user: JeanUser): void {
  try {
    // Store in both localStorage (persistent) and sessionStorage (current session)
    const userInfo = {
      email: user.email,
      name: user.name,
      timestamp: Date.now()
    };
    
    localStorage.setItem(SESSION_KEYS.USER_INFO, JSON.stringify(userInfo));
    localStorage.setItem(SESSION_KEYS.USER_TOKEN, user.access_token);
    localStorage.setItem(SESSION_KEYS.AUTH_STATE, 'authenticated');
    
    // Also store in sessionStorage for faster access
    sessionStorage.setItem(SESSION_KEYS.USER_INFO, JSON.stringify(userInfo));
    sessionStorage.setItem(SESSION_KEYS.USER_TOKEN, user.access_token);
    
    console.log('✅ Jean OAuth: User session stored successfully');
  } catch (error) {
    console.error('Failed to store user session:', error);
  }
}

/**
 * Retrieve stored user session
 */
export function getUserSession(): JeanUser | null {
  try {
    // Try sessionStorage first (faster), then localStorage
    let userInfo = sessionStorage.getItem(SESSION_KEYS.USER_INFO);
    let token = sessionStorage.getItem(SESSION_KEYS.USER_TOKEN);
    
    if (!userInfo || !token) {
      userInfo = localStorage.getItem(SESSION_KEYS.USER_INFO);
      token = localStorage.getItem(SESSION_KEYS.USER_TOKEN);
    }
    
    if (!userInfo || !token) return null;
    
    const user = JSON.parse(userInfo);
    return {
      ...user,
      access_token: token
    };
  } catch (error) {
    console.error('Failed to retrieve user session:', error);
    clearUserSession();
    return null;
  }
}

/**
 * Clear all user session data
 */
export function clearUserSession(): void {
  // Clear all session keys from both storages
  Object.values(SESSION_KEYS).forEach((key: string) => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
  
  // Clear legacy keys for backward compatibility
  const legacyKeys = [
    'auth_completed', 'userInfo', 'isLoggedIn', 'userEmail', 
    'userName', 'userId', 'userAvatar', 'authProvider', 'tempUserInfo'
  ];
  
  legacyKeys.forEach(key => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
  
  console.log('✅ Jean OAuth: All session data cleared');
}

/**
 * Initiate OAuth 2.1 PKCE flow
 */
export async function initiateOAuth(config: OAuthConfig): Promise<void> {
  try {
    const { apiKey, redirectUri = window.location.origin + window.location.pathname } = config;
    
    // Generate PKCE parameters
    const { verifier, challenge } = await generatePKCE();
    const state = generateSecureRandom(32);
    const clientId = `jean-sdk-${Date.now()}`;
    
    // Store OAuth session
    storeOAuthSession({
      codeVerifier: verifier,
      state,
      clientId,
      redirectUri,
      apiKey,
      timestamp: Date.now()
    });
    
    // Build authorization URL
    const authUrl = new URL(`${JEAN_API_BASE}/v1/sdk/oauth/authorize`);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', redirectUri);
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', challenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    
    console.log('🔄 Jean OAuth: Initiating OAuth flow...');
    
    // Redirect to OAuth provider
    window.location.href = authUrl.toString();
  } catch (error) {
    console.error('Failed to initiate OAuth:', error);
    throw new Error('OAuth initiation failed');
  }
}

// Global flag to prevent duplicate token exchanges in React StrictMode
let isExchangingToken = false;
let tokenExchangePromise: Promise<JeanUser | null> | null = null;

/**
 * Handle OAuth callback and exchange authorization code for token
 */
export async function handleOAuthCallback(): Promise<JeanUser | null> {
  try {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');
    const error = params.get('error');
    
    if (error) {
      const errorDescription = params.get('error_description') || 'OAuth authorization failed';
      throw new Error(`OAuth Error: ${error} - ${errorDescription}`);
    }
    
    if (!code || !state) {
      return null; // No OAuth callback parameters
    }

    // React StrictMode protection - prevent duplicate token exchanges
    if (isExchangingToken && tokenExchangePromise) {
      console.log('🔄 Jean OAuth: Token exchange already in progress, returning existing promise');
      return tokenExchangePromise;
    }
    
    if (isExchangingToken) {
      console.log('⚠️ Jean OAuth: Token exchange already in progress, skipping duplicate request');
      return null;
    }
    
    // Retrieve stored OAuth session
    const session = getOAuthSession();
    if (!session) {
      throw new Error('OAuth session not found or expired');
    }
    
    // Verify state parameter
    if (state !== session.state) {
      throw new Error('OAuth state mismatch - possible CSRF attack');
    }
    
    // Set flag and create promise to prevent duplicate exchanges
    isExchangingToken = true;
    console.log('🔄 Jean OAuth: Exchanging authorization code for token...');
    
    // Create the token exchange promise
    tokenExchangePromise = (async () => {
      try {
        // Exchange authorization code for access token
        const tokenResponse = await fetch(`${JEAN_API_BASE}/v1/sdk/oauth/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            grant_type: 'authorization_code',
            code,
            redirect_uri: session.redirectUri,
            client_id: session.clientId,
            code_verifier: session.codeVerifier
          })
        });
        
        if (!tokenResponse.ok) {
          const errorData = await tokenResponse.text();
          throw new Error(`Token exchange failed: ${errorData}`);
        }
        
        const tokenData = await tokenResponse.json();
        const { access_token } = tokenData;
        
        if (!access_token) {
          throw new Error('No access token received');
        }
        
        // Parse JWT token to extract user info (only client-safe fields)
        const payload = JSON.parse(atob(access_token.split('.')[1]));
        const user: JeanUser = {
          email: payload.email || '',
          name: payload.name || payload.email?.split('@')[0] || 'User',
          access_token
        };
        
        // Store user session
        storeUserSession(user);
        
        // Clean up OAuth session
        clearOAuthSession();
        
        // Clean up URL parameters
        const url = new URL(window.location.href);
        url.searchParams.delete('code');
        url.searchParams.delete('state');
        url.searchParams.delete('error');
        url.searchParams.delete('error_description');
        window.history.replaceState({}, '', url.toString());
        
        console.log('✅ Jean OAuth: Authentication successful for user:', user.email);
        
        return user;
      } finally {
        // Reset flags
        isExchangingToken = false;
        tokenExchangePromise = null;
      }
    })();
    
    return tokenExchangePromise;
  } catch (error) {
    console.error('OAuth callback handling failed:', error);
    clearOAuthSession();
    // Reset flags on error
    isExchangingToken = false;
    tokenExchangePromise = null;
    throw error;
  }
}

/**
 * Check if user is currently authenticated
 */
export function isAuthenticated(): boolean {
  const session = getUserSession();
  return session !== null && !!session.access_token;
}

/**
 * Get current user token for API requests
 */
export function getUserToken(): string | null {
  const session = getUserSession();
  return session?.access_token || null;
}