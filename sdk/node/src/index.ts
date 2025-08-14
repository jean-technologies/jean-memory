/**
 * Jean Memory Node.js SDK
 * Power your Next.js and other Node.js backends with perfect memory
 * 
 * @example
 * ```typescript
 * import { JeanMemoryClient } from '@jeanmemory/node';
 * 
 * const client = new JeanMemoryClient({ apiKey: 'jean_sk_...' });
 * await client.storeMemory('I prefer morning meetings');
 * const memories = await client.retrieveMemories('meeting preferences');
 * ```
 */

// Core client and error classes
export { JeanMemoryClient, JeanMemoryError } from './client';

// Authentication
export { JeanMemoryAuth } from './auth';

// Type definitions
export * from './types';

// Package metadata
export const SDK_VERSION = '1.0.1';
export const SDK_NAME = '@jeanmemory/node';