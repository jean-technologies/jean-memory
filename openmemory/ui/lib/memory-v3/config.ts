/**
 * Jean Memory V3 STM Configuration Manager
 * 
 * Handles configuration for the Short-Term Memory layer including
 * browser capabilities detection and adaptive settings.
 */

import { STMConfig, DEFAULT_STM_CONFIG } from './types';

// Browser Capabilities Detection
export interface BrowserCapabilities {
  indexedDB: boolean;
  webWorkers: boolean;
  webAssembly: boolean;
  storageQuota: number;
  isOnline: boolean;
  supportsEmbeddings: boolean;
}

// Detect browser capabilities
export async function detectBrowserCapabilities(): Promise<BrowserCapabilities> {
  const capabilities: BrowserCapabilities = {
    indexedDB: typeof indexedDB !== 'undefined',
    webWorkers: typeof Worker !== 'undefined',
    webAssembly: typeof WebAssembly !== 'undefined',
    storageQuota: 0,
    isOnline: navigator.onLine,
    supportsEmbeddings: false,
  };

  // Check storage quota
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    try {
      const estimate = await navigator.storage.estimate();
      capabilities.storageQuota = estimate.quota || 0;
    } catch (error) {
      console.warn('STM: Could not estimate storage quota:', error);
    }
  }

  // Check if we can load Transformers.js for embeddings
  capabilities.supportsEmbeddings = capabilities.webWorkers && capabilities.webAssembly;

  return capabilities;
}

// Configuration Manager
export class STMConfigManager {
  private config: STMConfig;
  private capabilities: BrowserCapabilities | null = null;

  constructor(userConfig: Partial<STMConfig> = {}) {
    this.config = { ...DEFAULT_STM_CONFIG, ...userConfig };
  }

  async initialize(): Promise<void> {
    this.capabilities = await detectBrowserCapabilities();
    await this.adaptConfigToCapabilities();
  }

  private async adaptConfigToCapabilities(): Promise<void> {
    if (!this.capabilities) return;

    // Adapt memory limit based on storage quota
    if (this.capabilities.storageQuota > 0) {
      // Use 20% of available storage for STM, assuming ~1KB per memory
      const estimatedMemoryCapacity = Math.floor(
        (this.capabilities.storageQuota * 0.2) / 1024
      );
      
      if (estimatedMemoryCapacity < this.config.maxMemories) {
        console.warn(`STM: Reducing memory limit from ${this.config.maxMemories} to ${estimatedMemoryCapacity} based on storage quota`);
        this.config.maxMemories = estimatedMemoryCapacity;
      }
    }

    // Disable local embeddings if not supported
    if (!this.capabilities.supportsEmbeddings) {
      console.warn('STM: Local embeddings not supported, falling back to server-side embeddings');
      this.config.localEmbedding = false;
    }

    // Adjust sync interval based on online status
    if (!this.capabilities.isOnline) {
      this.config.offlineMode = true;
      console.log('STM: Starting in offline mode');
    }

    // Check required capabilities
    if (!this.capabilities.indexedDB) {
      throw new Error('STM: IndexedDB is required but not supported in this browser');
    }
  }

  getConfig(): STMConfig {
    return { ...this.config };
  }

  updateConfig(updates: Partial<STMConfig>): void {
    this.config = { ...this.config, ...updates };
  }

  getBrowserCapabilities(): BrowserCapabilities | null {
    return this.capabilities;
  }

  // Validate configuration
  validateConfig(): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (this.config.maxMemories <= 0) {
      errors.push('maxMemories must be greater than 0');
    }

    if (this.config.syncInterval < 1000) {
      errors.push('syncInterval must be at least 1000ms');
    }

    if (this.config.memoryTTL < 0) {
      errors.push('memoryTTL must be non-negative');
    }

    if (!['manual', 'latest_wins', 'merge'].includes(this.config.conflictResolution)) {
      errors.push('conflictResolution must be one of: manual, latest_wins, merge');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  // Get recommended settings based on device capabilities
  getRecommendedConfig(): Partial<STMConfig> {
    if (!this.capabilities) {
      return {};
    }

    const recommended: Partial<STMConfig> = {};

    // Adjust memory limits based on available storage
    if (this.capabilities.storageQuota > 0) {
      const storageGB = this.capabilities.storageQuota / (1024 * 1024 * 1024);
      
      if (storageGB > 10) {
        recommended.maxMemories = 50000; // High-capacity device
      } else if (storageGB > 5) {
        recommended.maxMemories = 25000; // Medium-capacity device
      } else {
        recommended.maxMemories = 10000; // Low-capacity device
      }
    }

    // Adjust sync frequency based on connection
    if (!this.capabilities.isOnline) {
      recommended.autoSync = false;
      recommended.offlineMode = true;
    } else {
      // Adjust sync interval based on estimated connection quality
      recommended.syncInterval = 5 * 60 * 1000; // 5 minutes default
    }

    // Enable features based on browser support
    recommended.localEmbedding = this.capabilities.supportsEmbeddings;

    return recommended;
  }

  // Export configuration for persistence
  exportConfig(): string {
    return JSON.stringify({
      config: this.config,
      capabilities: this.capabilities,
      timestamp: Date.now()
    }, null, 2);
  }

  // Import configuration from persistence
  importConfig(jsonString: string): boolean {
    try {
      const data = JSON.parse(jsonString);
      if (data.config) {
        this.config = { ...DEFAULT_STM_CONFIG, ...data.config };
        return true;
      }
      return false;
    } catch (error) {
      console.error('STM: Failed to import configuration:', error);
      return false;
    }
  }
}