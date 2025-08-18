# Jean Memory React SDK - API Reference

Complete reference for all components, hooks, and types.

## Installation

```bash
npm install jeanmemory-react
```

## Exports

```tsx
import { 
  useJeanAgent,      // Primary hook with authentication
  useJean,           // Low-level hook requiring user management
  SignInWithJean,    // Authentication component
  JeanChat,          // Chat interface component
  JeanUser,          // TypeScript type
  JeanAgent          // TypeScript type
} from 'jeanmemory-react';
```

## Hooks

### `useJeanAgent(config)`

**Primary hook for Jean Memory integration with built-in authentication.**

#### Parameters
- `config` (required): Configuration object
  - `apiKey` (string, required): Your Jean Memory API key. Get yours at https://jeanmemory.com
  - `systemPrompt` (string, optional): System prompt for the AI

#### Returns
Object with the following properties:
- `agent` (JeanAgent | null): Agent object for sending messages, null when not authenticated
- `user` (JeanUser | null): Current authenticated user object
- `isLoading` (boolean): Loading state indicator
- `error` (string | null): Error message if any operation failed
- `signIn` (function): Authenticate user via email/password prompts
- `signOut` (function): Sign out current user

#### Example
```tsx
const { agent, user, isLoading, error, signIn, signOut } = useJeanAgent({
  apiKey: "jean_sk_your_api_key",
  systemPrompt: "You are a helpful math tutor"
});
```

---

### `useJean({ user })`

**Low-level hook that requires manual user management.**

#### Parameters
- `user` (JeanUser | null): User object with authentication details

#### Returns
Object with the following properties:
- `agent` (JeanAgent | null): Agent object for sending messages
- `isLoading` (boolean): Loading state indicator  
- `error` (string | null): Error message if any operation failed

#### Example
```tsx
const [user, setUser] = useState<JeanUser | null>(null);
const { agent, isLoading, error } = useJean({ user });
```

## Components

### `<SignInWithJean />`

**Authentication button component.**

#### Props
- `onSuccess` (function, optional): Callback function called when authentication succeeds
  - Signature: `(user: JeanUser) => void`
- `apiKey` (string, optional): Your Jean Memory API key  
- `className` (string, optional): CSS classes to apply to the button

#### Example
```tsx
<SignInWithJean 
  onSuccess={(user) => console.log('Signed in:', user)}
  apiKey="jean_sk_your_api_key"
  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
/>
```

#### Notes
- Currently uses browser `prompt()` for email/password input
- OAuth UI component coming in future version
- Button displays 🧠 emoji with "Sign in with Jean" text
- Shows loading state while authenticating

---

### `<JeanChat />`

**Ready-to-use chat interface component.**

#### Props
- `agent` (JeanAgent, required): Agent object from useJeanAgent or useJean
- `className` (string, optional): CSS classes to apply to the container
- `style` (React.CSSProperties, optional): Inline styles for the container

#### Example
```tsx
<JeanChat 
  agent={agent}
  className="border-2 border-gray-200 rounded-lg p-4"
  style={{ height: '500px', backgroundColor: '#f9f9f9' }}
/>
```

#### Features
- Message history display
- Text input with Enter key support  
- Loading indicator during AI responses
- User and assistant message differentiation
- Scrollable message area
- Error handling for failed messages

#### Default Styling
- Height: 384px (h-96)
- Border: 1px solid
- Border radius: 8px
- Padding: 16px
- Flexbox layout with scrollable message area

## TypeScript Types

### `JeanUser`
```typescript
interface JeanUser {
  user_id: string;      // Unique user identifier
  email: string;        // User's email address
  access_token: string; // Authentication token
}
```

### `JeanAgent`  
```typescript
interface JeanAgent {
  user: JeanUser;
  sendMessage: (message: string) => Promise<string>;
}
```

### `JeanAgentConfig`
```typescript
interface JeanAgentConfig {
  apiKey: string;       // Required API key - get yours at jeanmemory.com
  systemPrompt?: string; // Optional system prompt
}
```

## Agent Methods

### `agent.sendMessage(message)`

Send a message to the AI and receive a response with full context.

#### Parameters
- `message` (string): The user's message to send

#### Returns
- `Promise<string>`: The AI's response

#### Example
```tsx
const response = await agent.sendMessage("What's the weather like?");
console.log(response); // AI response with context
```

#### Notes
- Automatically includes conversation history and user context
- Handles memory storage and retrieval behind the scenes
- Throws error if user is not authenticated
- Response time typically 1-3 seconds

## API Endpoints

The SDK communicates with these Jean Memory API endpoints:

- **Base URL**: `https://jean-memory-api-virginia.onrender.com`
- **Authentication**: `POST /sdk/auth/login`
- **Chat**: `POST /sdk/chat/enhance`

## Error Handling

All hooks and components include error handling:

```tsx
const { agent, error } = useJeanAgent();

if (error) {
  console.error('Jean Memory error:', error);
  // Handle error state in your UI
}
```

Common errors:
- `"User is not authenticated"` - Call signIn() first
- `"Failed to send message"` - Network or API error
- `"Authentication failed"` - Invalid credentials

## Environment Variables

Recommended environment variable setup:

```bash
# .env
REACT_APP_JEAN_API_KEY=jean_sk_your_api_key_here
```

```tsx
const { agent, signIn } = useJeanAgent({
  apiKey: process.env.REACT_APP_JEAN_API_KEY
});
```

## Next.js Compatibility

For Next.js applications, disable SSR:

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

## Performance Notes

- Components are lightweight with minimal re-renders
- Agent object is memoized to prevent unnecessary updates
- Message history is stored in local component state
- API calls are debounced automatically

## Browser Support

- Modern browsers with ES2018+ support
- Chrome 70+, Firefox 62+, Safari 12+, Edge 79+
- Requires JavaScript enabled
- Uses Fetch API (polyfill may be needed for older browsers)