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
