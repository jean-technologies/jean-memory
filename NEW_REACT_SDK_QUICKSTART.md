# Jean Memory React SDK - Quickstart Guide

Get up and running with personalized AI chatbots in 5 minutes.

## 1. Installation

```bash
npm install jeanmemory-react
```

## 2. Get Your API Key

1. Visit [jeanmemory.com](https://jeanmemory.com) and subscribe to Pro
2. Generate your API key from the dashboard
3. Keep it secure - never commit it to version control

## 3. Basic Setup

Create a simple app with the Jean Memory SDK:

```tsx
import React from 'react';
import { useJeanAgent, SignInWithJean, JeanChat } from 'jeanmemory-react';

function App() {
  const { agent, signIn } = useJeanAgent({
    apiKey: "jean_sk_your_api_key_here",  // Required!
    systemPrompt: "You are a helpful assistant"
  });

  if (!agent) {
    return <SignInWithJean onSuccess={signIn} />;
  }
  
  return <JeanChat agent={agent} />;
}

export default App;
```

## 4. That's It!

Your app now has:
- ✅ User authentication 
- ✅ Persistent memory across conversations
- ✅ AI-powered responses with context
- ✅ Ready-to-use chat interface

## What Happens When Users Sign In?

1. User clicks "Sign in with Jean"
2. Browser prompts for email/password
3. Jean Memory authenticates and returns user data
4. Chat interface appears with full memory capabilities
5. All conversations are remembered across sessions

## Configuration Options

### Environment Variables (Recommended)

For security, store your API key in environment variables:

```bash
# .env
REACT_APP_JEAN_API_KEY=jean_sk_your_api_key_here
```

```tsx
const { agent, signIn } = useJeanAgent({
  apiKey: process.env.REACT_APP_JEAN_API_KEY!,
  systemPrompt: "You are a helpful assistant"
});
```

**Security Note:** API key is required for all requests. Never commit API keys to version control.

### Customize Authentication Button

```tsx
<SignInWithJean 
  onSuccess={signIn}
  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
/>
```

### Style the Chat Interface

```tsx
<JeanChat 
  agent={agent}
  className="border-2 border-gray-200 rounded-lg"
  style={{ height: '500px', backgroundColor: '#f9f9f9' }}
/>
```

## Environment Setup

For production apps, add your API key to environment variables:

```bash
# .env
REACT_APP_JEAN_API_KEY=jean_sk_your_api_key_here
```

```tsx
const { agent, signIn } = useJeanAgent({
  apiKey: process.env.REACT_APP_JEAN_API_KEY,
  systemPrompt: "You are a helpful assistant"
});
```

## Next.js Setup

For Next.js, disable SSR for Jean components:

```tsx
import dynamic from 'next/dynamic';

const JeanChat = dynamic(
  () => import('jeanmemory-react').then(mod => mod.JeanChat),
  { ssr: false }
);

const SignInWithJean = dynamic(
  () => import('jeanmemory-react').then(mod => mod.SignInWithJean), 
  { ssr: false }
);
```

## Testing Memory

To test that memory is working:

1. Sign in and tell the AI something: "My favorite color is blue"
2. Ask a different question: "What's the weather like?"
3. Later ask: "What's my favorite color?" 
4. The AI should remember "blue" from the earlier conversation

## Troubleshooting

**Authentication not working?**
- Check browser console for errors
- Ensure you're using HTTPS in production
- Verify API key if provided

**Chat not responding?**
- Check network tab for failed requests
- Verify user is properly authenticated
- Check browser console for JavaScript errors

## Get Help

- Documentation: Full examples and API reference in README.md
- Issues: Report problems on GitHub
- Questions: Contact support@jeanmemory.com

## What's Next?

- Customize the system prompt for your use case
- Style components to match your brand
- Integrate with your existing React application
- Explore advanced features in the full documentation