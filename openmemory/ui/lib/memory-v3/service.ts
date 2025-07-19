/**
 * Jean Memory V3 STM Service
 * 
 * Core service that provides Short-Term Memory functionality including:
 * - Memory lifecycle management
 * - Local semantic search
 * - Background sync with Jean Memory V2
 * - Conflict detection and resolution
 */

import {
  STMService,
  STMConfig,
  STMMemory,
  STMSearchQuery,
  STMSearchResult,
  STMSyncStatus,
  STMConflict,
  STMEvent,
  STMEventListener,
  STMStats,
  DEFAULT_STM_CONFIG,
} from './types';

import { STMConfigManager } from './config';
import { STMBrowserStorage } from './storage';
import { createEmbeddingService, EmbeddingService, EmbeddingUtils } from './embedding';

export class STMServiceImpl implements STMService {
  private config: STMConfig;
  private configManager: STMConfigManager;
  private storage: STMBrowserStorage | null = null;
  private embeddingService: EmbeddingService | null = null;
  private eventListeners: STMEventListener[] = [];
  
  private userId: string;
  private sessionId: string;
  private isInitialized = false;
  private syncTimer: NodeJS.Timeout | null = null;
  private cleanupTimer: NodeJS.Timeout | null = null;
  
  // Sync state
  private syncStatus: STMSyncStatus = {
    isOnline: navigator.onLine,
    lastSync: 0,
    pendingSync: 0,
    conflicts: 0,
    syncInProgress: false,
    totalMemories: 0,
    localMemories: 0,
    storageUsed: 0,
    storageQuota: 0,
  };
  
  private conflicts: STMConflict[] = [];

  constructor(userId: string, userConfig: Partial<STMConfig> = {}) {
    this.userId = userId;
    this.sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.configManager = new STMConfigManager(userConfig);
    this.config = { ...DEFAULT_STM_CONFIG, ...userConfig };
    
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnlineStatusChange.bind(this));
    window.addEventListener('offline', this.handleOnlineStatusChange.bind(this));
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    try {
      console.log('STM Service: Initializing...');
      
      // Initialize configuration manager
      await this.configManager.initialize();
      this.config = this.configManager.getConfig();
      
      // Initialize storage
      this.storage = new STMBrowserStorage(this.userId);
      await this.storage.initialize();
      
      // Initialize embedding service
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8765';
      this.embeddingService = await createEmbeddingService(
        this.config.localEmbedding,
        apiUrl
      );
      
      // Update sync status
      await this.updateSyncStatus();
      
      // Start background tasks
      this.startBackgroundTasks();
      
      // Cleanup expired memories
      await this.cleanupExpiredMemories();
      
      this.isInitialized = true;
      console.log('STM Service: Initialized successfully');
      
      this.emitEvent({ type: 'sync_started' });
      
    } catch (error) {
      console.error('STM Service: Failed to initialize:', error);
      throw error;
    }
  }

  async configure(config: Partial<STMConfig>): Promise<void> {
    this.config = { ...this.config, ...config };
    this.configManager.updateConfig(config);
    
    // Restart background tasks if sync settings changed
    if (config.autoSync !== undefined || config.syncInterval !== undefined) {
      this.stopBackgroundTasks();
      this.startBackgroundTasks();
    }
  }

  getConfig(): STMConfig {
    return { ...this.config };
  }

  async addMemory(content: string, metadata: any = {}): Promise<STMMemory> {
    this.ensureInitialized();
    
    const now = Date.now();
    const memory: STMMemory = {
      id: `stm_${now}_${Math.random().toString(36).substr(2, 9)}`,
      content,
      created_at: now,
      updated_at: now,
      user_id: this.userId,
      app_name: metadata.app_name || 'jean memory',
      memory_type: 'stm',
      session_id: this.sessionId,
      expires_at: this.config.memoryTTL > 0 ? now + this.config.memoryTTL : undefined,
      priority_score: this.calculatePriorityScore(content, metadata),
      access_count: 1,
      last_accessed: now,
      sync_status: 'pending',
      local_only: metadata.local_only || false,
      metadata: {
        categories: metadata.categories || [],
        tags: metadata.tags || [],
        source: metadata.source || 'user_input',
        ...metadata,
      },
    };
    
    // Generate embedding
    if (this.embeddingService) {
      try {
        memory.embedding = await this.embeddingService.embed(content);
      } catch (error) {
        console.warn('STM Service: Failed to generate embedding:', error);
      }
    }
    
    // Store memory
    await this.storage!.addMemory(memory);
    
    // Update sync status
    await this.updateSyncStatus();
    
    // Emit event
    this.emitEvent({ type: 'memory_added', memory });
    
    console.log('STM Service: Added memory:', memory.id);
    return memory;
  }

  async getMemory(id: string): Promise<STMMemory | null> {
    this.ensureInitialized();
    
    const memory = await this.storage!.getMemory(id);
    
    if (memory) {
      // Update access tracking
      memory.access_count++;
      memory.last_accessed = Date.now();
      await this.storage!.updateMemory(memory);
    }
    
    return memory;
  }

  async updateMemory(id: string, content: string, metadata: any = {}): Promise<STMMemory> {
    this.ensureInitialized();
    
    const existingMemory = await this.storage!.getMemory(id);
    if (!existingMemory) {
      throw new Error(`Memory not found: ${id}`);
    }
    
    const now = Date.now();
    const updatedMemory: STMMemory = {
      ...existingMemory,
      content,
      updated_at: now,
      last_accessed: now,
      access_count: existingMemory.access_count + 1,
      sync_status: 'pending',
      metadata: {
        ...existingMemory.metadata,
        ...metadata,
      },
    };
    
    // Regenerate embedding if content changed
    if (content !== existingMemory.content && this.embeddingService) {
      try {
        updatedMemory.embedding = await this.embeddingService.embed(content);
      } catch (error) {
        console.warn('STM Service: Failed to regenerate embedding:', error);
      }
    }
    
    await this.storage!.updateMemory(updatedMemory);
    
    // Update sync status
    await this.updateSyncStatus();
    
    // Emit event
    this.emitEvent({ type: 'memory_updated', memory: updatedMemory });
    
    return updatedMemory;
  }

  async deleteMemory(id: string): Promise<void> {
    this.ensureInitialized();
    
    await this.storage!.deleteMemory(id);
    
    // Update sync status
    await this.updateSyncStatus();
    
    // Emit event
    this.emitEvent({ type: 'memory_deleted', memory_id: id });
  }

  async search(query: STMSearchQuery): Promise<STMSearchResult[]> {
    this.ensureInitialized();
    
    if (!this.embeddingService) {
      throw new Error('STM Service: Embedding service not available');
    }
    
    const { 
      query: searchText, 
      limit = 10, 
      includeExpired = false,
      sessionOnly = false,
      similarityThreshold = 0.3,
      sortBy = 'relevance'
    } = query;
    
    try {
      // Generate query embedding
      const queryEmbedding = await this.embeddingService.embed(searchText);
      
      // Get candidate memories
      let memories: STMMemory[];
      if (sessionOnly) {
        memories = await this.storage!.getMemoriesBySession(this.sessionId);
      } else {
        memories = await this.storage!.getMemoriesByUser(this.userId);
      }
      
      // Filter out expired memories if needed
      if (!includeExpired) {
        const now = Date.now();
        memories = memories.filter(m => 
          !m.expires_at || m.expires_at > now
        );
      }
      
      // Calculate similarities and create results
      const results: STMSearchResult[] = [];
      
      for (const memory of memories) {
        if (memory.embedding) {
          const score = this.embeddingService.similarity(queryEmbedding, memory.embedding);
          
          if (score >= similarityThreshold) {
            results.push({
              memory,
              score,
              source: 'local',
            });
          }
        }
      }
      
      // Sort results
      results.sort((a, b) => {
        switch (sortBy) {
          case 'relevance':
            return b.score - a.score;
          case 'created_at':
            return b.memory.created_at - a.memory.created_at;
          case 'accessed_at':
            return b.memory.last_accessed - a.memory.last_accessed;
          case 'priority':
            return b.memory.priority_score - a.memory.priority_score;
          default:
            return b.score - a.score;
        }
      });
      
      // Update access tracking for results
      for (const result of results.slice(0, limit)) {
        result.memory.access_count++;
        result.memory.last_accessed = Date.now();
        await this.storage!.updateMemory(result.memory);
      }
      
      return results.slice(0, limit);
      
    } catch (error) {
      console.error('STM Service: Search failed:', error);
      throw error;
    }
  }

  async sync(): Promise<void> {
    if (this.syncStatus.syncInProgress) {
      console.log('STM Service: Sync already in progress');
      return;
    }
    
    this.syncStatus.syncInProgress = true;
    this.emitEvent({ type: 'sync_started' });
    
    try {
      // Get memories that need syncing
      const pendingMemories = await this.storage!.getMemoriesBySyncStatus('pending');
      
      let uploaded = 0;
      let downloaded = 0;
      let conflicts = 0;
      
      // TODO: Implement actual sync with Jean Memory V2 API
      // For now, just mark as synced
      for (const memory of pendingMemories) {
        if (!memory.local_only) {
          memory.sync_status = 'synced';
          await this.storage!.updateMemory(memory);
          uploaded++;
        }
      }
      
      // Update sync status
      this.syncStatus.lastSync = Date.now();
      await this.updateSyncStatus();
      
      this.emitEvent({ 
        type: 'sync_completed', 
        stats: { uploaded, downloaded, conflicts } 
      });
      
      console.log(`STM Service: Sync completed - uploaded: ${uploaded}, downloaded: ${downloaded}, conflicts: ${conflicts}`);
      
    } catch (error) {
      console.error('STM Service: Sync failed:', error);
      this.emitEvent({ type: 'sync_failed', error: String(error) });
      throw error;
    } finally {
      this.syncStatus.syncInProgress = false;
    }
  }

  getSyncStatus(): STMSyncStatus {
    return { ...this.syncStatus };
  }

  async resolveConflict(conflict: STMConflict, resolution: 'local' | 'remote' | 'merge'): Promise<void> {
    // TODO: Implement conflict resolution
    console.log('STM Service: Resolving conflict:', conflict.memory_id, resolution);
    
    // Remove from conflicts list
    this.conflicts = this.conflicts.filter(c => c.memory_id !== conflict.memory_id);
    await this.updateSyncStatus();
  }

  getConflicts(): STMConflict[] {
    return [...this.conflicts];
  }

  addEventListener(listener: STMEventListener): void {
    this.eventListeners.push(listener);
  }

  removeEventListener(listener: STMEventListener): void {
    const index = this.eventListeners.indexOf(listener);
    if (index > -1) {
      this.eventListeners.splice(index, 1);
    }
  }

  async getStats(): Promise<STMStats> {
    this.ensureInitialized();
    
    const storageStats = await this.storage!.getStorageStats();
    const memories = await this.storage!.getMemoriesByUser(this.userId);
    
    const syncedMemories = memories.filter(m => m.sync_status === 'synced').length;
    const pendingSync = memories.filter(m => m.sync_status === 'pending').length;
    
    let mostAccessedMemory: STMMemory | undefined;
    let maxAccessCount = 0;
    
    for (const memory of memories) {
      if (memory.access_count > maxAccessCount) {
        maxAccessCount = memory.access_count;
        mostAccessedMemory = memory;
      }
    }
    
    const averageMemorySize = storageStats.totalMemories > 0 
      ? storageStats.totalSize / storageStats.totalMemories 
      : 0;
    
    return {
      totalMemories: storageStats.totalMemories,
      localMemories: storageStats.totalMemories,
      syncedMemories,
      pendingSync,
      conflicts: this.conflicts.length,
      storageUsed: storageStats.totalSize,
      storageQuota: this.syncStatus.storageQuota,
      averageMemorySize,
      oldestMemory: storageStats.oldestMemory,
      newestMemory: storageStats.newestMemory,
      mostAccessedMemory,
      lastSyncTime: this.syncStatus.lastSync || undefined,
    };
  }

  async cleanup(): Promise<void> {
    this.stopBackgroundTasks();
    
    if (this.storage) {
      await this.storage.close();
    }
    
    if (this.embeddingService && 'dispose' in this.embeddingService) {
      (this.embeddingService as any).dispose();
    }
    
    window.removeEventListener('online', this.handleOnlineStatusChange.bind(this));
    window.removeEventListener('offline', this.handleOnlineStatusChange.bind(this));
    
    this.isInitialized = false;
  }

  // Private helper methods
  private ensureInitialized(): void {
    if (!this.isInitialized) {
      throw new Error('STM Service: Not initialized. Call initialize() first.');
    }
  }

  private calculatePriorityScore(content: string, metadata: any): number {
    let score = 0.5; // Base score
    
    // Adjust based on content length
    if (content.length > 100) score += 0.1;
    if (content.length > 500) score += 0.1;
    
    // Adjust based on metadata
    if (metadata.categories && metadata.categories.length > 0) score += 0.1;
    if (metadata.tags && metadata.tags.length > 0) score += 0.1;
    if (metadata.importance === 'high') score += 0.2;
    
    return Math.min(1.0, score);
  }

  private async updateSyncStatus(): Promise<void> {
    if (!this.storage) return;
    
    const stats = await this.storage.getStorageStats();
    const pendingMemories = await this.storage.getMemoriesBySyncStatus('pending');
    
    this.syncStatus.totalMemories = stats.totalMemories;
    this.syncStatus.localMemories = stats.totalMemories;
    this.syncStatus.pendingSync = pendingMemories.length;
    this.syncStatus.conflicts = this.conflicts.length;
    this.syncStatus.storageUsed = stats.totalSize;
    this.syncStatus.isOnline = navigator.onLine;
    
    // Check storage quota
    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate();
        this.syncStatus.storageQuota = estimate.quota || 0;
        
        // Emit warning if storage is getting full
        const usagePercent = this.syncStatus.storageUsed / this.syncStatus.storageQuota;
        if (usagePercent > 0.8) {
          this.emitEvent({
            type: 'storage_warning',
            usage: this.syncStatus.storageUsed,
            quota: this.syncStatus.storageQuota,
          });
        }
      } catch (error) {
        console.warn('STM Service: Could not check storage quota:', error);
      }
    }
  }

  private async cleanupExpiredMemories(): Promise<void> {
    if (!this.storage) return;
    
    const result = await this.storage.cleanup();
    console.log(`STM Service: Cleanup completed - deleted: ${result.deleted}, errors: ${result.errors}`);
  }

  private startBackgroundTasks(): void {
    if (this.config.autoSync && this.config.syncInterval > 0) {
      this.syncTimer = setInterval(() => {
        if (this.syncStatus.isOnline && !this.syncStatus.syncInProgress) {
          this.sync().catch(error => {
            console.error('STM Service: Background sync failed:', error);
          });
        }
      }, this.config.syncInterval);
    }
    
    // Cleanup timer (run every hour)
    this.cleanupTimer = setInterval(() => {
      this.cleanupExpiredMemories().catch(error => {
        console.error('STM Service: Background cleanup failed:', error);
      });
    }, 60 * 60 * 1000);
  }

  private stopBackgroundTasks(): void {
    if (this.syncTimer) {
      clearInterval(this.syncTimer);
      this.syncTimer = null;
    }
    
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
  }

  private handleOnlineStatusChange(): void {
    const wasOnline = this.syncStatus.isOnline;
    this.syncStatus.isOnline = navigator.onLine;
    
    if (!wasOnline && this.syncStatus.isOnline) {
      // Just came online, trigger sync
      console.log('STM Service: Back online, triggering sync...');
      this.sync().catch(error => {
        console.error('STM Service: Auto-sync after coming online failed:', error);
      });
    }
  }

  private emitEvent(event: STMEvent): void {
    for (const listener of this.eventListeners) {
      try {
        listener(event);
      } catch (error) {
        console.error('STM Service: Event listener error:', error);
      }
    }
  }
}