/**
 * Basic test for Jean Memory Node.js SDK
 * Run with: node dist/test.js
 */

import { JeanMemoryClient, JeanMemoryError } from './client';

async function testSDK() {
  console.log('🧪 Testing Jean Memory Node.js SDK...\n');

  // Test 1: Client initialization
  console.log('1. Testing client initialization...');
  
  try {
    // Should fail without API key
    new JeanMemoryClient({ apiKey: '' });
    console.log('❌ Should have failed without API key');
  } catch (error) {
    console.log('✅ Correctly rejected empty API key');
  }

  try {
    // Should fail with invalid API key format
    new JeanMemoryClient({ apiKey: 'invalid-key' });
    console.log('❌ Should have failed with invalid API key format');
  } catch (error) {
    console.log('✅ Correctly rejected invalid API key format');
  }

  try {
    // Should succeed with valid format
    const client = new JeanMemoryClient({ apiKey: 'jean_sk_test123' });
    console.log('✅ Client initialization successful');
  } catch (error) {
    console.log('❌ Client initialization failed:', error);
  }

  // Test 2: Method validation
  console.log('\n2. Testing method validation...');
  
  const client = new JeanMemoryClient({ 
    apiKey: 'jean_sk_test123',
    apiBase: 'https://httpbin.org' // Use httpbin for testing
  });

  try {
    await client.storeMemory('');
    console.log('❌ Should have failed with empty content');
  } catch (error) {
    console.log('✅ Correctly rejected empty memory content');
  }

  try {
    await client.retrieveMemories('');
    console.log('❌ Should have failed with empty query');
  } catch (error) {
    console.log('✅ Correctly rejected empty search query');
  }

  try {
    await client.retrieveMemories('test', { limit: 0 });
    console.log('❌ Should have failed with invalid limit');
  } catch (error) {
    console.log('✅ Correctly rejected invalid limit');
  }

  try {
    await client.listMemories({ offset: -1 });
    console.log('❌ Should have failed with negative offset');
  } catch (error) {
    console.log('✅ Correctly rejected negative offset');
  }

  // Test 3: Auth helper
  console.log('\n3. Testing auth helper...');
  
  try {
    const auth = client.createAuth();
    const { url, state, verifier } = auth.createAuthorizationUrl();
    
    console.log('✅ Auth URL generation successful');
    console.log(`   State length: ${state.length}`);
    console.log(`   Verifier length: ${verifier.length}`);
    console.log(`   URL starts with: ${url.substring(0, 50)}...`);
  } catch (error) {
    console.log('❌ Auth helper failed:', error);
  }

  // Test 4: Context generation
  console.log('\n4. Testing context generation...');
  
  try {
    // Mock client with no memories
    const mockClient = new JeanMemoryClient({ apiKey: 'jean_sk_test123' });
    
    // Override retrieveMemories to return empty array
    (mockClient as any).retrieveMemories = async () => [];
    
    const context = await mockClient.getContextLegacy('test query');
    
    if (context === 'No relevant context found.') {
      console.log('✅ Context generation for empty results works');
    } else {
      console.log('❌ Unexpected context result:', context);
    }
  } catch (error) {
    console.log('❌ Context generation failed:', error);
  }

  console.log('\n🎉 SDK tests completed!');
}

// Run tests if this file is executed directly
if (require.main === module) {
  testSDK().catch(console.error);
}

export { testSDK };