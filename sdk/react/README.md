# Jean Memory React SDK

The official React library for Jean Memory - Complete chat interface with personalized AI using MCP (Model Context Protocol).

## Installation

```bash
npm install @jeanmemory/react
```

## Quick Start (5 lines of code)

```jsx
import { JeanProvider, JeanChat } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="your-jean-memory-api-key">
      <JeanChat />
    </JeanProvider>
  );
}
```

That's it! This creates a complete personalized AI chatbot that:
- 🧠 **Remembers the user** via Jean Memory
- 💬 **Provides intelligent responses** using MCP jean_memory tool  
- 🎯 **Beautiful chat interface** with authentication
- 🔐 **Handles OAuth authentication** automatically

## Get Your API Key

Visit [jeanmemory.com](https://jeanmemory.com) to:
1. Create your Jean Memory account
2. Get your API key (starts with `jean_sk_`)
3. Start building personalized AI experiences

## Authentication

The SDK supports both test and production authentication:

### Test Mode (Development)
```jsx
// Use a test API key for development:
<JeanProvider apiKey="jean_sk_test_demo_key_for_ui_testing">
  <JeanChat />
</JeanProvider>
// Automatically creates a test user - no OAuth required
```

### Production Mode (OAuth)
```jsx
// Use your production API key:
<JeanProvider apiKey="jean_sk_live_your_production_key">
  <JeanChat />
</JeanProvider>
// Shows "Sign In with Jean" button, handles complete OAuth flow
```

## Advanced Usage

### Custom Authentication UI
```jsx
import { JeanProvider, useJean, JeanChat } from '@jeanmemory/react';

function CustomApp() {
  const { isAuthenticated, signIn, signOut, user } = useJean();

  if (!isAuthenticated) {
    return (
      <div>
        <h1>Welcome to My App</h1>
        <button onClick={signIn}>Sign In with Jean</button>
      </div>
    );
  }

  return (
    <div>
      <header>
        <span>Welcome, {user?.name}</span>
        <button onClick={signOut}>Sign Out</button>
      </header>
      <JeanChat />
    </div>
  );
}

function App() {
  return (
    <JeanProvider apiKey="your-jean-memory-api-key">
      <CustomApp />
    </JeanProvider>
  );
}
```

### Standalone Sign In Component
```jsx
import { SignInWithJean } from '@jeanmemory/react';

function LoginPage() {
  return (
    <SignInWithJean 
      apiKey="your-jean-memory-api-key"
      onSuccess={(user) => {
        console.log('User authenticated:', user);
        // Handle successful authentication
      }}
      onError={(error) => {
        console.error('Authentication failed:', error);
        // Handle authentication error
      }}
    >
      Custom Sign In Button Text
    </SignInWithJean>
  );
}
```

### Direct Memory Tools
```jsx
import { JeanProvider, useJean } from '@jeanmemory/react';

function MemoryExample() {
  const { tools, isAuthenticated } = useJean();

  const handleAddMemory = async () => {
    if (isAuthenticated) {
      await tools.add_memory("User likes pizza");
    }
  };

  const handleSearchMemory = async () => {
    if (isAuthenticated) {
      const results = await tools.search_memory("food preferences");
      console.log('Memory results:', results);
    }
  };

  return (
    <div>
      <button onClick={handleAddMemory}>Add Memory</button>
      <button onClick={handleSearchMemory}>Search Memory</button>
    </div>
  );
}
```

## Components & Hooks

### Core Components
- **`JeanProvider`** - Authentication and state management provider
- **`JeanChat`** - Complete chat interface with authentication
- **`SignInWithJean`** - Standalone OAuth authentication button

### Hooks
- **`useJean()`** - Access authentication state and methods
- **`useJeanMCP()`** - Direct access to MCP tools and memory functions

### Types
- **`JeanUser`** - User object with authentication details
- **`JeanMessage`** - Chat message structure
- **`MessageOptions`** - Options for sending messages

## OAuth Configuration

The SDK automatically handles OAuth authentication with Jean Memory's secure backend. For development on localhost, the following ports are supported:
- `localhost:3000` (Create React App default)
- `localhost:3005` (Custom development)
- `localhost:5173` (Vite default)
- `localhost:8080` (Alternative development)

## Features

- ✅ Complete OAuth 2.1 PKCE authentication flow
- ✅ Beautiful professional chat interface
- ✅ Real-time personalized responses
- ✅ Cross-platform memory persistence
- ✅ TypeScript support
- ✅ Test mode for development
- ✅ Production-ready authentication
- ✅ MCP (Model Context Protocol) integration

## Development Setup

For local development, no additional configuration is needed. The SDK automatically detects test API keys and localhost environments.

## Documentation

Full documentation: https://docs.jeanmemory.com

## License

MIT