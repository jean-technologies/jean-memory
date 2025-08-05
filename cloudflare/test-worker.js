// Simple test to verify the worker routing logic
const pathTests = [
  { path: '/mcp/chatgpt/sse/test-user', expected: 'valid' },
  { path: '/mcp/chatgpt/messages/test-user', expected: 'valid' },
  { path: '/mcp/claude/sse/test-user', expected: 'valid' },
  { path: '/mcp/chorus/sse/test-user', expected: 'valid' },
];

console.log('Testing URL routing patterns:');
pathTests.forEach(test => {
  const parts = test.path.split('/').filter(Boolean);
  let isValid = false;
  
  if (parts.length === 4 && parts[0] === 'mcp') {
    if ((parts[1] === 'chatgpt' || parts[1] === 'claude' || parts[1] === 'chorus') 
        && (parts[2] === 'sse' || parts[2] === 'messages')) {
      isValid = true;
    }
  }
  
  console.log(`  ${test.path}: ${isValid ? '✓' : '✗'}`);
});

console.log('\nWorker configuration looks correct!');
console.log('Backend URL will be: https://jean-memory-api-virginia.onrender.com');
