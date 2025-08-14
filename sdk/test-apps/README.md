# Jean Memory SDK Test Apps

**Quick validation of all three SDKs before building production applications.**

## 🎯 Testing Strategy

Test each SDK to ensure:
1. **Initialization works** - API key validation, client setup
2. **Configuration options pass through** - `speed`, `tool`, `format` parameters 
3. **Authentication flow ready** - JWT token handling, user management
4. **MCP integration functional** - Backend communication patterns
5. **Error handling robust** - Graceful failures and clear error messages

## 🚀 Quick Start

### 1. Set Environment Variables
```bash
# Required for all tests
export JEAN_API_KEY="jean_sk_your_actual_api_key_here"

# Required for React test
export NEXT_PUBLIC_JEAN_API_KEY="jean_sk_your_actual_api_key_here"
```

### 2. Run Individual SDK Tests

**Python SDK Test:**
```bash
cd python-test
python3 test_jean_memory.py
```

**Node.js SDK Test:**
```bash
cd node-test
npm install
npm test
```

**React SDK Test:**
```bash
cd react-test
npm install
npm run dev
# Open http://localhost:3000
```

## 📋 Expected Test Results

### Without Real API Key
- ✅ Parameter validation passes
- ✅ Client initialization works
- ❌ Backend requests fail (expected)
- ✅ Error handling works correctly

### With Real API Key
- ✅ Full end-to-end functionality
- ✅ Authentication flow complete
- ✅ Context retrieval working
- ✅ Memory operations functional

## 🔧 What Each Test Validates

### Python Test (`python-test/test_jean_memory.py`)
- JeanClient initialization
- Configuration parameter passing
- JWT token parsing with fallback
- Direct tool access (add_memory, search_memory)
- MCP request structure validation

### Node.js Test (`node-test/test.js`)
- JeanClient initialization with configurable API base
- Next.js API route compatibility
- Edge runtime compatibility
- TypeScript type safety
- Configuration options passing

### React Test (`react-test/`)
- 5-line integration promise (`JeanProvider` + `JeanChat`)
- OAuth 2.1 PKCE authentication flow
- Real-time chat interface with memory
- Professional UI components
- Configuration options in chat interface

## 🎯 Success Criteria

**Ready for Production When:**
- [ ] All three SDK tests pass initialization
- [ ] Configuration options properly passed to backend
- [ ] Authentication flows work end-to-end
- [ ] UI components render correctly
- [ ] Error handling provides clear feedback
- [ ] Backend MCP endpoints responding correctly

## 📈 Next Phase: Build Applications

Once SDKs test successfully, immediately build these applications:

### Immediate Applications (Week 1)
1. **Personal Assistant App** - Full-stack Next.js with all three SDKs
2. **Memory-Enhanced Chatbot** - Pure React frontend with chat history
3. **Document Processor** - Python script that ingests and remembers documents
4. **API Middleware Service** - Node.js service that adds memory to any AI API

### Advanced Applications (Week 2-3)
1. **Team Knowledge Base** - Multi-user memory sharing
2. **Learning Companion** - Educational app that adapts to user progress
3. **Meeting Assistant** - Records, summarizes, and remembers meeting contexts
4. **Developer Tools Integration** - VS Code extension with code context memory

### Enterprise Applications (Week 3-4)
1. **Customer Support Dashboard** - Memory-enhanced support ticket system
2. **Sales Intelligence Platform** - CRM with conversation memory
3. **Content Management System** - CMS that remembers user preferences and history
4. **Analytics Dashboard** - Business intelligence with contextual insights

## 🐛 Troubleshooting

### Common Issues
- **Import errors**: Check SDK file paths in test files
- **Authentication failures**: Verify API key format and permissions
- **Network errors**: Ensure backend endpoints are accessible
- **UI rendering issues**: Verify Tailwind CSS and dependencies installed

### Debug Mode
Add `DEBUG=true` environment variable for verbose logging:
```bash
DEBUG=true python3 test_jean_memory.py
DEBUG=true npm test
DEBUG=true npm run dev
```

## 📞 Next Steps

1. **Run all tests** with your real Jean Memory API key
2. **Document any issues** found during testing
3. **Fix critical bugs** before application development
4. **Start building** the first production application
5. **Iterate rapidly** based on real usage feedback

The goal is to move from "SDKs work" to "applications shipping with Jean Memory" as quickly as possible.