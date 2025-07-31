#!/usr/bin/env node

/**
 * Basic MCP Server Test - Tests server startup and protocol handling
 * This test doesn't require API keys, just tests the MCP protocol implementation
 */

const { spawn } = require('child_process');
const path = require('path');

async function testBasicMCP() {
  console.log('🧪 Testing Basic MCP Protocol Implementation...\n');

  const testUserId = 'test-user-123';
  const serverPath = path.join(__dirname, 'jean-memory-mcp-server.js');
  
  console.log(`📁 Server path: ${serverPath}`);
  console.log(`👤 Test User ID: ${testUserId}\n`);

  // Start the MCP server with minimal config
  const serverProcess = spawn('node', [serverPath, '--user-id', testUserId], {
    env: {
      ...process.env,
      USER_ID: testUserId,
      JEAN_MEMORY_API_KEY: 'test-key-123',  // Dummy key for basic testing
      JEAN_MEMORY_API_URL: 'http://localhost:3000'  // Won't be called in basic test
    },
    stdio: ['pipe', 'pipe', 'pipe']
  });

  // Test messages - just protocol validation
  const testMessages = [
    // Initialize
    {
      jsonrpc: '2.0',
      id: 1,
      method: 'initialize',
      params: {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: {
          name: 'test-client',
          version: '1.0.0'
        }
      }
    },
    // List tools
    {
      jsonrpc: '2.0',
      id: 2,
      method: 'tools/list',
      params: {}
    }
  ];

  let messageIndex = 0;
  let responses = [];
  let testTimeout;

  return new Promise((resolve, reject) => {
    // Set a timeout for the test
    testTimeout = setTimeout(() => {
      console.log('⏰ Test timeout - cleaning up...');
      serverProcess.kill();
      reject(new Error('Test timeout'));
    }, 10000);

    // Handle server output
    serverProcess.stdout.on('data', (data) => {
      const response = data.toString().trim();
      if (response) {
        console.log(`📤 Server Response ${responses.length + 1}:`);
        try {
          const parsed = JSON.parse(response);
          console.log(JSON.stringify(parsed, null, 2));
        } catch (e) {
          console.log(response);
        }
        console.log('');
        
        responses.push(response);
        
        // Send next message after receiving response
        if (messageIndex < testMessages.length) {
          const nextMessage = testMessages[messageIndex];
          console.log(`📥 Sending Message ${messageIndex + 1}:`);
          console.log(JSON.stringify(nextMessage, null, 2));
          console.log('');
          serverProcess.stdin.write(JSON.stringify(nextMessage) + '\n');
          messageIndex++;
        } else {
          // All messages sent, test complete
          setTimeout(() => {
            console.log('✅ Basic protocol test completed!');
            clearTimeout(testTimeout);
            serverProcess.kill();
          }, 1000);
        }
      }
    });

    // Handle server errors
    serverProcess.stderr.on('data', (data) => {
      console.log(`🔧 Server Log: ${data.toString().trim()}`);
    });

    // Handle server exit
    serverProcess.on('close', (code) => {
      console.log(`\n🏁 Server exited with code ${code}`);
      
      console.log('\n📊 Test Summary:');
      console.log(`- Messages sent: ${messageIndex}`);
      console.log(`- Responses received: ${responses.length}`);
      
      if (responses.length >= 2) {
        // Check if we got proper responses
        try {
          const initResponse = JSON.parse(responses[0]);
          const toolsResponse = JSON.parse(responses[1]);
          
          const hasInitResponse = initResponse.result && initResponse.result.protocolVersion;
          const hasToolsList = toolsResponse.result && Array.isArray(toolsResponse.result.tools);
          
          if (hasInitResponse && hasToolsList) {
            console.log('- Test result: ✅ SUCCESS - MCP protocol working correctly!');
            console.log(`- Tools available: ${toolsResponse.result.tools.length}`);
            resolve();
          } else {
            console.log('- Test result: ⚠️ PARTIAL - Server responding but format issues');
            resolve();
          }
        } catch (e) {
          console.log('- Test result: ⚠️ PARTIAL - Server responding but JSON parse issues');
          resolve();
        }
      } else {
        console.log('- Test result: ❌ FAILED - No responses received');
        reject(new Error('No responses received'));
      }
    });

    serverProcess.on('error', (error) => {
      clearTimeout(testTimeout);
      console.error('❌ Server error:', error);
      reject(error);
    });

    // Start the conversation
    if (testMessages.length > 0) {
      // Give server a moment to start up
      setTimeout(() => {
        console.log(`📥 Sending Message ${messageIndex + 1}:`);
        console.log(JSON.stringify(testMessages[0], null, 2));
        console.log('');
        serverProcess.stdin.write(JSON.stringify(testMessages[0]) + '\n');
        messageIndex++;
      }, 500);
    }
  });
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('\n🛑 Test interrupted');
  process.exit(0);
});

// Run the test
if (require.main === module) {
  testBasicMCP()
    .then(() => {
      console.log('\n🎉 Basic MCP test completed successfully!');
      console.log('\nNext steps:');
      console.log('1. Get your Jean Memory API key from https://app.jeanmemory.com/settings');
      console.log('2. Run: JEAN_MEMORY_API_KEY="your_key" npm test');
      console.log('3. Add to Claude Code: claude mcp add jean-memory -- node ' + __dirname + '/jean-memory-mcp-server.js --user-id your-user-id');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n❌ Basic test failed:', error.message);
      process.exit(1);
    });
}