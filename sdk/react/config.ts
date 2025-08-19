/**
 * Jean Memory React SDK - Configuration
 * Centralized API endpoints for Universal OAuth 2.1
 */
export const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

// OAuth endpoints use the same API base
export const JEAN_OAUTH_AUTHORIZE = `${JEAN_API_BASE}/v1/sdk/oauth/authorize`;
export const JEAN_OAUTH_TOKEN = `${JEAN_API_BASE}/v1/sdk/oauth/token`;
