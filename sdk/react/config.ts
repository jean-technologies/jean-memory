/**
 * Jean Memory React SDK - Configuration
 * Centralized API endpoints
 */
export const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';
export const JEAN_OAUTH_BASE = 'https://jeanmemory.com';

// Supabase configuration - should be provided via environment variables
export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://masapxpxcwvsjpuymbmd.supabase.co';
export const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder_key_set_in_env';
