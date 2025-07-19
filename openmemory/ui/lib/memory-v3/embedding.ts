/**
 * Jean Memory V3 Local Embedding Service
 * 
 * Provides browser-based embedding generation using Transformers.js with:
 * - Local model execution (no server calls)
 * - WebAssembly acceleration
 * - Automatic model caching
 * - Similarity computation
 */

import { pipeline, Pipeline, env } from '@xenova/transformers';
import { EmbeddingService } from './types';

// Configure Transformers.js for browser usage
env.allowRemoteModels = true;
env.allowLocalModels = false;

export class STMEmbeddingService implements EmbeddingService {
  private pipeline: Pipeline | null = null;
  private isInitializing = false;
  private initializationPromise: Promise<void> | null = null;
  
  // Model configuration
  private readonly modelName = 'Xenova/all-MiniLM-L6-v2';
  private readonly dimensions = 384;
  
  async initialize(): Promise<void> {
    if (this.pipeline) return;
    
    if (this.isInitializing) {
      if (this.initializationPromise) {
        await this.initializationPromise;
      }
      return;
    }
    
    this.isInitializing = true;
    
    this.initializationPromise = this.loadModel();
    
    try {
      await this.initializationPromise;
    } finally {
      this.isInitializing = false;
      this.initializationPromise = null;
    }
  }
  
  private async loadModel(): Promise<void> {
    try {
      console.log('STM Embedding: Loading model...');
      
      // Create feature extraction pipeline
      this.pipeline = await pipeline('feature-extraction', this.modelName, {
        quantized: true, // Use quantized model for better performance
      });
      
      console.log('STM Embedding: Model loaded successfully');
      
      // Warm up the model with a test sentence
      await this.embed('Hello world');
      
      console.log('STM Embedding: Model warmed up and ready');
    } catch (error) {
      console.error('STM Embedding: Failed to load model:', error);
      throw new Error(`Failed to initialize embedding model: ${error}`);
    }
  }
  
  async embed(text: string): Promise<number[]> {
    if (!this.isReady()) {
      await this.initialize();
    }
    
    if (!this.pipeline) {
      throw new Error('STM Embedding: Model not available');
    }
    
    try {
      // Clean and preprocess text
      const cleanText = this.preprocessText(text);
      
      // Generate embedding
      const output = await this.pipeline(cleanText, {
        pooling: 'mean',
        normalize: true,
      });
      
      // Extract the embedding array
      let embedding: number[];
      
      if (output.data) {
        // Convert Float32Array to regular array
        embedding = Array.from(output.data);
      } else {
        // Handle different output formats
        embedding = Array.from(output);
      }
      
      // Verify dimensions
      if (embedding.length !== this.dimensions) {
        console.warn(`STM Embedding: Expected ${this.dimensions} dimensions, got ${embedding.length}`);
      }
      
      return embedding;
    } catch (error) {
      console.error('STM Embedding: Failed to generate embedding:', error);
      throw new Error(`Failed to generate embedding: ${error}`);
    }
  }
  
  private preprocessText(text: string): string {
    // Clean up text for better embedding quality
    return text
      .trim()
      .replace(/\s+/g, ' ') // Normalize whitespace
      .replace(/[^\w\s.,!?-]/g, '') // Remove special characters
      .substring(0, 512); // Limit to 512 characters for performance
  }
  
  similarity(embedding1: number[], embedding2: number[]): number {
    if (embedding1.length !== embedding2.length) {
      throw new Error('STM Embedding: Embeddings must have the same length');
    }
    
    // Compute cosine similarity
    let dotProduct = 0;
    let norm1 = 0;
    let norm2 = 0;
    
    for (let i = 0; i < embedding1.length; i++) {
      dotProduct += embedding1[i] * embedding2[i];
      norm1 += embedding1[i] * embedding1[i];
      norm2 += embedding2[i] * embedding2[i];
    }
    
    // Avoid division by zero
    if (norm1 === 0 || norm2 === 0) {
      return 0;
    }
    
    return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
  }
  
  isReady(): boolean {
    return this.pipeline !== null && !this.isInitializing;
  }
  
  getDimensions(): number {
    return this.dimensions;
  }
  
  getModelName(): string {
    return this.modelName;
  }
  
  // Batch processing for efficiency
  async embedBatch(texts: string[]): Promise<number[][]> {
    const embeddings: number[][] = [];
    
    // Process in batches to avoid memory issues
    const batchSize = 10;
    
    for (let i = 0; i < texts.length; i += batchSize) {
      const batch = texts.slice(i, i + batchSize);
      const batchPromises = batch.map(text => this.embed(text));
      const batchEmbeddings = await Promise.all(batchPromises);
      embeddings.push(...batchEmbeddings);
    }
    
    return embeddings;
  }
  
  // Memory cleanup
  dispose(): void {
    if (this.pipeline) {
      // Transformers.js doesn't expose a disposal method,
      // but we can at least clear our reference
      this.pipeline = null;
    }
  }
}

// Singleton instance for global use
let embeddingServiceInstance: STMEmbeddingService | null = null;

export function getEmbeddingService(): STMEmbeddingService {
  if (!embeddingServiceInstance) {
    embeddingServiceInstance = new STMEmbeddingService();
  }
  return embeddingServiceInstance;
}

// Utility functions for embedding operations
export class EmbeddingUtils {
  static async findSimilar(
    queryEmbedding: number[],
    candidateEmbeddings: { id: string; embedding: number[] }[],
    threshold: number = 0.7,
    limit: number = 10
  ): Promise<{ id: string; score: number }[]> {
    const embeddingService = getEmbeddingService();
    
    // Calculate similarities
    const similarities = candidateEmbeddings.map(candidate => ({
      id: candidate.id,
      score: embeddingService.similarity(queryEmbedding, candidate.embedding)
    }));
    
    // Filter by threshold and sort by score
    return similarities
      .filter(item => item.score >= threshold)
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  }
  
  static averageEmbedding(embeddings: number[][]): number[] {
    if (embeddings.length === 0) return [];
    
    const dimensions = embeddings[0].length;
    const average = new Array(dimensions).fill(0);
    
    for (const embedding of embeddings) {
      for (let i = 0; i < dimensions; i++) {
        average[i] += embedding[i];
      }
    }
    
    for (let i = 0; i < dimensions; i++) {
      average[i] /= embeddings.length;
    }
    
    return average;
  }
  
  static normalizeEmbedding(embedding: number[]): number[] {
    let norm = 0;
    for (const value of embedding) {
      norm += value * value;
    }
    norm = Math.sqrt(norm);
    
    if (norm === 0) return embedding;
    
    return embedding.map(value => value / norm);
  }
}

// Fallback service for when local embeddings are not available
export class FallbackEmbeddingService implements EmbeddingService {
  private apiUrl: string;
  
  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }
  
  async embed(text: string): Promise<number[]> {
    try {
      const response = await fetch(`${this.apiUrl}/api/v1/embeddings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      return data.embedding;
    } catch (error) {
      throw new Error(`Fallback embedding failed: ${error}`);
    }
  }
  
  similarity(embedding1: number[], embedding2: number[]): number {
    // Use the same cosine similarity implementation
    return getEmbeddingService().similarity(embedding1, embedding2);
  }
  
  isReady(): boolean {
    return true; // Assume API is always ready
  }
  
  getDimensions(): number {
    return 384; // Assume same dimensions as local model
  }
}

// Factory function to create the appropriate embedding service
export async function createEmbeddingService(
  preferLocal: boolean = true,
  fallbackApiUrl?: string
): Promise<EmbeddingService> {
  if (preferLocal) {
    try {
      const localService = getEmbeddingService();
      await localService.initialize();
      return localService;
    } catch (error) {
      console.warn('STM Embedding: Local service failed, falling back to API:', error);
      
      if (fallbackApiUrl) {
        return new FallbackEmbeddingService(fallbackApiUrl);
      } else {
        throw new Error('Local embedding failed and no fallback API provided');
      }
    }
  } else if (fallbackApiUrl) {
    return new FallbackEmbeddingService(fallbackApiUrl);
  } else {
    throw new Error('No embedding service configuration provided');
  }
}