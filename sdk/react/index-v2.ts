/**
 * Jean Memory React SDK v2.0
 * Secure OAuth 2.1 PKCE with JWT-in-header authentication
 * @version 2.0.0
 */

// Core Provider and Hook (v2.0 Secure)
export { JeanProvider, useJean } from './provider-v2';

// Components (v2.0 Secure)
export { SignInWithJean, signOutFromJean } from './SignInWithJean-v2';

// OAuth Utilities (v2.0)
export { 
  initiateOAuth, 
  handleOAuthCallback, 
  getUserSession, 
  clearUserSession, 
  isAuthenticated, 
  getUserToken,
  storeUserSession 
} from './oauth';

// Legacy Components (v1.x compatibility)
export { JeanChat } from './JeanChat';
export { useJeanMCP } from './useJeanMCP';

// Types
export type { JeanUser, JeanMessage, MessageOptions } from './provider-v2';