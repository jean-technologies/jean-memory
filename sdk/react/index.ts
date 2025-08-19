/**
 * Jean Memory React SDK
 * The fastest way to add a context-aware AI to your React application
 * @version 1.0.0
 */

// Core Provider and Hook
export { JeanProvider, useJean } from './provider';

// Components
export { JeanChat } from './JeanChat';
export { SignInWithJean, signOutFromJean } from './SignInWithJean';

// New simplified components
export { JeanAuthGuard } from './JeanAuthGuard';
export { JeanChatComplete } from './JeanChatComplete';

// OAuth Utilities
export { 
  initiateOAuth, 
  handleOAuthCallback, 
  getUserSession, 
  clearUserSession, 
  isAuthenticated, 
  getUserToken,
  storeUserSession 
} from './oauth';

// Advanced MCP Hook (for direct tool access)
export { useJeanMCP } from './useJeanMCP';

// Types
export type { JeanUser, JeanMessage, MessageOptions } from './provider';
