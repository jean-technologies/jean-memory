# SDK Design Validation & "Under the Hood" Deep Dive

This document provides a detailed walkthrough of our proposed SDKs. Its purpose is to validate that our simple, elegant code snippets are grounded in a feasible technical architecture and to explain the layers of abstraction involved.

---

## 1. The React SDK: The All-in-One UI

### The Simple Code (The "5-Minute Install")

```tsx
import { JeanProvider, JeanChat } from '@jeanmemory/react';

function MyPage() {
  return (
    <JeanProvider apiKey="YOUR_API_KEY">
      <JeanChat />
    </JeanProvider>
  );
}
```

### For a Non-Technical Person: What Does This Do?

This code adds a complete, intelligent chatbot to a website. The `JeanProvider` is like plugging the website into the "Jean Memory brain." The `JeanChat` component is the actual chat window that users see and interact with. Together, they create a chat experience that remembers past conversations and automatically handles user login.

### What's Happening Under the Hood (For a Technical Person)

To make this snippet work, we are creating three key abstractions:

1.  **`<JeanProvider>`:** This is a React Context Provider.
    *   **State Management:** It holds all the critical state: the user's authentication status, the list of chat messages, the API key, etc.
    *   **Authentication Logic:** When it first loads, it checks for a `userToken` in a secure cookie. If none exists, it sets the `isAuthenticated` state to `false`.
    *   **API Client:** It likely initializes a lightweight API client instance that will be used by all child components to communicate with the Jean Memory backend.

2.  **`<JeanChat>`:** This is a "batteries-included" presentational component. It is a consumer of the context provided by `<JeanProvider>`.
    *   **Conditional Rendering:** It internally checks the `isAuthenticated` state.
        *   If `false`, it renders a `<SignInWithJean />` button.
        *   If `true`, it renders the chat interface (the message list and the input form).
    *   **UI Logic:** It maps over the `messages` array from the context to display the conversation. It handles the user typing into the input box and the form submission. When the form is submitted, it calls the `sendMessage` function from our hook.

3.  **`useJean()` (The Hook That `<JeanChat>` Uses Internally):** This is the core functional abstraction.
    *   **`sendMessage(messageText)`:** This function does the heavy lifting. It reads the `userToken` from the context state and makes a `POST` request to our backend API (e.g., `https://api.jeanmemory.com/api/v1/sdk/mcp/chat`). The request includes the message text and the user token in an `Authorization: Bearer <token>` header. It then handles the streaming response from the server, updating the `messages` array in the state as new data arrives.
    *   **`SignInWithJean` Logic:** The sign-in button, when clicked, doesn't handle the login itself. It simply redirects the browser to our secure OAuth 2.1 endpoint (e.g., `https://api.jeanmemory.com/sdk/oauth/authorize?...`). The real work happens when the user is redirected back to a special callback page. That page exchanges the authorization code for a `userToken`, securely sets it in a cookie, and then redirects the user back to the application. The `JeanProvider` then detects the new cookie and updates the state, causing the `<JeanChat>` component to re-render and show the chat interface.

**Verdict:** The design is simple, elegant, and **entirely feasible**. It follows standard patterns in modern web development and provides a powerful, yet simple, developer experience by abstracting away the complexities of state management and OAuth.

---

## 2. The Headless SDKs (Python/Node.js)

### The Simple Code (The "Core Product")

```python
from jeanmemory import JeanClient
from openai import OpenAI

# Initialize clients
jean = JeanClient(api_key="YOUR_JEAN_API_KEY")
openai = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# Get context from Jean Memory
context = jean.get_context(
    user_token="USER_TOKEN_FROM_FRONTEND",
    message="What did we talk about last week?"
).text
```

### For a Non-Technical Person: What Does This Do?

This code allows a developer's *backend server* to talk to the Jean Memory brain. It takes a secure user ID (`user_token`) and a user's question, sends them to Jean Memory, and gets back a block of relevant "context." The developer can then give this context to their own AI to help it respond more intelligently. This is the core product: we provide the memory, they provide the AI.

### What's Happening Under the Hood (For a Technical Person)

This elegant API is made possible by a straightforward client-server architecture.

1.  **`JeanClient` Class:**
    *   **Constructor (`__init__`)**: When a developer calls `JeanClient(api_key=...)`, the constructor simply stores the API key internally and sets the base URL for our backend API (`https://api.jeanmemory.com`).

2.  **`get_context()` Method:** This is the primary method and the main abstraction.
    *   **Input:** It takes the developer-provided `user_token` and `message`.
    *   **Request Construction:** It constructs a network request (e.g., `POST /api/v1/sdk/context`).
    *   **Authentication:** It adds two critical headers to the request:
        1.  `X-Api-Key: YOUR_JEAN_API_KEY` (to authenticate the *developer's application*).
        2.  `Authorization: Bearer USER_TOKEN_FROM_FRONTEND` (to identify the *end-user* whose memory should be accessed).
    *   **HTTP Communication:** It uses a standard HTTP library (like `requests` in Python or `axios` in Node.js) to send the request to our backend.
    *   **Error Handling:** It includes logic to handle non-200 responses. If it gets a `401 Unauthorized`, it means the `user_token` is invalid. If it gets a `403 Forbidden`, the `api_key` is invalid. It would raise a specific error that the developer can catch.
    *   **Response Parsing:** On a successful `200 OK` response, it parses the JSON body, extracts the `text` field from the response (e.g., `{"text": "..."}`), and returns it as a simple string.

**Verdict:** This is a very robust and standard API client design. The complexity of our backend (the tri-database architecture, the AI orchestration, the context engineering flows) is completely hidden behind a single, clean API endpoint. The SDK's job is to make calling that endpoint as simple and elegant as possible. This design is not only feasible, it is the right way to build a modern, developer-friendly API client.

---

## 3. The Custom UI React SDK: The Power-User Path

### The Simple Code (The "Build Your Own UI" Hook)

```tsx
import { useJean, SignInWithJean } from '@jeanmemory/react';

function CustomChat() {
  const agent = useJean(); // The core hook

  if (!agent.isAuthenticated) {
    return <SignInWithJean onSuccess={(user) => agent.setUser(user)} />;
  }

  return (
    <div>
      {/* Your custom UI for messages */}
      <form onSubmit={(e) => agent.sendMessage(input)}>
        {/* Your custom input */}
      </form>
    </div>
  );
}
```

### For a Non-Technical Person: What Does This Do?

This code gives a developer the "raw ingredients" to build their own chat experience. Instead of a pre-built chat window, we give them the core functions: a `useJean` "hook" to get the chat history and send messages, and a `SignInWithJean` button for login. This allows them to design a chat interface that looks and feels completely unique to their application, while still being powered by the Jean Memory brain.

### What's Happening Under the Hood (For a Technical Person)

This approach exposes the underlying primitives that the all-in-one `<JeanChat>` component uses internally. The abstractions here are more granular:

1.  **`useJean()` Hook:** This is the absolute core of the React SDK.
    *   **Accessing Context:** It is a consumer of the `<JeanProvider>`'s context. It doesn't *manage* the state, but it provides a clean, simple API to *access and interact with* it.
    *   **Exposed State:** It returns the live state variables like `messages`, `isAuthenticated`, and `user`. Because it's a hook, any component that calls `useJean()` will automatically re-render whenever this state changes in the provider.
    *   **Exposed Methods:** It returns the key functions for interacting with the backend, like `sendMessage` and `setUser`. These methods are pre-bound to the provider's API client, so the developer doesn't need to worry about passing tokens or API keys around. `sendMessage` works exactly as described in the All-in-One UI section.

2.  **`<SignInWithJean />` Component:**
    *   **Focused Responsibility:** Unlike the `<JeanChat>` component, this component does only one thing: handles the sign-in flow.
    *   **Callback-Driven:** The critical piece is the `onSuccess` prop. This is a function that the component calls *after* the entire OAuth 2.1 flow is complete and it has successfully received the `user` object.
    *   **Decoupling:** This design is crucial because it decouples the authentication flow from the application's state management. The component handles the redirects and token exchange, then hands the final user object back to the developer's application. The developer then decides what to do with it—in this case, calling `agent.setUser(user)` to update the central state in the `<JeanProvider>`.

**Verdict:** This is a fantastic example of a well-architected React library. It offers a simple, "batteries-included" component (`<JeanChat>`) for rapid development and a powerful, flexible set of hooks and granular components (`useJean`, `<SignInWithJean>`) for developers who need full control. The architecture is sound, feasible, and follows industry best practices for building flexible frontend tools.

---

## 4. Direct Tool Access: The Most Granular Control

### The Simple Code (The "Power-User" Tools)

```python
# The deterministic, tool-based way (Python example):
jean.tools.add_memory(
    user_token=...,
    content="My favorite color is blue."
)

search_results = jean.tools.search_memory(
    user_token=...,
    query="what are my preferences?"
)
```

### For a Non-Technical Person: What Does This Do?

This code lets a developer bypass the main "Context Engineering" brain and talk directly to the lower-level memory tools. Instead of letting the AI decide what to remember, the developer can force it to save a specific piece of information with `add_memory`. They can also perform a very specific keyword search with `search_memory`. This is like giving the developer a set of scalpels for precise surgery, instead of a smart assistant that handles the operation for them.

### What's Happening Under the Hood (For a Technical Person)

This exposes a different part of our backend API, moving away from the single, orchestrated `getContext` endpoint and hitting more granular, deterministic endpoints.

1.  **The `tools` Namespace:**
    *   In the `JeanClient` class (Python/Node) or the `useJean` hook (React), we expose a `tools` object. This is a simple organizational pattern. `jean.tools` or `agent.tools` would be an object containing methods that map directly to our specific tool-based API endpoints.

2.  **`tools.add_memory(content, user_token)` Method:**
    *   **Request Construction:** This method constructs a `POST` request to a specific endpoint, for example, `/api/v1/tools/add_memory`.
    *   **Authentication:** It sends both the developer's `X-Api-Key` and the end-user's `Authorization: Bearer <user_token>`.
    *   **Body:** The request body contains the `content` to be saved, e.g., `{"content": "My favorite color is blue."}`.
    *   **Backend Logic:** This endpoint is simpler than `getContext`. It bypasses the "Smart Triage" AI analysis and directly calls the function to save the memory to the databases. It would still perform necessary checks like content deduplication.
    *   **Response:** It would return a simple success or failure message, e.g., `{"success": true, "memory_id": "..."}`.

3.  **`tools.search_memory(query, user_token)` Method:**
    *   **Request Construction:** This constructs a `POST` request to `/api/v1/tools/search_memory`.
    *   **Authentication:** Same as above.
    *   **Body:** The request body contains the search `query`, e.g., `{"query": "what are my preferences?"}`.
    *   **Backend Logic:** This endpoint performs a direct vector search (RAG) in Qdrant for the user associated with the `user_token`. It involves none of the complex orchestration or synthesis from the main `getContext` flow.
    *   **Response:** It would return a raw list of search results, e.g., `{"results": [{"id": "...", "content": "...", "score": 0.89}]}`.

**Verdict:** This is a crucial part of the design for power users. Exposing these granular, deterministic endpoints via a `tools` namespace is a clean, industry-standard way to offer advanced functionality without complicating the primary, orchestrated `getContext` flow. The architecture is completely feasible and adds a necessary layer of flexibility that makes the SDKs feel complete.
