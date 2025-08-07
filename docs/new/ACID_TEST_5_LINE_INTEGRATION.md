# 🧪 ACID TEST: 5-Line "Sign in with Jean Memory" Integration

**Mission:** Build a working AI app with persistent memory in 5 minutes using only our public API docs.

**Success Criteria:** If this doesn't work perfectly, our "5-line integration" claim is false and we're not ready for launch.

---

## Test Instructions for External Developer

**Context:** You've been given this document and told that Jean Memory offers the world's first "Sign in with Memory" for AI apps. Your job is to build a simple AI chat app that remembers conversations across sessions using only the public API docs.

### Step 1: Create New React App (2 minutes)

```bash
npx create-next-app@latest my-jean-app --typescript --tailwind --eslint --app
cd my-jean-app
```

### Step 2: Install Jean Memory SDK (30 seconds)

```bash
npm install @jeanmemory/react
```

**❌ BLOCKER:** If this fails, the SDK isn't published to NPM yet.

### Step 3: Get API Key (1 minute)

1. Go to https://jean-memory.com  
2. Sign up / Sign in
3. Get your API key from dashboard

**❌ BLOCKER:** If the website doesn't have clear API key generation, this fails.

### Step 4: The 5-Line Integration (1 minute)

Replace `app/page.tsx` with:

```tsx
'use client';
import { useState } from 'react';
import { useJean, SignInWithJean, JeanChat } from '@jeanmemory/react';

export default function App() {
  const [user, setUser] = useState(null);
  const { agent } = useJean({ user });
  
  if (!agent) return <SignInWithJean apiKey="your-api-key-here" onSuccess={setUser} />;
  return <JeanChat agent={agent} />;
}
```

**❌ BLOCKER:** If TypeScript errors, imports fail, or components don't exist, this fails.

### Step 5: Test the Flow (1 minute)

```bash
npm run dev
# Visit http://localhost:3000
```

**Expected Flow:**
1. ✅ See "Sign in with Jean Memory" button
2. ✅ Click button → redirects to Jean Memory OAuth
3. ✅ Sign in → redirects back to app  
4. ✅ See chat interface
5. ✅ Type "Remember my name is Alex" → gets response
6. ✅ Refresh page → still signed in
7. ✅ Type "What's my name?" → responds "Alex"

**❌ CRITICAL BLOCKERS:**
- Button doesn't appear
- OAuth redirect fails  
- OAuth callback fails
- Chat doesn't work
- Memory doesn't persist
- Any error in browser console

---

## Internal Test Results Checklist

Run this test internally and check every item:

### ⬜ NPM Package Status
- [ ] `npm install @jeanmemory/react` works
- [ ] All exports are available: `useJean`, `SignInWithJean`, `JeanChat`
- [ ] TypeScript definitions work correctly

### ⬜ API Key & Client Registration  
- [ ] API key can be obtained from jean-memory.com
- [ ] API key works without additional OAuth client registration
- [ ] Clear instructions for developers to get API key

### ⬜ OAuth Flow
- [ ] `SignInWithJean` button renders correctly
- [ ] Button click initiates OAuth flow
- [ ] OAuth authorize endpoint `/sdk/oauth/authorize` responds
- [ ] User can sign in on OAuth page
- [ ] Callback redirects work with `http://localhost:3000/callback`
- [ ] Token exchange endpoint `/sdk/oauth/token` works
- [ ] User info endpoint `/sdk/oauth/userinfo` works
- [ ] User object is returned to `onSuccess` callback

### ⬜ Chat & Memory
- [ ] `JeanChat` component renders when authenticated
- [ ] Can send messages to Jean Memory agent
- [ ] Agent responds with memory-aware answers
- [ ] Memory persists across browser refreshes
- [ ] Memory works across different conversations

### ⬜ Developer Experience
- [ ] No confusing error messages
- [ ] TypeScript intellisense works
- [ ] Components are styled/look professional
- [ ] Loading states work correctly
- [ ] Error handling is graceful

### ⬜ Documentation
- [ ] API docs clearly show this 5-line example
- [ ] Clear API key instructions
- [ ] Troubleshooting section exists
- [ ] No missing information

---

## Blockers Found (Fill This Out)

### 🔴 Critical Issues:
- [ ] NPM package not published
- [ ] OAuth client registration required
- [ ] API endpoints not working
- [ ] Components not working
- [ ] Memory not persisting

### 🟡 Polish Issues:
- [ ] Confusing error messages
- [ ] Poor styling
- [ ] Missing loading states
- [ ] Documentation gaps

### 🟢 Status:
- [ ] ✅ **READY FOR LAUNCH** - Everything works perfectly
- [ ] ❌ **NOT READY** - Critical blockers exist

---

## Fix-It List

If this test fails, here's what needs immediate attention:

1. **Publish NPM Package** - `cd sdk/react && npm publish`
2. **Fix OAuth Client Registration** - Auto-register API keys as OAuth clients
3. **Fix API Endpoints** - Ensure all `/sdk/oauth/*` endpoints work
4. **Fix Component Issues** - Test all React components work correctly
5. **Fix Memory Issues** - Ensure persistence works end-to-end
6. **Update Documentation** - Make API docs crystal clear

---

**Bottom Line:** If an external developer can't follow this guide and build a working AI app with persistent memory in 5 minutes, we're not ready for the "first universal memory layer" claim.**

**Test this ruthlessly. No excuses. Fix everything until it's perfect.**