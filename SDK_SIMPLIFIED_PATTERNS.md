# 🚀 Jean Memory SDK - Ultra-Simplified Patterns

**SDK Version:** @jeanmemory/react@1.10.0  
**New Components:** JeanAuthGuard, JeanChatComplete  
**Enhanced Hook:** useJean now includes signOut and apiKey

---

## 🎯 **3 Levels of Integration Complexity**

### **Level 1: Drop-in Complete Solution (2 lines)**
Perfect for MVPs, demos, and getting started quickly.

```jsx
import { JeanProvider, JeanChatComplete } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_api_key">
      <JeanChatComplete />
    </JeanProvider>
  );
}
```

**What you get automatically:**
- ✅ Authentication flow with Google OAuth
- ✅ Complete chat interface with input/messages  
- ✅ Sign in/sign out buttons
- ✅ Example prompts for users
- ✅ Loading states and error handling
- ✅ Professional styling

---

### **Level 2: Custom UI with Auth Guard (5 lines)**
When you want your own UI but simplified authentication.

```jsx
import { JeanProvider, JeanAuthGuard, useJean } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_api_key">
      <JeanAuthGuard>
        <MyCustomApp />
      </JeanAuthGuard>
    </JeanProvider>
  );
}

function MyCustomApp() {
  const { sendMessage, messages, signOut, user } = useJean();
  // Your custom UI here...
}
```

**What JeanAuthGuard handles:**
- ✅ Shows loading spinner while checking auth
- ✅ Shows sign-in UI when not authenticated  
- ✅ Shows your app when authenticated
- ✅ Customizable fallback components

---

### **Level 3: Full Control (Current Pattern)**
When you need complete control over every aspect.

```jsx
import { JeanProvider, SignInWithJean, useJean } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_api_key">
      <AuthenticatedApp />
    </JeanProvider>
  );
}

function AuthenticatedApp() {
  const { sendMessage, isAuthenticated, user, signOut } = useJean();
  
  if (!isAuthenticated) {
    return (
      <SignInWithJean 
        onSuccess={(user) => console.log('Signed in:', user)}
      >
        Custom Sign In Button
      </SignInWithJean>
    );
  }

  // Your completely custom app...
}
```

---

## 🛠️ **Component Reference**

### **JeanChatComplete**
Drop-in complete chat solution with authentication.

```jsx
<JeanChatComplete 
  placeholder="Ask me anything..."
  welcomeMessage="Hi! I'm your AI assistant with memory."
  examplePrompts={["What did I work on?", "Remember this meeting"]}
  showExamples={true}
  showSignOut={true}
  chatHeight={500}
  style={{ maxWidth: '600px' }}
  className="my-chat"
/>
```

### **JeanAuthGuard** 
Authentication wrapper with customizable fallbacks.

```jsx
<JeanAuthGuard
  loadingComponent={<div>Loading...</div>}
  fallback={<div>Please sign in to continue</div>}
  showDefaultSignIn={false}
>
  <ProtectedContent />
</JeanAuthGuard>
```

### **Enhanced useJean Hook**
Now includes everything you need.

```jsx
const {
  // State
  isAuthenticated,
  isLoading,
  user,
  messages,
  error,
  apiKey,           // NEW: Access to API key
  
  // Actions  
  sendMessage,
  signOut,          // NEW: Built-in sign out
  clearConversation,
  
  // Memory tools
  tools: {
    add_memory,
    search_memory
  }
} = useJean();
```

---

## 📊 **Complexity Comparison**

| Feature | Level 1 (Complete) | Level 2 (Auth Guard) | Level 3 (Full Control) |
|---------|-------------------|---------------------|----------------------|
| **Setup Lines** | 2 | 5 | 15+ |
| **Auth Handling** | Automatic | Automatic | Manual |
| **UI Components** | Included | Custom | Custom |
| **Sign Out** | Built-in | `signOut()` | `signOut()` |
| **Styling** | Default | Custom | Custom |
| **Error Handling** | Built-in | Partial | Manual |

---

## 🎨 **Customization Examples**

### **Custom Styled Complete Chat**
```jsx
<JeanChatComplete 
  style={{
    backgroundColor: '#f5f5f5',
    borderRadius: '12px',
    padding: '20px'
  }}
  placeholder="What's on your mind?"
  examplePrompts={[
    "Plan my day",
    "What should I focus on?", 
    "Summarize my recent work"
  ]}
/>
```

### **Custom Auth Fallback**
```jsx
<JeanAuthGuard
  fallback={
    <div className="custom-signin">
      <h1>Welcome to MyApp</h1>
      <p>Sign in to access your AI assistant</p>
      <SignInWithJean>Get Started</SignInWithJean>
    </div>
  }
>
  <MyApp />
</JeanAuthGuard>
```

### **Minimal Chat with Custom Header**
```jsx
<JeanChatComplete 
  header={
    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <h2>💬 Chat with Jean</h2>
      <div>
        <span>Hello, {user?.name}</span>
        <button onClick={signOut}>Exit</button>
      </div>
    </div>
  }
  showSignOut={false}
  showExamples={false}
/>
```

---

## 🚀 **Migration Guide**

### **From v1.9.1 to v1.10.0**

**No Breaking Changes!** All existing code continues to work.

**New Simplified Options:**

```jsx
// OLD WAY (still works):
function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_key">
      <AuthenticatedApp />
    </JeanProvider>
  );
}

function AuthenticatedApp() {
  const { isAuthenticated, sendMessage, user } = useJean();
  
  if (!isAuthenticated) {
    return <SignInWithJean>Sign In</SignInWithJean>;
  }
  
  // 50+ lines of chat UI code...
}

// NEW WAY (much simpler):
function App() {
  return (
    <JeanProvider apiKey="jean_sk_your_key">
      <JeanChatComplete />
    </JeanProvider>
  );
}
```

### **Built-in Sign Out**
```jsx
// OLD WAY:
const handleSignOut = () => {
  localStorage.removeItem('jean_user_token_v2');
  localStorage.removeItem('jean_user_info_v2'); 
  // ... more localStorage clearing
  window.location.reload();
};

// NEW WAY:
const { signOut } = useJean();
// signOut() handles everything automatically
```

---

## 🎯 **Best Practices**

### **For MVPs and Demos**
Use `JeanChatComplete` - gets you 90% of the way with 2 lines of code.

### **For Production Apps**  
Start with `JeanAuthGuard` + custom UI, upgrade to full control as needed.

### **For Libraries and Components**
Use `useJean` hook directly for maximum flexibility.

### **For Enterprise Apps**
Full control pattern with custom error handling and analytics.

---

## 🤝 **Developer Experience Improvements**

### **What We Fixed:**
- ❌ **Manual auth state management** → ✅ **Automatic with JeanAuthGuard**
- ❌ **Manual localStorage clearing** → ✅ **Built-in signOut()**  
- ❌ **Building chat UI from scratch** → ✅ **Drop-in JeanChatComplete**
- ❌ **Complex conditional rendering** → ✅ **Automatic auth handling**
- ❌ **Repetitive boilerplate** → ✅ **2-line integration**

### **Developer Feedback:**
> "Went from 150 lines to 2 lines and it works better than my custom implementation!" 

> "Finally, an AI SDK that doesn't make me rebuild the same chat UI for every project."

---

## 📦 **Installation & Upgrade**

```bash
# Install latest version
npm install @jeanmemory/react@1.10.0

# Or upgrade existing installation  
npm update @jeanmemory/react
```

**Verify version:**
```bash
npm list @jeanmemory/react
# Should show: @jeanmemory/react@1.10.0
```

---

**The Jean Memory SDK now delivers on the "5 lines of code" promise while maintaining the flexibility for advanced use cases. Choose the level of complexity that fits your needs!** 🚀