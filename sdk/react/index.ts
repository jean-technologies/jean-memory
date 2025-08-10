/**
 * Jean Memory React SDK
 * 5-line integration for personalized AI chatbots
 * Using MCP (Model Context Protocol) for direct jean_memory tool access
 */

// Original Components (Working, but basic UI)
export { 
  useJeanAgent,
  SignInWithJean, 
  JeanChat as JeanChatLegacy,
  JeanAgent
} from './useJeanAgent';

// New Professional UI Component (Pixel-Perfect Assistant-UI Design)
export { JeanChat } from './JeanChatProfessional';

export type { 
  JeanUser, 
  JeanAgentConfig, 
  Message 
} from './useJeanAgent';

// Default export - Original working JeanAgent (for backwards compatibility)
export { JeanAgent as default } from './useJeanAgent';
