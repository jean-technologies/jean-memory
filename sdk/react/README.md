# Jean Memory React SDK

The official React library for Jean Memory - 5-line integration for personalized AI chatbots using MCP (Model Context Protocol).

## Installation

```bash
npm install @jeanmemory/react
```

## Quick Start (5 lines of code)

```jsx
import { JeanAgent } from '@jeanmemory/react';

function App() {
  return <JeanAgent 
    apiKey="your-jean-memory-api-key"
    systemPrompt="You are a helpful assistant"
  />;
}
```

That's it! This creates a complete personalized AI chatbot that:
- 🧠 **Remembers the user** via Jean Memory
- 💬 **Provides intelligent responses** using MCP jean_memory tool  
- 🎯 **Acts according to your system prompt** (math tutor, writing coach, etc.)
- 🔐 **Handles authentication** automatically

## Get Your API Key

Visit [jeanmemory.com](https://jeanmemory.com) to:
1. Create your Jean Memory account
2. Get your API key (starts with `jean_sk_`)
3. Start building personalized AI experiences

## Examples

### Math Tutor
```jsx
<JeanAgent 
  apiKey="your-api-key-here"
  systemPrompt="You are an expert math tutor who helps students with algebra, calculus, and statistics"
/>
```

### Writing Coach  
```jsx
<JeanAgent 
  apiKey="your-api-key-here"
  systemPrompt="You are an expert writing coach who helps improve clarity and engagement"
/>
```

## Advanced Usage

```jsx
import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function CustomApp() {
  const agent = useJeanAgent({
    apiKey: "your-api-key-here",
    systemPrompt: "You are a helpful assistant"
  });

  if (!agent.isAuthenticated) {
    return <SignInWithJean onSuccess={agent.signIn} />;
  }

  return <JeanChat agent={agent} />;
}
```

## Development Setup

For local development, add a proxy to your `package.json` to avoid CORS issues:

```json
{
  "name": "my-app",
  "scripts": { "..." },
  "proxy": "https://jean-memory-api-virginia.onrender.com"
}
```

## Features

- ✅ Professional assistant-UI styling
- ✅ MCP (Model Context Protocol) integration  
- ✅ Real-time personalized responses
- ✅ TypeScript support
- ✅ 5-line integration promise
- ✅ Cross-platform memory persistence

## Documentation

Full documentation: https://docs.jeanmemory.com

## License

MIT