# Jean Memory React SDK

**5-line integration for personalized AI chatbots**

Add universal memory to your React application with just a few lines of code. Your users get a personalized AI experience that remembers their conversations across all applications.

## Quick Start

```bash
npm install jeanmemory-react
```

```tsx
import { useState } from 'react';
import { useJean, SignInWithJean, JeanChat } from 'jeanmemory-react';

function MyApp() {
  const [user, setUser] = useState(null);
  const { agent } = useJean({ user });

  if (!agent) {
    return <SignInWithJean apiKey="your-api-key" onSuccess={setUser} />;
  }
  return <JeanChat agent={agent} />;
}
```

That's it! Your users can now sign in with their Jean Memory account and get personalized AI assistance.

## Features

- **🔐 Complete OAuth 2.1 PKCE Flow**: Secure authentication with auto-redirect handling
- **🧠 Universal Memory**: Conversations persist across all applications using Jean Memory
- **⚛️ React-First**: Built specifically for React with TypeScript support
- **🎨 Fully Customizable**: Style components to match your brand
- **📱 Production Ready**: Auto-detects redirect URIs, handles errors gracefully

## Components

### `SignInWithJean`

Beautiful, production-ready sign-in button with complete OAuth flow.

```tsx
<SignInWithJean
  apiKey="your-api-key"
  onSuccess={(user) => setUser(user)}
  onError={(error) => console.error(error)}
  className="custom-button"
  redirectUri="https://yourapp.com/callback" // Optional - auto-detected
>
  Custom Button Text
</SignInWithJean>
```

### `JeanChat`

Simple chat interface for interacting with the Jean Memory agent.

```tsx
<JeanChat 
  agent={agent}
  className="chat-container"
  style={{ height: '400px' }}
/>
```

### `useJean`

Core hook for managing Jean Memory state.

```tsx
const { agent, isLoading, error } = useJean({ user });
```

## Examples

### Math Tutor App
```tsx
function MathTutorApp() {
  const [user, setUser] = useState(null);
  const { agent } = useJean({ user });

  if (!agent) {
    return <SignInWithJean apiKey="your-api-key" onSuccess={setUser} />;
  }
  return <JeanChat agent={agent} />;
}
```

### Custom Styling
```tsx
function CustomApp() {
  const [user, setUser] = useState(null);
  const { agent } = useJean({ user });

  if (!agent) {
    return (
      <SignInWithJean 
        apiKey="your-api-key"
        onSuccess={setUser}
        className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg"
      >
        🚀 Get Started with AI Memory
      </SignInWithJean>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <h1>Personal AI Assistant</h1>
      <JeanChat 
        agent={agent} 
        className="border rounded-lg p-4 h-96"
      />
    </div>
  );
}
```

## API Reference

### Types

```tsx
interface JeanUser {
  user_id: string;
  email: string;
  access_token: string;
}

interface JeanAgent {
  user: JeanUser;
  sendMessage: (message: string) => Promise<string>;
}
```

### Configuration

- `apiKey`: Your Jean Memory API key (get one at [jean-memory.com](https://jean-memory.com))
- `redirectUri`: OAuth callback URL (auto-detected if not provided)
- `apiBase`: API base URL (defaults to production)

## Get API Key

Visit [jean-memory.com](https://jean-memory.com) to create an account and get your API key.

## Support

- Documentation: [docs.jean-memory.com](https://docs.jean-memory.com)
- Issues: [GitHub Issues](https://github.com/jean-technologies/jean-memory/issues)
- Email: support@jean-memory.com