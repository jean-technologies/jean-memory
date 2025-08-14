# Proposed Surgical Edits for Documentation

**Status:** Awaiting Review
**Date:** 2025-08-10

## Overview

This document outlines specific, surgical edits to bring the documentation in line with `IDEAL_SDK_DESIGN.md`. Each proposed change is presented individually for review to ensure we improve accuracy while preserving the core of the existing docs.

---

### **File: `openmemory/ui/docs-mintlify/sdk/react.mdx`**

#### **Edit 1: Remove Email/Password Account Warning**

*   **Reason:** The new, primary authentication flow is OAuth 2.1, which supports all account types (including Google/GitHub). This warning is no longer accurate and may confuse users.
*   **Current Code (Lines 14-16):**
    ```mdx
    <Warning>
    **Account Requirement**: This SDK only works with Jean Memory accounts created using email/password. Accounts created via Google or GitHub sign-in are not currently supported.
    </Warning>
    ```
*   **Proposal:** Delete these three lines entirely.

---

#### **Edit 2: Update `useJeanAgent` Hook Documentation**

*   **Reason:** The `signIn(email, password)` function is being removed to enforce the more secure OAuth flow. We need to update the hook's documented return values to reflect this.
*   **Current Code (Lines 121-124):**
    ```mdx
    - **signIn(email, password)**: Sign in function
    - **sendMessage(message)**: Send message to AI
    - **storeDocument(title, content)**: Store document to Jean Memory
    - **clearConversation()**: Clear current chat
    ```
*   **Proposed Change:**
    *   Remove the `signIn` line.
    *   Add `setUser(user)` and `signOut()` for developers building custom auth flows.
    *   Add `connect(service)` for the new integrations flow.
*   **Proposed Code:**
    ```mdx
    - **isAuthenticated**: Boolean for auth state
    - **user**: The authenticated user object (`JeanUser | null`).
    - **messages**: The array of conversation messages.
    - **sendMessage(message)**: Sends a message to the assistant.
    - **storeDocument(title, content)**: Saves a document to the user's memory.
    - **connect(service)**: Initiates the connection flow for an external service (e.g., 'notion').
    - **clearConversation()**: Clears the current chat history.
    - **setUser(user)**: Manually sets the user state (for custom auth flows).
    - **signOut()**: Clears the user session.
    ```

---

#### **Edit 3: Update Custom `useJeanAgent` Example**

*   **Reason:** The current advanced example uses the now-deprecated `agent.signIn`. It needs to be updated to show the correct pattern using the `<SignInWithJean />` component.
*   **Current Code (Lines 106-108):**
    ```jsx
    if (!agent.isAuthenticated) {
      return <SignInWithJean onSuccess={agent.signIn} />;
    }
    ```
*   **Proposed Code:**
    ```jsx
    if (!agent.isAuthenticated) {
      // The `SignInWithJean` component handles the entire OAuth flow.
      // The `onSuccess` callback receives the user object, which we use
      // to update the agent's state.
      return (
        <SignInWithJean
          apiKey="YOUR_JEAN_SK_API_KEY"
          onSuccess={(user) => agent.setUser(user)}
        />
      );
    }
    ```

---

### **File: `openmemory/ui/docs-mintlify/sdk/python.mdx`**

#### **Edit 1: Add a Note About Production Authentication**

*   **Reason:** The current `agent.authenticate(email, password)` method is a development convenience. We need to add a note advising developers to use a proper OAuth 2.1 flow for production backend services to ensure security.
*   **Proposal:** Add the following note directly above the authentication code block.
*   **Proposed Code:**
    ```python
    # NOTE: This direct email/password method is a convenience for local 
    # development and testing. For production applications, you should implement 
    # a secure server-to-server OAuth 2.1 flow.

    agent.authenticate(
        email="user@example.com", 
        password="user_password"
    )
    ```

---

### **File: `openmemory/ui/docs-mintlify/sdk/nodejs.mdx`**

#### **Edit 1: Correct the Quickstart Example**

*   **Reason:** The current quickstart shows an incorrect `agent.run()` method. The primary use case for the Node.js SDK is to create an API route handler.
*   **Current Code (Lines 14-22):**
    ```javascript
    import { JeanAgent } from 'jeanmemory-node';

    const agent = new JeanAgent({
      apiKey: process.env.JEAN_API_KEY
    });

    await agent.run();
    ```
*   **Proposed Code:**
    ```typescript {{ title: '/pages/api/chat.ts' }}
    import { createJeanHandler } from 'jeanmemory-node';

    // This handler is compatible with the Vercel AI SDK and edge runtimes
    export const config = {
      runtime: 'edge',
    };

    // This one line creates the entire API endpoint
    export default createJeanHandler({
      apiKey: process.env.JEAN_API_KEY
    });
    ```

---
**(More edits will be added here for your review after we agree on these.)**
