/**
 * Jean Memory React SDK
 * 5-line integration for personalized AI chatbots
 * Using MCP (Model Context Protocol) for direct jean_memory tool access
 */

export { 
  useJeanAgent,
  SignInWithJean, 
  JeanChat,
  JeanAgent
} from './useJeanAgent';

export type { 
  JeanUser, 
  JeanAgentConfig, 
  Message 
} from './useJeanAgent';

// Default export for business case integration
export { default } from './useJeanAgent';
