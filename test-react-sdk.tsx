/**
 * Test file to verify React SDK documentation accuracy
 * Testing against: https://docs.jeanmemory.com/sdk/react
 */

import React from 'react';

// Test 1: Import statements from documentation
// Documentation says: import { useJean, JeanChat } from 'jeanmemory-react';
// Actual exports based on code inspection:
// - useJean (from useJean.tsx)
// - useJeanAgent (from useJeanAgent.tsx) 
// - JeanChat (from both useJeanAgent and components/JeanChat)
// - SignInWithJean (from components/SignInWithJean and useJeanAgent)

// Test 2: useJean hook configuration
// Documentation shows:
const documentedConfig = {
  apiKey: "jean_sk_...",        // Required
  systemPrompt: "You are...",   // Optional
  baseUrl: "https://...",       // Optional
  debug: false                  // Optional
};

// Actual useJean hook signature from code:
// export const useJean = ({ user }: UseJeanProps)
// where UseJeanProps = { user: JeanUser | null }
// This is DIFFERENT - useJean expects a user object, not apiKey/systemPrompt

// Test 3: useJeanAgent hook (not documented but exists)
// Actual signature: useJeanAgent(config: JeanAgentConfig)
// where JeanAgentConfig = { apiKey?: string, systemPrompt?: string }
// This matches what documentation claims for useJean!

// Test 4: Return values
// Documentation says useJean returns:
// - agent, signIn, signOut, isAuthenticated, isLoading, error

// Actual useJean returns (from code):
// - agent, isLoading, error (NO signIn, signOut, isAuthenticated)

// Actual useJeanAgent returns:
// - agent, user, isLoading, error, signIn, signOut

// Test 5: JeanChat component props
// Documentation shows:
const documentedJeanChatProps = {
  agent: null, // agent from useJean
  theme: {
    primaryColor: '#9563FF',
    fontFamily: 'Inter'
  },
  height: "600px",
  placeholder: "Ask me anything..."
};

// Actual JeanChat props from components/JeanChat.tsx:
// interface JeanChatProps {
//   agent: JeanAgent;
//   className?: string;
//   style?: React.CSSProperties;
// }
// NO theme, height, or placeholder props!

// Test 6: Manual memory management
// Documentation shows:
// await agent.addMemory("User prefers...")
// await agent.searchMemories("user preferences")

// Actual agent object (from useJean):
// agent = { user: JeanUser, sendMessage: Function }
// NO addMemory or searchMemories methods!

// Test 7: Authentication flow
// Documentation mentions flexible authentication with customizable button
// Actual: SignInWithJean component uses prompt() for email/password
// Not OAuth-based as might be expected

// Test 8: Package name discrepancy
// Documentation: npm install jeanmemory-react
// package.json name: "jeanmemory-react" ✓ (matches)
// Demo app imports: @jeanmemory/react (different!)

export const DocumentationDiscrepancies = {
  critical: [
    "useJean hook has completely different signature - expects user, not apiKey",
    "useJean doesn't return signIn/signOut/isAuthenticated methods",
    "JeanChat doesn't support theme/height/placeholder props",
    "agent.addMemory() and agent.searchMemories() don't exist",
    "The correct hook to use appears to be useJeanAgent, not useJean"
  ],
  
  moderate: [
    "Demo app uses @jeanmemory/react but docs say jeanmemory-react",
    "Authentication uses browser prompt(), not a proper UI component",
    "No baseUrl or debug options actually implemented",
    "useMemory and useConversation hooks mentioned in docs don't exist"
  ],
  
  recommendations: [
    "Update docs to show useJeanAgent instead of useJean",
    "Remove non-existent props from JeanChat documentation",
    "Remove memory management methods that don't exist",
    "Clarify the actual authentication flow",
    "Fix package name consistency"
  ]
};