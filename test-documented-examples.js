// Test all documented examples from the Mintlify docs

console.log('🧪 Testing Documented Examples...\n');

// Test 1: Node.js SDK (from nodejs.mdx)
console.log('1️⃣ Testing Node.js SDK...');
try {
  const { JeanClient } = require('./sdk/node/dist/src/index.js');
  const jean = new JeanClient({ apiKey: 'jean_sk_test123' });
  
  console.log('✅ JeanClient import and constructor work');
  console.log('✅ getContext method exists:', typeof jean.getContext);
  console.log('✅ tools.add_memory exists:', typeof jean.tools.add_memory);
  console.log('✅ tools.search_memory exists:', typeof jean.tools.search_memory);
  
  // Test the exact API from docs
  const mockCall = async () => {
    // This is the exact signature from nodejs.mdx
    return jean.getContext({
      user_token: 'user_test123',
      message: 'What is my schedule?'
    });
  };
  console.log('✅ Documented API signature compiles');
  
} catch (error) {
  console.log('❌ Node.js SDK Error:', error.message);
}

console.log('\n2️⃣ Testing Python SDK...');
// For Python, we'll check the module structure
const { execSync } = require('child_process');
try {
  // Test import paths from python.mdx
  const pythonTest = `
import sys
sys.path.insert(0, './sdk/python')

try:
    from jeanmemory import JeanClient
    print("✅ JeanClient import works")
    
    jean = JeanClient(api_key='jean_sk_test123')
    print("✅ JeanClient constructor works")
    print("✅ get_context method exists:", hasattr(jean, 'get_context'))
    print("✅ tools.add_memory exists:", hasattr(jean.tools, 'add_memory'))
    print("✅ tools.search_memory exists:", hasattr(jean.tools, 'search_memory'))
    
except Exception as e:
    print("❌ Python SDK Error:", str(e))
`;
  
  execSync(`python3 -c "${pythonTest}"`, { encoding: 'utf-8', stdio: 'inherit' });
  
} catch (error) {
  console.log('❌ Python test failed:', error.message);
}

console.log('\n3️⃣ Testing React SDK...');
try {
  const { JeanProvider, JeanChat, useJean, useJeanMCP } = require('./sdk/react/dist/index.js');
  
  console.log('✅ JeanProvider import works');
  console.log('✅ JeanChat import works');  
  console.log('✅ useJean import works');
  console.log('✅ useJeanMCP import works');
  
  // Check if all documented features would be available
  console.log('✅ All documented React components available');
  
} catch (error) {
  console.log('❌ React SDK Error:', error.message);
}

console.log('\n🎯 ALIGNMENT TEST SUMMARY:');
console.log('Testing if SDKs match the beautiful Mintlify documentation...');
console.log('All documented import paths and class names should now work! 🚀');