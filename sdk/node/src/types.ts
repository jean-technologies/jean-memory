/**
 * Jean Memory Node.js SDK Type Definitions
 * TypeScript interfaces and types for the Jean Memory API
 */

/**
 * Configuration for the Jean Memory client
 */
export interface ClientConfig {
  /** Your Jean Memory API key (starts with 'jean_sk_') */
  apiKey: string;
  /** Base URL for the Jean Memory API (optional) */
  apiBase?: string;
  /** Custom User-Agent string (optional) */
  userAgent?: string;
}

/**
 * Individual memory object
 */
export interface Memory {
  /** Unique memory identifier */
  id: string;
  /** Memory content */
  content: string;
  /** Additional context metadata */
  context: Record<string, any>;
  /** Creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at?: string;
  /** Memory processing status */
  status: MemoryStatus;
  /** Vector embedding (if available) */
  embedding_vector?: number[];
  /** Relevance score for search results */
  relevance_score?: number;
}

/**
 * Memory processing status
 */
export enum MemoryStatus {
  PENDING = 'pending',
  PROCESSED = 'processed',
  FAILED = 'failed'
}

/**
 * Request payload for creating a new memory
 */
export interface MemoryCreateRequest {
  /** Memory content */
  content: string;
  /** Additional context metadata */
  context?: Record<string, any>;
}

/**
 * Response from memory creation
 */
export interface MemoryCreateResponse {
  /** Created memory ID */
  id: string;
  /** Creation status */
  status: string;
  /** Status message */
  message: string;
}

/**
 * Options for memory search
 */
export interface MemorySearchOptions {
  /** Maximum number of memories to return (1-100, default: 10) */
  limit?: number;
  /** Number of memories to skip (default: 0) */
  offset?: number;
  /** Include memory embeddings in response */
  include_embeddings?: boolean;
  /** Minimum relevance score threshold */
  min_score?: number;
}

/**
 * Options for listing memories
 */
export interface MemoryListOptions {
  /** Maximum number of memories to return (1-100, default: 20) */
  limit?: number;
  /** Number of memories to skip (default: 0) */
  offset?: number;
  /** Sort order ('created_at', 'updated_at', 'relevance') */
  sort_by?: 'created_at' | 'updated_at' | 'relevance';
  /** Sort direction ('asc' or 'desc') */
  sort_order?: 'asc' | 'desc';
}

/**
 * Search result containing memories and metadata
 */
export interface MemorySearchResult {
  /** List of matching memories */
  memories: Memory[];
  /** Total number of matching memories */
  total: number;
  /** Original search query */
  query: string;
  /** Maximum results requested */
  limit: number;
  /** Results offset */
  offset: number;
  /** Search execution time in milliseconds */
  search_time_ms?: number;
}

/**
 * User information
 */
export interface UserInfo {
  /** Unique user identifier */
  user_id: string;
  /** User email address */
  email: string;
  /** User display name */
  name?: string;
  /** Account creation date */
  created_at: string;
  /** Subscription tier */
  subscription_tier?: string;
  /** Total memories stored */
  memory_count?: number;
}

/**
 * Generic API response wrapper
 */
export interface APIResponse<T = any> {
  /** Request success status */
  success: boolean;
  /** Response data */
  data?: T;
  /** Error message if any */
  error?: string;
  /** Response timestamp */
  timestamp: string;
}

/**
 * API health check response
 */
export interface HealthStatus {
  /** Service status */
  status: string;
  /** API version */
  version: string;
  /** Service uptime in seconds */
  uptime_seconds?: number;
  /** Memory usage in MB */
  memory_usage_mb?: number;
  /** Authentication status */
  authenticated: boolean;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  /** Total number of items */
  total: number;
  /** Items per page */
  limit: number;
  /** Current offset */
  offset: number;
  /** Whether more items exist */
  has_next: boolean;
  /** Whether previous items exist */
  has_prev: boolean;
}

/**
 * Response for paginated memory lists
 */
export interface MemoryListResponse {
  /** List of memories */
  memories: Memory[];
  /** Pagination information */
  pagination: PaginationMeta;
}

/**
 * OAuth authentication configuration
 */
export interface OAuthConfig {
  /** OAuth server base URL */
  oauth_base?: string;
  /** Local redirect port for OAuth callback */
  redirect_port?: number;
  /** OAuth scopes to request */
  scopes?: string[];
}

/**
 * OAuth authentication result
 */
export interface AuthResult {
  /** User ID */
  user_id: string;
  /** User email */
  email: string;
  /** User display name */
  name?: string;
  /** Access token */
  access_token: string;
  /** Account creation date */
  created_at: string;
  /** Token expiration (if provided) */
  expires_at?: string;
  /** Refresh token (if provided) */
  refresh_token?: string;
}

/**
 * Error response from the API
 */
export interface APIError {
  /** Error code */
  code?: string;
  /** Human-readable error message */
  message: string;
  /** Additional error details */
  details?: Record<string, any>;
  /** Request ID for debugging */
  request_id?: string;
}

/**
 * Streaming options
 */
export interface StreamOptions {
  /** Batch size for streaming */
  batch_size?: number;
  /** Include memory metadata in stream */
  include_metadata?: boolean;
}

/**
 * Context retrieval options
 */
export interface ContextOptions {
  /** Maximum number of memories to use for context */
  max_memories?: number;
  /** Context formatting style */
  format?: 'simple' | 'detailed' | 'json';
  /** Include timestamps in context */
  include_timestamps?: boolean;
}

/**
 * Enhanced context response with metadata
 */
export interface ContextResponse {
  /** Generated context text */
  text: string;
  /** Response metadata */
  metadata?: Record<string, any>;
}

/**
 * OAuth context parameters
 */
export interface OAuthContextParams {
  /** User token for OAuth flow */
  user_token: string;
  /** User message/query */
  message: string;
  /** Processing speed mode */
  speed?: 'fast' | 'balanced' | 'comprehensive';
  /** Tool to use for processing */
  tool?: 'jean_memory' | 'search_memory';
  /** Response format */
  format?: 'simple' | 'enhanced';
}

/**
 * Memory update request
 */
export interface MemoryUpdateRequest {
  /** Updated content */
  content?: string;
  /** Updated context metadata */
  context?: Record<string, any>;
}

/**
 * Bulk operation request
 */
export interface BulkOperationRequest {
  /** Memory IDs to operate on */
  memory_ids: string[];
  /** Operation type */
  operation: 'delete' | 'update' | 'export';
  /** Operation-specific parameters */
  params?: Record<string, any>;
}

/**
 * Bulk operation response
 */
export interface BulkOperationResponse {
  /** Number of successfully processed items */
  success_count: number;
  /** Number of failed items */
  error_count: number;
  /** Detailed results for each item */
  results: Array<{
    memory_id: string;
    success: boolean;
    error?: string;
  }>;
}

// Type aliases for convenience
export type MemoryId = string;
export type ContextDict = Record<string, any>;
export type Timestamp = string;