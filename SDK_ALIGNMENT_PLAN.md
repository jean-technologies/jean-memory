# SDK Alignment Plan: Fixing the Documentation vs Implementation Gap

**Status:** 🚨 CRITICAL - Complete misalignment between Mintlify docs and actual SDKs  
**Goal:** Align implementations with the excellent Mintlify documentation  
**Approach:** Update SDKs to match docs (docs are perfect, implementations are wrong)

## 📊 Current State Analysis

### **What the Mintlify Docs Promise (CORRECT TARGET)**

#### Node.js SDK (nodejs.mdx)
```typescript
import { JeanClient } from '@jeanmemory/node';
const jean = new JeanClient({ apiKey: process.env.JEAN_API_KEY });

const contextResponse = await jean.getContext({
  user_token: userToken,
  message: currentMessage,
  speed: "balanced",    // optional
  tool: "jean_memory",  // optional  
  format: "enhanced"    // optional
});

// Advanced tool access
await jean.tools.add_memory({ user_token: ..., content: "..." });
const results = await jean.tools.search_memory({ user_token: ..., query: "..." });
```

#### Python SDK (python.mdx)
```python
from jeanmemory import JeanClient
jean = JeanClient(api_key=os.environ.get("JEAN_API_KEY"))

context_response = jean.get_context(
    user_token=user_token,
    message=user_message,
    speed="balanced",    # optional
    tool="jean_memory",  # optional
    format="enhanced"    # optional
)

# Advanced tool access
jean.tools.add_memory(user_token=..., content="...")
results = jean.tools.search_memory(user_token=..., query="...")
```

#### React SDK (react.mdx)
```typescript
import { JeanProvider, JeanChat, useJean } from '@jeanmemory/react';

const {
  isAuthenticated, user, messages,
  sendMessage, storeDocument, connect, clearConversation, setUser, signOut,
  tools: { add_memory, search_memory }
} = useJean();
```

### **What We Actually Built (WRONG)**

#### Node.js SDK
```typescript
import { JeanMemoryClient } from '@jeanmemory/node';  // ❌ Wrong class name
const client = new JeanMemoryClient({ apiKey: '...' });

await client.storeMemory('...');     // ❌ Wrong method
await client.retrieveMemories('...'); // ❌ Wrong method
// ❌ Missing: getContext() - the main API from docs
```

#### Python SDK  
```python
from jean_memory import JeanMemoryClient  # ❌ Wrong import & class
client = JeanMemoryClient('...')

client.store_memory('...')      # ❌ Wrong method
client.retrieve_memories('...') # ❌ Wrong method
# ❌ Missing: get_context() - the main API from docs
```

#### React SDK
```typescript
// ✅ Import paths correct, but missing features:
// ❌ Missing: useJeanMCP hook (docs show it)
// ❌ Missing: Complete tools object in useJean
```

## 🎯 ALIGNMENT STRATEGY

### **Phase 1: Node.js SDK Fixes**

**Goal:** Make the Node.js SDK match nodejs.mdx exactly

#### 1.1 Add `JeanClient` Class Alias
```typescript
// In sdk/node/src/index.ts
export { JeanMemoryClient as JeanClient } from './client';
export { JeanMemoryClient } from './client'; // Keep for backward compatibility
```

#### 1.2 Add `getContext()` Method
```typescript
// In sdk/node/src/client.ts
export class JeanMemoryClient {
  // Add the main API method from docs
  async getContext(options: {
    user_token: string;
    message: string;
    speed?: 'fast' | 'balanced' | 'comprehensive';
    tool?: 'jean_memory' | 'search_memory';
    format?: 'simple' | 'enhanced';
  }): Promise<ContextResponse> {
    // Implementation using MCP calls
    return await makeMCPRequest(
      { access_token: options.user_token }, 
      this.apiKey,
      options.tool || 'jean_memory',
      {
        user_message: options.message,
        speed: options.speed || 'balanced',
        format: options.format || 'enhanced'
      }
    );
  }

  // Add tools namespace as documented
  tools = {
    add_memory: async (options: { user_token: string; content: string }) => {
      return await makeMCPRequest(
        { access_token: options.user_token },
        this.apiKey,
        'add_memory',
        { content: options.content }
      );
    },
    
    search_memory: async (options: { user_token: string; query: string }) => {
      return await makeMCPRequest(
        { access_token: options.user_token },
        this.apiKey,
        'search_memory', 
        { query: options.query }
      );
    }
  };
}
```

### **Phase 2: Python SDK Fixes**

**Goal:** Make the Python SDK match python.mdx exactly

#### 2.1 Add `JeanClient` Class Alias
```python
# In sdk/python/jean_memory/__init__.py
from .client import JeanMemoryClient as JeanClient
from .client import JeanMemoryClient  # Keep for backward compatibility
```

#### 2.2 Add `get_context()` Method
```python
# In sdk/python/jean_memory/client.py
class JeanMemoryClient:
    def get_context(
        self,
        user_token: str,
        message: str,
        speed: str = "balanced",
        tool: str = "jean_memory", 
        format: str = "enhanced"
    ) -> ContextResponse:
        """Main context API matching the documentation."""
        # Implementation using MCP calls
        return self._make_mcp_request(
            user_token=user_token,
            tool=tool,
            arguments={
                'user_message': message,
                'speed': speed,
                'format': format
            }
        )
    
    # Add tools namespace as documented
    class Tools:
        def __init__(self, client):
            self.client = client
            
        def add_memory(self, user_token: str, content: str):
            return self.client._make_mcp_request(
                user_token=user_token,
                tool='add_memory',
                arguments={'content': content}
            )
            
        def search_memory(self, user_token: str, query: str):
            return self.client._make_mcp_request(
                user_token=user_token,
                tool='search_memory',
                arguments={'query': query}
            )
    
    def __init__(self, api_key: str):
        # ... existing init ...
        self.tools = self.Tools(self)
```

### **Phase 3: React SDK Fixes**

**Goal:** Ensure React SDK matches react.mdx exactly  

#### 3.1 Verify All Documented Features Exist
```typescript
// In sdk/react/provider.tsx - ensure these are all available:
interface JeanContextValue {
  // State (✅ already correct)
  isAuthenticated: boolean;
  user: JeanUser | null;
  messages: JeanMessage[];
  
  // Methods (✅ we added these)
  sendMessage: (message: string) => Promise<void>;
  storeDocument: (title: string, content: string) => Promise<void>;
  connect: (service: 'notion' | 'slack' | 'gdrive') => void;
  clearConversation: () => void;
  setUser: (user: JeanUser) => void;
  signOut: () => void;
  
  // Tools (✅ we added these)
  tools: {
    add_memory: (content: string) => Promise<any>;
    search_memory: (query: string) => Promise<any>;
  };
}
```

#### 3.2 Add useJeanMCP Hook (Missing from our implementation)
```typescript
// In sdk/react/useJeanMCP.tsx
export function useJeanMCP({ apiKey }: { apiKey: string }) {
  const addMemory = async (user: JeanUser, content: string) => {
    return await makeMCPRequest(user, apiKey, 'add_memory', { content });
  };
  
  const searchMemory = async (user: JeanUser, query: string) => {
    return await makeMCPRequest(user, apiKey, 'search_memory', { query });
  };
  
  const storeDocument = async (user: JeanUser, title: string, content: string, type = 'markdown') => {
    return await makeMCPRequest(user, apiKey, 'store_document', { title, content, document_type: type });
  };
  
  const callJeanMemory = async (user: JeanUser, message: string, isNewConversation = false) => {
    return await makeMCPRequest(user, apiKey, 'jean_memory', { 
      user_message: message, 
      is_new_conversation: isNewConversation 
    });
  };
  
  return {
    addMemory,
    searchMemory, 
    storeDocument,
    callJeanMemory
  };
}
```

## 📋 IMPLEMENTATION PLAN

### **Step 1: Code Updates (2-3 hours)**

1. **Node.js SDK**
   - Add `JeanClient` export alias
   - Implement `getContext()` method
   - Add `tools` namespace
   - Keep existing methods for backward compatibility

2. **Python SDK** 
   - Add `JeanClient` import alias
   - Implement `get_context()` method
   - Add `tools` namespace
   - Keep existing methods for backward compatibility

3. **React SDK**
   - Verify all documented features exist (✅ mostly done)
   - Add missing `useJeanMCP` hook
   - Ensure exports match docs exactly

### **Step 2: Build & Test (30 minutes)**

1. Build all SDKs locally
2. Run the testing suite against updated packages
3. Verify all documented examples work

### **Step 3: Publish (30 minutes)**

1. Bump versions to 1.1.0 (major API additions)
2. Publish to npm/PyPI with correct org account
3. Test published packages immediately

### **Step 4: Update Testing Guide (15 minutes)**

1. Update test scripts to use correct class names
2. Add tests for new `getContext()` and `get_context()` methods
3. Test the documented examples exactly as written

## 🧪 REVISED TESTING SUITE

### **Test 1: Node.js SDK (Updated)**
```bash
# Test both old and new APIs
cat > test.js << 'EOF'
const { JeanClient, JeanMemoryClient } = require('@jeanmemory/node');

console.log('Testing Node.js SDK...');

try {
  // Test 1: New documented API
  const jean = new JeanClient({ apiKey: 'jean_sk_test123' });
  console.log('✅ JeanClient constructor works');
  console.log('✅ getContext method exists:', typeof jean.getContext);
  console.log('✅ tools.add_memory exists:', typeof jean.tools.add_memory);
  console.log('✅ tools.search_memory exists:', typeof jean.tools.search_memory);
  
  // Test 2: Backward compatibility 
  const client = new JeanMemoryClient({ apiKey: 'jean_sk_test123' });
  console.log('✅ JeanMemoryClient still works');
  
} catch (error) {
  console.log('❌ Error:', error.message);
}
EOF
```

### **Test 2: Python SDK (Updated)**
```bash
cat > test.py << 'EOF'
print("Testing Python SDK...")

try:
    # Test 1: New documented API
    from jeanmemory import JeanClient
    jean = JeanClient(api_key='jean_sk_test123')
    print("✅ JeanClient import and constructor work")
    print("✅ get_context method exists:", hasattr(jean, 'get_context'))
    print("✅ tools.add_memory exists:", hasattr(jean.tools, 'add_memory'))
    print("✅ tools.search_memory exists:", hasattr(jean.tools, 'search_memory'))
    
    # Test 2: Backward compatibility
    from jean_memory import JeanMemoryClient
    client = JeanMemoryClient('jean_sk_test123') 
    print("✅ JeanMemoryClient still works")
    
except Exception as e:
    print("❌ Error:", e)
EOF
```

### **Test 3: React SDK (Updated)**
```bash
# Test all documented components and hooks
cat > TestComponent.tsx << 'EOF'
import { JeanProvider, JeanChat, useJean, useJeanMCP } from '@jeanmemory/react';

function TestComponent() {
  const jean = useJean();
  const mcpTools = useJeanMCP({ apiKey: 'test' });
  
  console.log('✅ useJean hook works');
  console.log('✅ sendMessage exists:', typeof jean.sendMessage);
  console.log('✅ storeDocument exists:', typeof jean.storeDocument);
  console.log('✅ tools.add_memory exists:', typeof jean.tools.add_memory);
  console.log('✅ useJeanMCP hook works');
  console.log('✅ mcpTools.addMemory exists:', typeof mcpTools.addMemory);
  
  return <div>All documented features available!</div>;
}
EOF
```

## 🎯 SUCCESS CRITERIA

**After implementation, these EXACT examples from Mintlify docs must work:**

### Node.js (from nodejs.mdx)
```typescript
import { JeanClient } from '@jeanmemory/node';
const jean = new JeanClient({ apiKey: process.env.JEAN_API_KEY });
const contextResponse = await jean.getContext({
  user_token: userToken,
  message: currentMessage
}); // ✅ Must work exactly as shown
```

### Python (from python.mdx)  
```python
from jeanmemory import JeanClient
jean = JeanClient(api_key=os.environ.get("JEAN_API_KEY"))
context_response = jean.get_context(
    user_token=user_token,
    message=user_message
) # ✅ Must work exactly as shown
```

### React (from react.mdx)
```typescript
import { JeanProvider, JeanChat, useJean } from '@jeanmemory/react';
const { sendMessage, storeDocument, tools } = useJean();
// ✅ Must work exactly as shown
```

## 🎉 OUTCOME

**Once completed:**
- ✅ All Mintlify documentation examples work exactly as written
- ✅ SDKs provide both documented API and backward compatibility  
- ✅ New developers can follow docs without any issues
- ✅ Testing suite validates documented behavior
- ✅ Published packages match repository source code

**The Mintlify docs are PERFECT** - we just need to make our SDKs match them!