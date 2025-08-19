# Jean Memory React SDK Implementation Guide

**The fastest way to add personalized AI memory to any React application in 5 lines of code.**

---

## 🎯 What You're Building

A React application with:
- ✅ **Secure OAuth 2.1 authentication** (Google sign-in)
- ✅ **Persistent user sessions** (survives browser refreshes)
- ✅ **Personalized AI chat** that remembers user context
- ✅ **Universal identity** across all Jean Memory apps
- ✅ **Zero authentication complexity** for developers

## 🚀 Quick Start (5 Minutes)

### Step 1: Create Your React App

```bash
npx create-react-app jean-memory-demo
cd jean-memory-demo
npm install @jeanmemory/react
```

### Step 2: Get Your API Key

1. Visit [Jean Memory Dashboard](https://jeanmemory.com/dashboard)
2. Sign up/login with Google
3. Create a new app and copy your API key (`jean_sk_...`)

### Step 3: Add Jean Memory (5 Lines of Code)

Replace your `src/App.js` with:

```jsx
import React from 'react';
import { JeanProvider, SignInWithJean, useJean } from '@jeanmemory/react';
import './App.css';

// Replace with your actual API key
const JEAN_API_KEY = "jean_sk_your_api_key_here";

function App() {
  return (
    <div className="App">
      <JeanProvider apiKey={JEAN_API_KEY}>
        <AuthenticatedApp />
      </JeanProvider>
    </div>
  );
}

function AuthenticatedApp() {
  const { sendMessage, isAuthenticated, user, messages, isLoading } = useJean();
  const [input, setInput] = React.useState('');

  // If not authenticated, show sign-in
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h1>🧠 Jean Memory Demo</h1>
        <p>Sign in to access your personalized AI that remembers everything</p>
        <SignInWithJean 
          onSuccess={(user) => console.log('✅ Signed in:', user.email)}
          onError={(error) => console.error('❌ Auth error:', error)}
        >
          Sign In with Jean
        </SignInWithJean>
      </div>
    );
  }

  // Authenticated user interface
  const handleSend = async () => {
    if (!input.trim()) return;
    
    try {
      await sendMessage(input);
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <header style={{ marginBottom: '20px', textAlign: 'center' }}>
        <h1>🧠 Jean Memory AI Chat</h1>
        <p>Welcome back, <strong>{user.name || user.email}</strong>!</p>
        <p style={{ color: '#666' }}>Ask me anything - I remember our conversations and your context</p>
      </header>

      {/* Chat History */}
      <div style={{ 
        height: '400px', 
        border: '1px solid #ddd', 
        borderRadius: '8px', 
        padding: '16px', 
        marginBottom: '16px',
        overflowY: 'auto',
        backgroundColor: '#f9f9f9'
      }}>
        {messages.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', marginTop: '50px' }}>
            Start a conversation! Try asking: "What did I work on recently?" or "Remember that I like coffee"
          </p>
        ) : (
          messages.map((message, index) => (
            <div key={index} style={{ 
              marginBottom: '12px',
              padding: '8px 12px',
              borderRadius: '6px',
              backgroundColor: message.role === 'user' ? '#007bff' : '#fff',
              color: message.role === 'user' ? 'white' : 'black',
              marginLeft: message.role === 'user' ? '20%' : '0',
              marginRight: message.role === 'user' ? '0' : '20%'
            }}>
              <strong>{message.role === 'user' ? 'You' : 'Jean'}:</strong> {message.content}
            </div>
          ))
        )}
        {isLoading && (
          <div style={{ textAlign: 'center', color: '#666' }}>
            <em>Jean is thinking...</em>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask Jean anything..."
          style={{
            flex: 1,
            padding: '12px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '16px'
          }}
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          style={{
            padding: '12px 24px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Send
        </button>
      </div>

      {/* Demo Actions */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <h3>Try These Examples:</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {[
            "What did I work on recently?",
            "Remember that I prefer TypeScript",
            "What are my current projects?",
            "Help me plan my week"
          ].map(example => (
            <button
              key={example}
              onClick={() => setInput(example)}
              style={{
                padding: '8px 16px',
                backgroundColor: '#f8f9fa',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
```

### Step 4: Run Your App

```bash
npm start
```

🎉 **That's it!** You now have a fully functional AI chat with:
- Secure OAuth authentication
- Persistent user sessions
- Personalized AI that remembers context
- Universal identity across all Jean Memory apps

---

## 🔧 What Happens Under the Hood

### When a user clicks "Sign In with Jean":

1. **OAuth 2.1 PKCE Flow Initiates**
   - Secure PKCE parameters generated
   - User redirected to Google OAuth
   - No client secrets exposed to browser

2. **Authentication Completes**
   - User approves Google OAuth
   - JWT token generated with user ID
   - Universal identity mapped across all apps

3. **Session Established**
   - JWT stored securely in localStorage
   - Session persists across browser refreshes
   - Automatic token validation on app load

4. **AI Chat Ready**
   - All messages automatically include user context
   - Memories and preferences retrieved automatically
   - Personalized responses based on user history

### Security Features:

- ✅ **OAuth 2.1 PKCE** - Industry standard for public clients
- ✅ **JWT-in-header** - Prevents user impersonation attacks  
- ✅ **Universal identity** - Same user across all Jean Memory apps
- ✅ **Session persistence** - Robust localStorage + sessionStorage
- ✅ **Automatic cleanup** - Handles expired tokens gracefully

---

## 📚 Advanced Usage

### Custom Authentication UI

```jsx
import { useJean, signOutFromJean } from '@jeanmemory/react';

function CustomAuth() {
  const { isAuthenticated, user } = useJean();

  if (isAuthenticated) {
    return (
      <div>
        <span>Welcome, {user.name}!</span>
        <button onClick={signOutFromJean}>Sign Out</button>
      </div>
    );
  }

  return (
    <SignInWithJean
      className="custom-signin-button"
      onSuccess={(user) => console.log('Signed in:', user)}
    >
      <span>🔐 Custom Sign In Button</span>
    </SignInWithJean>
  );
}
```

### Memory Management

```jsx
function MemoryManager() {
  const { addMemory, searchMemory } = useJean();

  const saveMemory = async () => {
    await addMemory("I prefer React over Vue for frontend development");
  };

  const findMemories = async () => {
    const results = await searchMemory("frontend preferences");
    console.log(results);
  };

  return (
    <div>
      <button onClick={saveMemory}>Save Preference</button>
      <button onClick={findMemories}>Search Memories</button>
    </div>
  );
}
```

### Error Handling

```jsx
function App() {
  const [authError, setAuthError] = React.useState(null);

  return (
    <JeanProvider apiKey={JEAN_API_KEY}>
      {authError && (
        <div style={{ color: 'red', padding: '10px' }}>
          Authentication Error: {authError.message}
        </div>
      )}
      <SignInWithJean
        onSuccess={(user) => {
          setAuthError(null);
          console.log('Success:', user);
        }}
        onError={(error) => {
          setAuthError(error);
          console.error('Auth failed:', error);
        }}
      />
    </JeanProvider>
  );
}
```

---

## 🚀 Deployment

### Environment Variables

Create a `.env` file:

```bash
REACT_APP_JEAN_API_KEY=jean_sk_your_production_key
```

Update your code:

```jsx
const JEAN_API_KEY = process.env.REACT_APP_JEAN_API_KEY;
```

### Production Checklist

- ✅ Use production API key (not test key)
- ✅ Set proper CORS origins in Jean Memory dashboard
- ✅ Enable HTTPS for OAuth redirects
- ✅ Test authentication flow in production environment
- ✅ Monitor authentication success rates

---

## 🔍 Troubleshooting

### Common Issues

**1. "API key not found" error**
```jsx
// ❌ Wrong
<JeanProvider apiKey="">

// ✅ Correct  
<JeanProvider apiKey="jean_sk_your_actual_key">
```

**2. Authentication not persisting**
```jsx
// Make sure JeanProvider wraps your entire app
function App() {
  return (
    <JeanProvider apiKey={JEAN_API_KEY}>
      {/* All components that use authentication */}
    </JeanProvider>
  );
}
```

**3. CORS errors in production**
- Add your production domain to allowed origins in Jean Memory dashboard
- Ensure HTTPS is enabled for OAuth redirects

**4. "Invalid redirect URI" error**
- Check that your domain is registered in Jean Memory dashboard
- Verify HTTPS is properly configured

### Debug Authentication

```jsx
import { getUserSession, isAuthenticated } from '@jeanmemory/react';

function DebugAuth() {
  const session = getUserSession();
  const authenticated = isAuthenticated();
  
  return (
    <pre>
      {JSON.stringify({
        authenticated,
        session,
        timestamp: new Date().toISOString()
      }, null, 2)}
    </pre>
  );
}
```

---

## 📖 API Reference

### `JeanProvider`

```tsx
<JeanProvider 
  apiKey: string              // Required: Your Jean Memory API key
  children: ReactNode         // Your app components
/>
```

### `SignInWithJean`

```tsx
<SignInWithJean
  onSuccess?: (user) => void  // Called when authentication succeeds
  onError?: (error) => void   // Called when authentication fails  
  className?: string          // Custom CSS class
  children?: ReactNode        // Custom button content
  redirectUri?: string        // Custom OAuth redirect (optional)
/>
```

### `useJean` Hook

```tsx
const {
  // Authentication
  isAuthenticated: boolean,
  user: JeanUser | null,
  
  // Messaging
  messages: JeanMessage[],
  sendMessage: (message: string) => Promise<string>,
  clearConversation: () => void,
  
  // Memory Management
  addMemory: (content: string) => Promise<any>,
  searchMemory: (query: string) => Promise<any>,
  
  // State
  isLoading: boolean,
  error: string | null,
  
  // Internal (for custom auth UI)
  setUser: (user: JeanUser) => void
} = useJean();
```

### Utility Functions

```tsx
import { 
  signOutFromJean,     // Clear all session data
  getUserSession,      // Get current user session
  isAuthenticated,     // Check if user is authenticated
  clearUserSession     // Manually clear session
} from '@jeanmemory/react';
```

---

## 🌟 Example Use Cases

### 1. Customer Support Chat
```jsx
// Add personalized support that remembers customer history
function SupportChat() {
  const { sendMessage, isAuthenticated } = useJean();
  
  const askSupport = async (question) => {
    const response = await sendMessage(
      `Support question: ${question}. Please use my order history and preferences.`
    );
    return response;
  };
  
  // ... rest of component
}
```

### 2. E-commerce Recommendations
```jsx
// AI that remembers shopping preferences
function ProductRecommendations() {
  const { sendMessage } = useJean();
  
  const getRecommendations = async () => {
    return await sendMessage(
      "Based on my shopping history and preferences, what products would you recommend?"
    );
  };
  
  // ... rest of component
}
```

### 3. Learning Assistant
```jsx
// AI tutor that tracks learning progress
function LearningAssistant() {
  const { sendMessage, addMemory } = useJean();
  
  const trackProgress = async (topic, level) => {
    await addMemory(`Completed ${topic} at ${level} level`);
    return await sendMessage("What should I learn next based on my progress?");
  };
  
  // ... rest of component
}
```

---

## 🎯 Success Metrics

After implementing Jean Memory, you should see:

- ✅ **Sub-5 minute integration time**
- ✅ **Zero authentication setup complexity**  
- ✅ **Persistent user sessions across browser restarts**
- ✅ **Personalized AI responses based on user context**
- ✅ **Universal user identity across applications**
- ✅ **Production-ready security (OAuth 2.1 PKCE)**

---

## 📞 Support

- **Documentation**: [docs.jeanmemory.com](https://docs.jeanmemory.com)
- **GitHub Issues**: [Report bugs or request features](https://github.com/jean-technologies/jean-memory/issues)
- **Discord Community**: [Join our developer community](https://discord.gg/jeanmemory)
- **Email Support**: support@jeanmemory.com

---

## 🏆 You're Done!

Congratulations! You've successfully implemented personalized AI memory in your React application. Your users now have:

- 🔐 **Secure OAuth authentication** that "just works"
- 🧠 **AI that remembers** their preferences and context
- 🔄 **Persistent sessions** across all their devices
- 🌐 **Universal identity** across all Jean Memory applications

**The future of AI is personal, and it starts with memory.** 🚀