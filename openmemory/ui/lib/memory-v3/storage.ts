/**
 * Jean Memory V3 Browser Storage Layer
 * 
 * Provides IndexedDB-based storage for STM memories with:
 * - High-performance indexed access
 * - Automatic cleanup and expiration
 * - Efficient memory management
 */

import { STMMemory, BrowserStorage } from './types';

// IndexedDB Database Schema
const DB_NAME = 'JeanMemoryV3_STM';
const DB_VERSION = 1;
const MEMORIES_STORE = 'memories';
const METADATA_STORE = 'metadata';

// Database Schema
interface DBSchema {
  memories: {
    key: string; // memory_id
    value: STMMemory;
    indexes: {
      'by-user-id': string;
      'by-created-at': number;
      'by-last-accessed': number;
      'by-expires-at': number;
      'by-sync-status': string;
      'by-session-id': string;
    };
  };
  metadata: {
    key: string;
    value: any;
  };
}

export class STMBrowserStorage implements BrowserStorage {
  private db: IDBDatabase | null = null;
  private userId: string;

  constructor(userId: string) {
    this.userId = userId;
  }

  async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        reject(new Error(`STM Storage: Failed to open database: ${request.error}`));
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        this.setupDatabase(db);
      };
    });
  }

  private setupDatabase(db: IDBDatabase): void {
    // Create memories object store
    if (!db.objectStoreNames.contains(MEMORIES_STORE)) {
      const memoriesStore = db.createObjectStore(MEMORIES_STORE, { keyPath: 'id' });
      
      // Create indexes for efficient querying
      memoriesStore.createIndex('by-user-id', 'user_id', { unique: false });
      memoriesStore.createIndex('by-created-at', 'created_at', { unique: false });
      memoriesStore.createIndex('by-last-accessed', 'last_accessed', { unique: false });
      memoriesStore.createIndex('by-expires-at', 'expires_at', { unique: false });
      memoriesStore.createIndex('by-sync-status', 'sync_status', { unique: false });
      memoriesStore.createIndex('by-session-id', 'session_id', { unique: false });
    }

    // Create metadata object store
    if (!db.objectStoreNames.contains(METADATA_STORE)) {
      db.createObjectStore(METADATA_STORE);
    }
  }

  // Memory Operations
  async addMemory(memory: STMMemory): Promise<void> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readwrite');
      const store = transaction.objectStore(MEMORIES_STORE);
      
      const request = store.put(memory);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error(`STM Storage: Failed to add memory: ${request.error}`));
    });
  }

  async getMemory(id: string): Promise<STMMemory | null> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readonly');
      const store = transaction.objectStore(MEMORIES_STORE);
      
      const request = store.get(id);
      
      request.onsuccess = () => {
        const memory = request.result as STMMemory | undefined;
        if (memory && memory.user_id === this.userId) {
          resolve(memory);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => reject(new Error(`STM Storage: Failed to get memory: ${request.error}`));
    });
  }

  async updateMemory(memory: STMMemory): Promise<void> {
    return this.addMemory(memory); // IndexedDB put() works for both add and update
  }

  async deleteMemory(id: string): Promise<void> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readwrite');
      const store = transaction.objectStore(MEMORIES_STORE);
      
      const request = store.delete(id);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error(`STM Storage: Failed to delete memory: ${request.error}`));
    });
  }

  // Query Operations
  async getMemoriesByUser(userId: string, limit?: number): Promise<STMMemory[]> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readonly');
      const store = transaction.objectStore(MEMORIES_STORE);
      const index = store.index('by-user-id');
      
      const request = index.getAll(userId, limit);
      
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(new Error(`STM Storage: Failed to query memories: ${request.error}`));
    });
  }

  async getMemoriesBySession(sessionId: string): Promise<STMMemory[]> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readonly');
      const store = transaction.objectStore(MEMORIES_STORE);
      const index = store.index('by-session-id');
      
      const request = index.getAll(sessionId);
      
      request.onsuccess = () => {
        const memories = (request.result || []).filter(m => m.user_id === this.userId);
        resolve(memories);
      };
      request.onerror = () => reject(new Error(`STM Storage: Failed to query session memories: ${request.error}`));
    });
  }

  async getMemoriesBySyncStatus(status: STMMemory['sync_status']): Promise<STMMemory[]> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readonly');
      const store = transaction.objectStore(MEMORIES_STORE);
      const index = store.index('by-sync-status');
      
      const request = index.getAll(status);
      
      request.onsuccess = () => {
        const memories = (request.result || []).filter(m => m.user_id === this.userId);
        resolve(memories);
      };
      request.onerror = () => reject(new Error(`STM Storage: Failed to query sync status: ${request.error}`));
    });
  }

  async getExpiredMemories(): Promise<STMMemory[]> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    const now = Date.now();
    
    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readonly');
      const store = transaction.objectStore(MEMORIES_STORE);
      const index = store.index('by-expires-at');
      
      const range = IDBKeyRange.upperBound(now);
      const request = index.getAll(range);
      
      request.onsuccess = () => {
        const memories = (request.result || []).filter(m => 
          m.user_id === this.userId && m.expires_at && m.expires_at <= now
        );
        resolve(memories);
      };
      request.onerror = () => reject(new Error(`STM Storage: Failed to query expired memories: ${request.error}`));
    });
  }

  // Cleanup Operations
  async cleanup(): Promise<{ deleted: number; errors: number }> {
    let deleted = 0;
    let errors = 0;

    try {
      // Get expired memories
      const expiredMemories = await this.getExpiredMemories();
      
      // Delete expired memories
      for (const memory of expiredMemories) {
        try {
          await this.deleteMemory(memory.id);
          deleted++;
        } catch (error) {
          console.error('STM Storage: Failed to delete expired memory:', memory.id, error);
          errors++;
        }
      }

      // Also clean up memories that haven't been accessed in a while
      await this.cleanupOldMemories();

    } catch (error) {
      console.error('STM Storage: Cleanup failed:', error);
      errors++;
    }

    return { deleted, errors };
  }

  private async cleanupOldMemories(): Promise<void> {
    // Get all memories, sorted by last accessed
    const allMemories = await this.getMemoriesByUser(this.userId);
    
    // Sort by last accessed (oldest first)
    allMemories.sort((a, b) => a.last_accessed - b.last_accessed);
    
    // If we have too many memories, delete the oldest ones
    const maxMemories = 10000; // This should come from config
    if (allMemories.length > maxMemories) {
      const toDelete = allMemories.slice(0, allMemories.length - maxMemories);
      
      for (const memory of toDelete) {
        try {
          await this.deleteMemory(memory.id);
        } catch (error) {
          console.error('STM Storage: Failed to delete old memory:', memory.id, error);
        }
      }
    }
  }

  // Statistics
  async getStorageStats(): Promise<{
    totalMemories: number;
    totalSize: number;
    oldestMemory?: number;
    newestMemory?: number;
  }> {
    const memories = await this.getMemoriesByUser(this.userId);
    
    let totalSize = 0;
    let oldest: number | undefined;
    let newest: number | undefined;

    for (const memory of memories) {
      // Estimate memory size (rough calculation)
      totalSize += JSON.stringify(memory).length;
      
      if (!oldest || memory.created_at < oldest) {
        oldest = memory.created_at;
      }
      
      if (!newest || memory.created_at > newest) {
        newest = memory.created_at;
      }
    }

    return {
      totalMemories: memories.length,
      totalSize,
      oldestMemory: oldest,
      newestMemory: newest,
    };
  }

  // Generic storage interface implementation
  async get(key: string): Promise<any> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([METADATA_STORE], 'readonly');
      const store = transaction.objectStore(METADATA_STORE);
      
      const request = store.get(key);
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error(`STM Storage: Failed to get metadata: ${request.error}`));
    });
  }

  async set(key: string, value: any): Promise<void> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([METADATA_STORE], 'readwrite');
      const store = transaction.objectStore(METADATA_STORE);
      
      const request = store.put(value, key);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error(`STM Storage: Failed to set metadata: ${request.error}`));
    });
  }

  async delete(key: string): Promise<void> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([METADATA_STORE], 'readwrite');
      const store = transaction.objectStore(METADATA_STORE);
      
      const request = store.delete(key);
      
      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error(`STM Storage: Failed to delete metadata: ${request.error}`));
    });
  }

  async clear(): Promise<void> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE, METADATA_STORE], 'readwrite');
      
      const memoriesStore = transaction.objectStore(MEMORIES_STORE);
      const metadataStore = transaction.objectStore(METADATA_STORE);
      
      const memoriesRequest = memoriesStore.clear();
      const metadataRequest = metadataStore.clear();
      
      let completed = 0;
      const checkComplete = () => {
        completed++;
        if (completed === 2) resolve();
      };

      memoriesRequest.onsuccess = checkComplete;
      metadataRequest.onsuccess = checkComplete;
      
      memoriesRequest.onerror = () => reject(new Error(`STM Storage: Failed to clear memories: ${memoriesRequest.error}`));
      metadataRequest.onerror = () => reject(new Error(`STM Storage: Failed to clear metadata: ${metadataRequest.error}`));
    });
  }

  async keys(): Promise<string[]> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([METADATA_STORE], 'readonly');
      const store = transaction.objectStore(METADATA_STORE);
      
      const request = store.getAllKeys();
      
      request.onsuccess = () => resolve(request.result.map(k => String(k)));
      request.onerror = () => reject(new Error(`STM Storage: Failed to get keys: ${request.error}`));
    });
  }

  async size(): Promise<number> {
    if (!this.db) throw new Error('STM Storage: Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([MEMORIES_STORE], 'readonly');
      const store = transaction.objectStore(MEMORIES_STORE);
      
      const request = store.count();
      
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(new Error(`STM Storage: Failed to count memories: ${request.error}`));
    });
  }

  async close(): Promise<void> {
    if (this.db) {
      this.db.close();
      this.db = null;
    }
  }
}