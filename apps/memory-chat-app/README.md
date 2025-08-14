# Memory Chat App

**Production-ready chat application with persistent memory powered by Jean Memory.**

This app demonstrates the complete Jean Memory stack:
- **React SDK** - Frontend authentication & chat interface
- **Node.js SDK** - Backend context retrieval 
- **OpenAI Integration** - LLM responses with memory context

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set environment variables:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your API keys
   ```

3. **Run the app:**
   ```bash
   npm run dev
   ```

4. **Open http://localhost:3000**

## 🔑 Required API Keys

### Jean Memory API Key
Get your API key from [Jean Memory Dashboard](https://dashboard.jean-memory.com)
```
JEAN_API_KEY=jean_sk_your_key_here
NEXT_PUBLIC_JEAN_API_KEY=jean_sk_your_key_here
```

### OpenAI API Key
Get your API key from [OpenAI Platform](https://platform.openai.com)
```
OPENAI_API_KEY=sk-your_openai_key_here
```

## 🏗️ Architecture

### Frontend (React SDK)
- `JeanProvider` - Manages authentication state
- `JeanChat` - Complete chat interface with OAuth
- Automatic OAuth 2.1 PKCE authentication flow
- Professional UI with dark mode support

### Backend (Node.js SDK + API Route)
- `pages/api/chat.ts` - Next.js API route
- Jean Memory context retrieval
- OpenAI integration with enhanced prompts
- Comprehensive error handling

### Flow
1. User signs in with Jean Memory OAuth
2. User sends message in chat interface  
3. Frontend calls `/api/chat` with user token
4. Backend gets personalized context from Jean Memory
5. Backend calls OpenAI with context-enhanced prompt
6. Response sent back with memory-aware answer

## 💡 Key Features

### Memory-Enhanced Conversations
- Every conversation is remembered across sessions
- Context from previous chats automatically included
- Personal details and preferences retained
- Conversations build on each other naturally

### Professional UI/UX
- Clean, modern interface suitable for enterprise
- Dark mode support with system preference detection
- Responsive design works on mobile and desktop
- Professional loading states and error handling

### Production Ready
- Comprehensive error handling with user-friendly messages
- Edge runtime compatible for fast serverless deployment
- TypeScript throughout for type safety
- Optimized bundle size and performance

## 🔧 Customization

### Chat Interface
Customize the `JeanChat` component:
```tsx
<JeanChat 
  className="custom-styles"
  showHeader={true}
  placeholder="Ask me anything..."
/>
```

### Memory Configuration
Adjust memory retrieval in `pages/api/chat.ts`:
```typescript
const contextResponse = await jean.getContext({
  user_token: userToken,
  message: currentMessage,
  speed: 'comprehensive',    // More thorough memory search
  tool: 'search_memory',     // Direct memory search
  format: 'enhanced'         // Detailed context metadata
})
```

### LLM Settings
Modify OpenAI configuration:
```typescript
const completion = await openai.chat.completions.create({
  model: 'gpt-4-turbo-preview',
  max_tokens: 2000,           // Longer responses
  temperature: 0.9,           // More creative
  stream: true                // Streaming responses
})
```

## 📊 Testing & Development

### Local Development
```bash
npm run dev          # Start development server
npm run build        # Build for production  
npm run start        # Start production server
npm run lint         # Check code quality
```

### Environment Testing
Test with different configurations:
- Development: Full error logging and debugging
- Production: Optimized performance and error handling
- Demo Mode: Works without real API keys for testing

## 🚀 Deployment

### Vercel (Recommended)
```bash
vercel deploy
```

### Docker
```bash
docker build -t memory-chat-app .
docker run -p 3000:3000 memory-chat-app
```

### Environment Variables for Production
Ensure these are set in your deployment platform:
- `JEAN_API_KEY`
- `NEXT_PUBLIC_JEAN_API_KEY` 
- `OPENAI_API_KEY`

## 📈 Next Steps

### Immediate Improvements
1. **Streaming Responses** - Real-time message streaming
2. **Message History** - Persistent chat history in UI
3. **File Upload** - Document upload and memory storage
4. **Integration Connect** - Notion, Slack, Google Drive connections

### Advanced Features  
1. **Voice Chat** - Speech-to-text and text-to-speech
2. **Multi-user** - Team conversations with shared memory
3. **Analytics** - Usage tracking and insights
4. **Custom Models** - Support for different LLMs

This app serves as the foundation for any memory-enhanced AI application. The architecture scales from personal assistants to enterprise knowledge systems.