# Jean Memory Node.js SDK

The official Node.js SDK for Jean Memory - Build personalized AI chatbots with persistent memory in your backend applications.

## Installation

```bash
npm install @jeanmemory/node
```

## Quick Start

```javascript
import { JeanAgent } from '@jeanmemory/node';

// Create agent
const agent = new JeanAgent({
  apiKey: process.env.JEAN_API_KEY,
  systemPrompt: 'You are a helpful assistant with memory.'
});

// For Next.js API routes
export const POST = agent.createHandler();

// For Express.js
app.post('/chat', agent.createHandler());
```

## Features

- 🧠 **Persistent Memory**: Conversations remember previous interactions
- 🚀 **Next.js Ready**: Built-in API route handlers
- 🔒 **Secure**: OAuth 2.1 authentication with JWT tokens
- ⚡ **Fast**: Optimized for serverless environments
- 🎯 **TypeScript**: Full type safety

## API Reference

### JeanAgent

```typescript
interface JeanAgentConfig {
  apiKey?: string;
  systemPrompt?: string;
  model?: string;
}

class JeanAgent {
  constructor(config: JeanAgentConfig)
  async process(message: string, userToken: string): Promise<Response>
  createHandler(): Function
}
```

### Example Usage

```javascript
import { JeanAgent } from '@jeanmemory/node';

const agent = new JeanAgent({
  apiKey: 'jean_sk_your_api_key',
  systemPrompt: 'You are a helpful tutor.',
  model: 'gpt-4o-mini'
});

// Next.js App Router
export async function POST(request) {
  const { message } = await request.json();
  const userToken = request.headers.get('authorization');
  
  return await agent.process(message, userToken);
}
```

## Links

- [Documentation](https://docs.jeanmemory.com)
- [GitHub](https://github.com/jean-technologies/jean-memory)
- [Website](https://jeanmemory.com)