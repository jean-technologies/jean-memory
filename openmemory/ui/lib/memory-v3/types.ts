/**
 * Jean Memory V3 STM (Short-Term Memory) Type Definitions
 * 
 * These types define the browser-based Short-Term Memory layer that provides:
 * - Instant memory access and creation
 * - Local semantic search
 * - Background sync to Jean Memory V2 (LTM)
 */

// STM Configuration
export interface STMConfig {
  /** Maximum number of memories to store locally */
  maxMemories: number;
  
  /** Enable local embedding generation using Transformers.js */
  localEmbedding: boolean;
  
  /** Enable automatic background sync to Jean Memory V2 */
  autoSync: boolean;
  
  /** Sync interval in milliseconds */
  syncInterval: number;
  
  /** Conflict resolution strategy */
  conflictResolution: 'manual' | 'latest_wins' | 'merge';
  
  /** Memory expiration time in milliseconds */
  memoryTTL: number;
  
  /** Enable offline mode */
  offlineMode: boolean;
}

// Default STM Configuration
export const DEFAULT_STM_CONFIG: STMConfig = {
  maxMemories: 10000,
  localEmbedding: true,
  autoSync: true,
  syncInterval: 5 * 60 * 1000, // 5 minutes
  conflictResolution: 'manual',
  memoryTTL: 7 * 24 * 60 * 60 * 1000, // 7 days
  offlineMode: false,
};

// STM Memory Item (extends existing Memory with STM-specific fields)
export interface STMMemory {
  id: string;
  content: string;
  embedding?: number[];
  created_at: number;
  updated_at: number;
  user_id: string;
  app_name: string;
  
  // STM-specific fields
  memory_type: 'stm' | 'ltm';
  session_id?: string;
  expires_at?: number;
  priority_score: number;
  access_count: number;
  last_accessed: number;
  sync_status: 'pending' | 'syncing' | 'synced' | 'conflict' | 'failed';
  local_only: boolean;
  
  // Optional metadata
  metadata?: {
    categories?: string[];
    tags?: string[];
    source?: string;
    [key: string]: any;
  };
}

// STM Search Query
export interface STMSearchQuery {
  query: string;
  limit?: number;
  includeExpired?: boolean;
  sessionOnly?: boolean;
  similarityThreshold?: number;
  sortBy?: 'relevance' | 'created_at' | 'accessed_at' | 'priority';
}

// STM Search Result
export interface STMSearchResult {
  memory: STMMemory;
  score: number;
  source: 'local' | 'remote';
}

// STM Sync Status
export interface STMSyncStatus {
  isOnline: boolean;
  lastSync: number;
  pendingSync: number;
  conflicts: number;
  syncInProgress: boolean;
  totalMemories: number;
  localMemories: number;
  storageUsed: number; // bytes
  storageQuota: number; // bytes
}

// STM Conflict
export interface STMConflict {
  memory_id: string;
  local_version: STMMemory;
  remote_version: STMMemory;
  conflict_type: 'content' | 'metadata' | 'state';
  created_at: number;
}

// STM Events
export type STMEvent = 
  | { type: 'memory_added'; memory: STMMemory }
  | { type: 'memory_updated'; memory: STMMemory }
  | { type: 'memory_deleted'; memory_id: string }
  | { type: 'sync_started' }
  | { type: 'sync_completed'; stats: { uploaded: number; downloaded: number; conflicts: number } }
  | { type: 'sync_failed'; error: string }
  | { type: 'conflict_detected'; conflict: STMConflict }
  | { type: 'storage_warning'; usage: number; quota: number };

// STM Event Listener
export type STMEventListener = (event: STMEvent) => void;

// STM Statistics
export interface STMStats {
  totalMemories: number;
  localMemories: number;
  syncedMemories: number;
  pendingSync: number;
  conflicts: number;
  storageUsed: number;
  storageQuota: number;
  averageMemorySize: number;
  oldestMemory?: number;
  newestMemory?: number;
  mostAccessedMemory?: STMMemory;
  lastSyncTime?: number;
}

// Browser Storage Interface
export interface BrowserStorage {
  get(key: string): Promise<any>;
  set(key: string, value: any): Promise<void>;
  delete(key: string): Promise<void>;
  clear(): Promise<void>;
  keys(): Promise<string[]>;
  size(): Promise<number>;
}

// Embedding Service Interface
export interface EmbeddingService {
  embed(text: string): Promise<number[]>;
  similarity(embedding1: number[], embedding2: number[]): number;
  isReady(): boolean;
  getDimensions(): number;
}

// STM Service Interface
export interface STMService {
  // Configuration
  configure(config: Partial<STMConfig>): Promise<void>;
  getConfig(): STMConfig;
  
  // Memory Operations
  addMemory(content: string, metadata?: any): Promise<STMMemory>;
  getMemory(id: string): Promise<STMMemory | null>;
  updateMemory(id: string, content: string, metadata?: any): Promise<STMMemory>;
  deleteMemory(id: string): Promise<void>;
  
  // Search Operations
  search(query: STMSearchQuery): Promise<STMSearchResult[]>;
  
  // Sync Operations
  sync(): Promise<void>;
  getSyncStatus(): STMSyncStatus;
  
  // Conflict Resolution
  resolveConflict(conflict: STMConflict, resolution: 'local' | 'remote' | 'merge'): Promise<void>;
  getConflicts(): STMConflict[];
  
  // Event Management
  addEventListener(listener: STMEventListener): void;
  removeEventListener(listener: STMEventListener): void;
  
  // Statistics
  getStats(): Promise<STMStats>;
  
  // Lifecycle
  initialize(): Promise<void>;
  cleanup(): Promise<void>;
}