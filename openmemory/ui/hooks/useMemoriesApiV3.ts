/**
 * Jean Memory V3 Enhanced API Hook
 * 
 * Extends the existing useMemoriesApi with STM (Short-Term Memory) capabilities.
 * Provides seamless integration between local STM and remote Jean Memory V2.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { useMemoriesApi, SimpleMemory } from './useMemoriesApi';
import { Memory } from '@/components/types';

// STM imports
import {
  createSTMService,
  isSTMSupported,
  STMServiceImpl,
  STMConfig,
  STMMemory,
  STMSearchQuery,
  STMSearchResult,
  STMSyncStatus,
  STMStats,
  STMEventListener,
  DEFAULT_STM_CONFIG,
} from '@/lib/memory-v3';

// Enhanced search options
interface V3SearchOptions {
  query?: string;
  filters?: {
    apps?: string[];
    categories?: string[];
    sortColumn?: string;
    sortDirection?: 'asc' | 'desc';
    showArchived?: boolean;
    groupThreads?: boolean;
  };
  useSTM?: boolean;
  stmOnly?: boolean;
  hybridSearch?: boolean;
  similarityThreshold?: number;
}

// Enhanced return type
interface UseMemoriesApiV3Return {
  // Extended from original API
  fetchMemories: (
    query?: string,
    filters?: {
      apps?: string[];
      categories?: string[];
      sortColumn?: string;
      sortDirection?: 'asc' | 'desc';
      showArchived?: boolean;
      groupThreads?: boolean;
    }
  ) => Promise<{ memories: Memory[]; total: number }>;
  
  fetchMemoryById: (memoryId: string) => Promise<void>;
  fetchAccessLogs: (memoryId: string, page?: number, pageSize?: number) => Promise<void>;
  fetchRelatedMemories: (memoryId: string) => Promise<void>;
  createMemory: (text: string, useSTM?: boolean) => Promise<void>;
  deleteMemories: (memoryIds: string[]) => Promise<void>;
  updateMemory: (memoryId: string, content: string) => Promise<void>;
  updateMemoryState: (memoryIds: string[], state: string) => Promise<void>;
  
  // V3 STM-specific methods
  searchV3: (options: V3SearchOptions) => Promise<{ memories: Memory[]; total: number; source: 'stm' | 'ltm' | 'hybrid' }>;
  createSTMMemory: (text: string, metadata?: any) => Promise<STMMemory>;
  searchSTM: (query: STMSearchQuery) => Promise<STMSearchResult[]>;
  syncSTM: () => Promise<void>;
  configureSTM: (config: Partial<STMConfig>) => Promise<void>;
  
  // STM status and control
  isSTMEnabled: boolean;
  isSTMReady: boolean;
  enableSTM: () => Promise<void>;
  disableSTM: () => void;
  getSTMStatus: () => STMSyncStatus | null;
  getSTMStats: () => Promise<STMStats | null>;
  
  // Original properties
  isLoading: boolean;
  error: string | null;
  hasUpdates: number;
  memories: Memory[];
  selectedMemory: SimpleMemory | null;
}

export const useMemoriesApiV3 = (): UseMemoriesApiV3Return => {
  // Get original API hook
  const originalApi = useMemoriesApi();
  
  // User ID from Redux store
  const user_id = useSelector((state: RootState) => state.profile.userId);
  
  // STM state
  const [isSTMEnabled, setIsSTMEnabled] = useState(false);
  const [isSTMReady, setIsSTMReady] = useState(false);
  const [stmStatus, setSTMStatus] = useState<STMSyncStatus | null>(null);
  const [stmError, setSTMError] = useState<string | null>(null);
  
  // STM service reference
  const stmServiceRef = useRef<STMServiceImpl | null>(null);
  const eventListenerRef = useRef<STMEventListener | null>(null);
  
  // STM configuration
  const stmConfig: Partial<STMConfig> = {
    ...DEFAULT_STM_CONFIG,
    maxMemories: 10000,
    localEmbedding: true,
    autoSync: true,
    syncInterval: 5 * 60 * 1000, // 5 minutes
  };

  // Initialize STM service
  const initializeSTM = useCallback(async () => {
    if (!user_id || !isSTMSupported()) {
      console.warn('STM: Cannot initialize - user not logged in or browser not supported');
      return;
    }

    try {
      console.log('STM: Initializing service...');
      
      const service = await createSTMService(user_id, stmConfig);
      stmServiceRef.current = service;
      
      // Set up event listener
      const eventListener: STMEventListener = (event) => {
        console.log('STM Event:', event.type, event);
        
        switch (event.type) {
          case 'sync_completed':
            // Refresh memories after sync
            originalApi.fetchMemories().catch(console.error);
            break;
          case 'sync_failed':
            setSTMError(`Sync failed: ${event.error}`);
            break;
          case 'storage_warning':
            console.warn('STM: Storage warning', event.usage, event.quota);
            break;
        }
        
        // Update status
        if (stmServiceRef.current) {
          setSTMStatus(stmServiceRef.current.getSyncStatus());
        }
      };
      
      service.addEventListener(eventListener);
      eventListenerRef.current = eventListener;
      
      setIsSTMReady(true);
      setSTMStatus(service.getSyncStatus());
      setSTMError(null);
      
      console.log('STM: Service initialized successfully');
      
    } catch (error) {
      console.error('STM: Failed to initialize:', error);
      setSTMError(String(error));
      setIsSTMReady(false);
    }
  }, [user_id]);

  // Enable STM
  const enableSTM = useCallback(async () => {
    if (!isSTMSupported()) {
      throw new Error('STM not supported in this browser');
    }
    
    setIsSTMEnabled(true);
    await initializeSTM();
  }, [initializeSTM]);

  // Disable STM
  const disableSTM = useCallback(() => {
    if (stmServiceRef.current) {
      if (eventListenerRef.current) {
        stmServiceRef.current.removeEventListener(eventListenerRef.current);
      }
      stmServiceRef.current.cleanup().catch(console.error);
      stmServiceRef.current = null;
    }
    
    setIsSTMEnabled(false);
    setIsSTMReady(false);
    setSTMStatus(null);
    setSTMError(null);
  }, []);

  // Enhanced create memory with STM support
  const createMemory = useCallback(async (text: string, useSTM: boolean = false): Promise<void> => {
    if (useSTM && isSTMReady && stmServiceRef.current) {
      try {
        await stmServiceRef.current.addMemory(text, {
          app_name: 'jean memory',
          source: 'web_ui',
        });
        
        // Update STM status
        setSTMStatus(stmServiceRef.current.getSyncStatus());
        
        // Still create in the original system for compatibility
        await originalApi.createMemory(text);
        
      } catch (error) {
        console.error('STM: Failed to create memory:', error);
        setSTMError(String(error));
        // Fallback to original API
        await originalApi.createMemory(text);
      }
    } else {
      await originalApi.createMemory(text);
    }
  }, [originalApi, isSTMReady]);

  // Create STM-only memory
  const createSTMMemory = useCallback(async (text: string, metadata: any = {}): Promise<STMMemory> => {
    if (!isSTMReady || !stmServiceRef.current) {
      throw new Error('STM not ready');
    }
    
    return await stmServiceRef.current.addMemory(text, metadata);
  }, [isSTMReady]);

  // STM search
  const searchSTM = useCallback(async (query: STMSearchQuery): Promise<STMSearchResult[]> => {
    if (!isSTMReady || !stmServiceRef.current) {
      throw new Error('STM not ready');
    }
    
    return await stmServiceRef.current.search(query);
  }, [isSTMReady]);

  // Enhanced search with STM integration
  const searchV3 = useCallback(async (options: V3SearchOptions): Promise<{ 
    memories: Memory[]; 
    total: number; 
    source: 'stm' | 'ltm' | 'hybrid' 
  }> => {
    const { 
      query, 
      filters, 
      useSTM = isSTMEnabled, 
      stmOnly = false, 
      hybridSearch = true,
      similarityThreshold = 0.3 
    } = options;

    if (stmOnly && (!useSTM || !isSTMReady || !stmServiceRef.current)) {
      return { memories: [], total: 0, source: 'stm' };
    }

    try {
      let stmResults: STMSearchResult[] = [];
      let ltmResults: { memories: Memory[]; total: number } = { memories: [], total: 0 };

      // Search STM if enabled
      if (useSTM && isSTMReady && stmServiceRef.current && query) {
        try {
          stmResults = await stmServiceRef.current.search({
            query,
            limit: 50,
            similarityThreshold,
            sortBy: 'relevance',
          });
        } catch (error) {
          console.warn('STM: Search failed, falling back to LTM only:', error);
        }
      }

      // Search LTM unless STM-only mode
      if (!stmOnly) {
        ltmResults = await originalApi.fetchMemories(query, filters);
      }

      // Convert STM results to Memory format
      const stmMemories: Memory[] = stmResults.map(result => ({
        id: result.memory.id,
        memory: result.memory.content,
        created_at: result.memory.created_at,
        state: 'active' as const,
        metadata: result.memory.metadata,
        categories: result.memory.metadata?.categories || [],
        client: 'stm' as const,
        app_name: result.memory.app_name,
      }));

      // Determine result composition
      if (stmOnly) {
        return {
          memories: stmMemories,
          total: stmMemories.length,
          source: 'stm',
        };
      } else if (!useSTM || stmMemories.length === 0) {
        return {
          memories: ltmResults.memories,
          total: ltmResults.total,
          source: 'ltm',
        };
      } else if (hybridSearch) {
        // Merge results, prioritizing STM for recent/relevant content
        const mergedMemories = [...stmMemories];
        
        // Add LTM results that aren't duplicates
        for (const ltmMemory of ltmResults.memories) {
          const isDuplicate = stmMemories.some(stmMemory => 
            stmMemory.memory.toLowerCase().includes(ltmMemory.memory.toLowerCase()) ||
            ltmMemory.memory.toLowerCase().includes(stmMemory.memory.toLowerCase())
          );
          
          if (!isDuplicate) {
            mergedMemories.push(ltmMemory);
          }
        }
        
        return {
          memories: mergedMemories.slice(0, 50), // Limit total results
          total: mergedMemories.length,
          source: 'hybrid',
        };
      } else {
        // Use STM results only
        return {
          memories: stmMemories,
          total: stmMemories.length,
          source: 'stm',
        };
      }

    } catch (error) {
      console.error('V3 Search error:', error);
      // Fallback to original API
      const fallbackResults = await originalApi.fetchMemories(query, filters);
      return {
        memories: fallbackResults.memories,
        total: fallbackResults.total,
        source: 'ltm',
      };
    }
  }, [originalApi, isSTMEnabled, isSTMReady]);

  // STM sync
  const syncSTM = useCallback(async (): Promise<void> => {
    if (!isSTMReady || !stmServiceRef.current) {
      throw new Error('STM not ready');
    }
    
    await stmServiceRef.current.sync();
    setSTMStatus(stmServiceRef.current.getSyncStatus());
  }, [isSTMReady]);

  // Configure STM
  const configureSTM = useCallback(async (config: Partial<STMConfig>): Promise<void> => {
    if (!isSTMReady || !stmServiceRef.current) {
      throw new Error('STM not ready');
    }
    
    await stmServiceRef.current.configure(config);
  }, [isSTMReady]);

  // Get STM status
  const getSTMStatus = useCallback((): STMSyncStatus | null => {
    return stmStatus;
  }, [stmStatus]);

  // Get STM stats
  const getSTMStats = useCallback(async (): Promise<STMStats | null> => {
    if (!isSTMReady || !stmServiceRef.current) {
      return null;
    }
    
    return await stmServiceRef.current.getStats();
  }, [isSTMReady]);

  // Auto-initialize STM if enabled and user is logged in
  useEffect(() => {
    if (isSTMEnabled && user_id && !isSTMReady && !stmServiceRef.current) {
      initializeSTM();
    }
  }, [isSTMEnabled, user_id, isSTMReady, initializeSTM]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disableSTM();
    };
  }, [disableSTM]);

  // Combined error state
  const combinedError = originalApi.error || stmError;

  return {
    // Original API methods
    fetchMemories: originalApi.fetchMemories,
    fetchMemoryById: originalApi.fetchMemoryById,
    fetchAccessLogs: originalApi.fetchAccessLogs,
    fetchRelatedMemories: originalApi.fetchRelatedMemories,
    deleteMemories: originalApi.deleteMemories,
    updateMemory: originalApi.updateMemory,
    updateMemoryState: originalApi.updateMemoryState,

    // Enhanced methods
    createMemory,
    searchV3,

    // STM-specific methods
    createSTMMemory,
    searchSTM,
    syncSTM,
    configureSTM,

    // STM status and control
    isSTMEnabled,
    isSTMReady,
    enableSTM,
    disableSTM,
    getSTMStatus,
    getSTMStats,

    // Original properties
    isLoading: originalApi.isLoading,
    error: combinedError,
    hasUpdates: originalApi.hasUpdates,
    memories: originalApi.memories,
    selectedMemory: originalApi.selectedMemory,
  };
};