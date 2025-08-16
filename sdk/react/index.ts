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

// Advanced MCP Hook (for direct tool access)
export { useJeanMCP } from './useJeanMCP';

// Types
export type { JeanUser as JeanProviderUser, JeanMessage, MessageOptions } from './provider';
export type { JeanUser } from './SignInWithJean';
