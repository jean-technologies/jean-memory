# Jean Memory React SDK Test Application

This is a test application to validate the Jean Memory React SDK functionality, ensuring it matches the Python SDK feature parity.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run the development server:**
   ```bash
   npm run dev
   ```

3. **Open in browser:**
   - Go to http://localhost:3000
   - You'll see three demo applications

## 🧪 Test Scenarios

### 1. Math Tutor Demo
- **System Prompt**: "You are a patient math tutor who explains concepts step by step"  
- **Purpose**: Test basic 5-line integration from /api-docs page
- **Expected**: Bot acts as math tutor with personalized context

### 2. Therapist Demo  
- **System Prompt**: "You are a supportive therapist who provides empathetic guidance"
- **Purpose**: Match Python SDK example exactly
- **Expected**: Bot acts as therapist with user's personal memories

### 3. Custom Demo
- **System Prompt**: "You are a helpful AI assistant who knows the user's personal context"
- **Purpose**: Test custom styling and advanced features
- **Expected**: Personalized responses with custom UI

## 🔑 Authentication

Use any valid Jean Memory account credentials:
- The app uses the same API key as the working Python SDK
- Authentication endpoint: `/sdk/auth/login` 
- Chat endpoint: `/sdk/chat/enhance`

## ✅ Success Criteria

The React SDK should match Python SDK functionality:

1. **Authentication**: "Sign in with Jean" works end-to-end
2. **Context Retrieval**: Gets personalized user context (4681+ characters)  
3. **System Prompt**: Bot behavior changes based on system prompt
4. **Memory Persistence**: New conversations saved to user's memory vault
5. **Multi-tenant**: Each user sees only their own memories
6. **5-Line Integration**: Exact code from /api-docs page works

## 🐛 Testing Notes

- **Expected Behavior**: Should work exactly like Python SDK
- **API Endpoints**: Uses same backend as Python SDK  
- **Error Handling**: Should show clear error messages
- **Loading States**: Should show loading indicators during API calls

## 📋 Issues to Report

If something doesn't work, please provide:

1. **Screenshots** of any errors or unexpected behavior
2. **Browser console logs** (F12 → Console)
3. **Network requests** (F12 → Network tab)  
4. **Comparison** with Python SDK behavior

## 🔧 Architecture

```
test-react-app/
├── lib/jeanmemory.tsx    # React SDK implementation
├── pages/index.tsx       # Test demos 
├── styles/globals.css    # Tailwind CSS
└── package.json          # Dependencies
```

This test app validates that the React SDK delivers the same "Sign in with Google for AI memory" experience as the Python SDK.