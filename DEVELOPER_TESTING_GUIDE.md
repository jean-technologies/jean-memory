# Jean Memory SDK Developer Testing Guide

**Purpose:** This guide allows any new developer to test the Jean Memory SDKs from scratch and provide feedback on what works vs what doesn't.

## 🎯 What We Know About the Codebase

### **Current Status (Based on Testing)**
- **React SDK**: Local code has all documented features, builds successfully
- **Node.js SDK**: Local code exports correct `JeanMemoryClient` class  
- **Python SDK**: Local code has correct `jean_memory` module structure
- **Published Packages**: May have stale/wrong code - needs verification

### **Core Architecture**
- **API Base**: `https://jean-memory-api-virginia.onrender.com`
- **Authentication**: Supabase OAuth flow with PKCE
- **Memory Storage**: MCP (Model Context Protocol) tools for memory operations
- **React Components**: `JeanProvider` wraps app, `JeanChat` provides UI

## 🧪 Test Suite for New Developers

Run these tests in order and document what works vs what fails.

### **Test 1: Fresh Environment Node.js SDK**

**Goal:** Verify Node.js SDK works as documented

```bash
# Create fresh test directory
mkdir /tmp/jean-node-test && cd /tmp/jean-node-test

# Install from npm
npm init -y
npm install @jeanmemory/node

# Create test file
cat > test.js << 'EOF'
const { JeanMemoryClient } = require('@jeanmemory/node');

console.log('Testing Node.js SDK...');

try {
  // Test 1: Import works
  console.log('✅ Import successful');
  
  // Test 2: Constructor works
  const client = new JeanMemoryClient({ apiKey: 'jean_sk_test123' });
  console.log('✅ Constructor successful');
  
  // Test 3: Check methods exist
  console.log('Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(client)));
  
} catch (error) {
  console.log('❌ Error:', error.message);
}
EOF

# Run test
node test.js
```

**Expected Result:** Should import `JeanMemoryClient` and show available methods
**Document:** What actually happens vs expected

### **Test 2: Fresh Environment Python SDK**

**Goal:** Verify Python SDK works as documented

```bash
# Create fresh test directory  
mkdir /tmp/jean-python-test && cd /tmp/jean-python-test

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install from PyPI
pip install jeanmemory

# Create test file
cat > test.py << 'EOF'
print("Testing Python SDK...")

try:
    # Test 1: Import works
    from jean_memory import JeanMemoryClient
    print("✅ Import successful")
    
    # Test 2: Constructor works
    client = JeanMemoryClient('jean_sk_test123')
    print("✅ Constructor successful")
    
    # Test 3: Check methods exist
    print("Available methods:", [method for method in dir(client) if not method.startswith('_')])
    
except ImportError as e:
    print("❌ Import failed:", e)
except Exception as e:
    print("❌ Error:", e)
EOF

# Run test
python test.py
```

**Expected Result:** Should import `JeanMemoryClient` from `jean_memory` module
**Document:** What actually happens vs expected

### **Test 3: Fresh Environment React SDK**

**Goal:** Verify React SDK works in Next.js

```bash
# Create fresh Next.js app
npx create-next-app@latest jean-react-test --typescript --tailwind --eslint --app --no-src-dir --import-alias="@/*"
cd jean-react-test

# Install React SDK
npm install @jeanmemory/react

# Create test page
cat > app/test/page.tsx << 'EOF'
'use client';

import { JeanProvider, JeanChat, useJean } from '@jeanmemory/react';

function TestComponent() {
  try {
    const jean = useJean();
    
    return (
      <div className="p-4">
        <h1>Jean SDK Test</h1>
        <p>✅ useJean hook loaded</p>
        <p>Available features:</p>
        <ul className="list-disc ml-6">
          <li>isAuthenticated: {jean.isAuthenticated ? 'Yes' : 'No'}</li>
          <li>sendMessage: {typeof jean.sendMessage}</li>
          <li>storeDocument: {typeof jean.storeDocument}</li>
          <li>connect: {typeof jean.connect}</li>
          <li>clearConversation: {typeof jean.clearConversation}</li>
          <li>tools.add_memory: {typeof jean.tools?.add_memory}</li>
          <li>tools.search_memory: {typeof jean.tools?.search_memory}</li>
        </ul>
      </div>
    );
  } catch (error) {
    return <div>❌ Error: {error.message}</div>;
  }
}

export default function TestPage() {
  return (
    <JeanProvider apiKey="jean_sk_test123">
      <TestComponent />
    </JeanProvider>
  );
}
EOF

# Update app/layout.tsx to not conflict
# Run dev server
npm run dev
```

**Expected Result:** Should show all documented useJean features
**Test URL:** `http://localhost:3000/test`
**Document:** What features show up vs documented features

### **Test 4: End-to-End React Chat Test**

**Goal:** Test actual chat functionality with real API

```bash
# In the same Next.js app, create chat test
cat > app/chat/page.tsx << 'EOF'
'use client';

import { JeanProvider, JeanChat } from '@jeanmemory/react';

export default function ChatTest() {
  return (
    <div style={{ height: '100vh' }}>
      <JeanProvider apiKey={process.env.NEXT_PUBLIC_JEAN_API_KEY || 'jean_sk_test123'}>
        <JeanChat />
      </JeanProvider>
    </div>
  );
}
EOF

# Create .env.local with real API key (if available)
echo "NEXT_PUBLIC_JEAN_API_KEY=your_real_api_key_here" > .env.local
```

**Expected Result:** Should show sign-in flow and chat interface
**Test URL:** `http://localhost:3000/chat`
**Document:** What UI appears, if sign-in works, if chat responds

### **Test 5: API Endpoint Direct Test**

**Goal:** Test the underlying API directly

```bash
# Test API health
curl -X GET "https://jean-memory-api-virginia.onrender.com/health"

# Test with sample data (if API key available)
curl -X POST "https://jean-memory-api-virginia.onrender.com/api/v1/mcp/tools/call" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "tool": "jean_memory",
    "arguments": {
      "user_message": "Hello, test message",
      "is_new_conversation": true
    }
  }'
```

**Expected Result:** Health check should return 200, tool call should work with valid API key
**Document:** API responses and error messages

## 📋 Testing Checklist

For each test, document:

### **What Works ✅**
- [ ] Package installs from npm/PyPI
- [ ] Imports work as documented  
- [ ] Constructor accepts documented parameters
- [ ] Methods exist as documented
- [ ] UI components render without errors
- [ ] Sign-in flow appears
- [ ] Chat interface loads

### **What Doesn't Work ❌**
- [ ] Import fails with error: `_____`
- [ ] Constructor fails with error: `_____`
- [ ] Missing documented methods: `_____`
- [ ] UI crashes with error: `_____`
- [ ] Sign-in doesn't work: `_____`
- [ ] Chat doesn't respond: `_____`

### **Discrepancies Between Docs and Reality**
- [ ] Documented class name vs actual: `_____`
- [ ] Documented import vs actual: `_____`
- [ ] Documented methods vs actual: `_____`
- [ ] Documented UI behavior vs actual: `_____`

## 🔍 Known Issues to Look For

Based on our testing, watch for these specific problems:

1. **Node.js SDK**: May export `JeanClient` instead of `JeanMemoryClient`
2. **Python SDK**: May fail on `from jean_memory import` vs `import jeanmemory`
3. **React SDK**: May be missing documented features like `storeDocument`, `tools`
4. **Build Issues**: React components may crash in Next.js due to SSR
5. **API Keys**: May need `jean_sk_` prefix format

## 📝 Feedback Template

After running all tests, provide feedback using this template:

```
## Test Results for Jean Memory SDKs

**Test Environment:**
- OS: _____ 
- Node.js: _____
- Python: _____
- Date: _____

**Node.js SDK:**
- ✅/❌ Install: 
- ✅/❌ Import:
- ✅/❌ Constructor:
- Notes: _____

**Python SDK:**
- ✅/❌ Install:
- ✅/❌ Import: 
- ✅/❌ Constructor:
- Notes: _____

**React SDK:**
- ✅/❌ Install:
- ✅/❌ Import:
- ✅/❌ Components render:
- ✅/❌ useJean hook:
- Missing features: _____
- Notes: _____

**Overall Assessment:**
- Ready for development: Yes/No
- Biggest blocking issue: _____
- Suggested fixes: _____
```

## 🎯 Success Criteria

The SDKs are ready when:

1. ✅ All packages install from public registries
2. ✅ All documented imports work exactly as shown
3. ✅ All documented examples run without modification
4. ✅ React components render in fresh Next.js app
5. ✅ Chat interface appears and handles sign-in
6. ✅ No discrepancies between docs and implementation

**Goal:** A new developer should be able to follow the docs and build a working app in 15 minutes.