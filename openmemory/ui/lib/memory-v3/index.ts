/**
 * Jean Memory V3 STM - Main Export
 * 
 * Browser-based Short-Term Memory layer for instant memory access
 * and local semantic search with background sync to Jean Memory V2.
 */

// Core types
export type {
  STMConfig,
  STMMemory,
  STMSearchQuery,
  STMSearchResult,
  STMSyncStatus,
  STMConflict,
  STMEvent,
  STMEventListener,
  STMStats,
  STMService,
  BrowserStorage,
  EmbeddingService,
} from './types';

export { DEFAULT_STM_CONFIG } from './types';

// Configuration
export { STMConfigManager, detectBrowserCapabilities } from './config';
export type { BrowserCapabilities } from './config';

// Storage
export { STMBrowserStorage } from './storage';

// Embedding
export { 
  STMEmbeddingService, 
  FallbackEmbeddingService,
  EmbeddingUtils,
  getEmbeddingService,
  createEmbeddingService,
} from './embedding';

// Core service
export { STMServiceImpl } from './service';

// Convenience factory function
import { STMServiceImpl } from './service';
import { STMConfig } from './types';

/**
 * Create and initialize a new STM service instance
 */
export async function createSTMService(
  userId: string, 
  config: Partial<STMConfig> = {}
): Promise<STMServiceImpl> {
  const service = new STMServiceImpl(userId, config);
  await service.initialize();
  return service;
}

/**
 * Check if STM is supported in the current browser
 */
export function isSTMSupported(): boolean {
  return (
    typeof indexedDB !== 'undefined' &&
    typeof Worker !== 'undefined' &&
    typeof WebAssembly !== 'undefined'
  );
}

/**
 * Get recommended STM configuration based on browser capabilities
 */
export async function getRecommendedSTMConfig(): Promise<Partial<STMConfig>> {
  const { STMConfigManager } = await import('./config');
  const manager = new STMConfigManager();
  await manager.initialize();
  return manager.getRecommendedConfig();
}