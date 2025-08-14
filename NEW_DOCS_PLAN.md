# Jean Memory Documentation Plan: From Vision to Implementation

**Status:** Draft
**Date:** 2025-08-10
**Owner:** AI Assistant

## 1. Guiding Principles

This documentation will be architected around the core principles defined in our product strategy:

*   **We are a Headless Context Engine:** Our primary product is an API that delivers rich, personal context. The docs must be "headless-first."
*   **Developer Experience is the Product:** The goal is to get developers to a "moment of success" in under 5 minutes. Simplicity, clarity, and powerful examples are paramount.
*   **Modular & Flexible:** Developers can integrate at the level that suits them, from a simple UI component to a powerful backend library. The docs will clearly delineate these paths.
*   **Secure by Design:** We will exclusively document and promote the secure OAuth 2.1 authentication flow.

## 2. Proposed Documentation Structure

This is the proposed sitemap and content strategy for the new documentation.

---

### **`/introduction` (The 60-Second Pitch)**

*   **Goal:** Answer "What is Jean Memory and why should I care?"
*   **Content:**
    *   **Headline:** "Stop building chatbots. Start building copilots."
    *   **Core Value Prop:** Jean Memory is a developer-first context engine that gives your AI application a perfect, long-term memory. Instead of just responding, your app can now understand, anticipate, and reason based on your user's entire history.
    *   **Simple Diagram:** A visual showing the "golden path":
        *   `[Your App] <--> [Jean Memory API] <--> [User's Memory Graph (Notion, Slack, etc.)]`
        *   The diagram should emphasize that Jean sits between the developer's app and the user's scattered data, transforming it into coherent context.
    *   **Key Use Cases (Briefly):**
        *   **Agentic AI:** Build agents that can execute complex, multi-step tasks.
        *   **Personalized Experiences:** Create AI tutors that remember a student's progress or a financial advisor that understands a user's history.
        *   **Proactive Assistants:** Power AI that can anticipate needs based on calendars, emails, and more.
    *   **The Gateway:** Introduce the `<SignInWithJean />` button as the simple, secure way for a user to grant your application access to their memory.

---

### **`/quickstart` (The 5-Minute Success)**

*   **Goal:** Get a developer running with a tangible result immediately.
*   **Content:** Two clear, parallel tracks presented side-by-side.

    *   **Track 1: Add an AI Chatbot to Your App in Minutes**
        *   **Focus:** The "appliance" model using our pre-built UI component.
        *   **Audience:** Developers who want the fastest possible visual integration.
        *   **Steps:**
            1.  Install `@jeanmemory/react`.
            2.  Wrap your app in `<JeanProvider>`.
            3.  Add the `<JeanChat />` component.
            4.  (Show a complete, copy-pasteable React component).

    *   **Track 2: Add Context to Your Backend Agent**
        *   **Focus:** The "headless" model using our core SDK.
        *   **Audience:** Developers who have an existing AI backend and want to superpower it with context.
        *   **Steps (using Node.js/TypeScript as the primary example):**
            1.  Install `@jeanmemory/node`.
            2.  Get a `userToken` on your frontend (briefly mention `<SignInWithJean />`).
            3.  On your backend, before calling your LLM, call the Jean SDK:
                ```typescript
                import { JeanClient } from '@jeanmemory/node';

                const jean = new JeanClient({ apiKey: process.env.JEAN_API_KEY });

                const context = await jean.getContext({
                  userToken: 'USER_TOKEN_FROM_FRONTEND',
                  message: 'What was the last thing we talked about regarding the Q3 budget?'
                });

                // Now, add this context to your LLM prompt
                const finalPrompt = `
                  Context: ${context.text}
                  ---
                  User question: What was the last thing we talked about regarding the Q3 budget?
                `;
                ```

---

### **`/architecture` (How the Magic Works)**

*   **Goal:** Explain the underlying power of our system to build confidence and showcase our technical depth.
*   **Content:**
    *   **The Pyramid of Integration:** Use the Mermaid diagram from `IDEAL_SDK_DESIGN.md` to show the different layers of our platform (Core API -> MCP -> SDK -> UI Component). Explain that developers can choose their entry point.
    *   **The Tri-Database Design:** Briefly explain the role of PostgreSQL (metadata), Qdrant (semantic search), and Neo4j (relationship graph). This demonstrates our commitment to specialized, high-performance architecture.
    *   **Introduction to Context Engineering:** Explain that we don't just *retrieve* data, we *engineer* context. Mention "Smart Triage" and "Dual-Path Processing" as examples of how we create meaningful context from noise. Link to the full Context Engineering page for a deep dive.

---

### **`/sdk/overview` (The Developer's Power Cord)**

*   **Goal:** Provide a consolidated overview of our SDKs and the two-layer model.
*   **Content:**
    *   Explain the **Two-Layer SDK model**:
        *   **Core SDK (`@jeanmemory/core`):** The headless, UI-agnostic library for backend use. Its job is to provide context.
        *   **UI SDK (`@jeanmemory/react`):** An optional wrapper that provides pre-built components for rapid UI development.
    *   Link out to the detailed pages for each language.

### **`/sdk/react` | `/sdk/python` | `/sdk/nodejs`**

*   **Goal:** Detailed, implementation-focused guides for each language.
*   **Structure for each page:**
    1.  **Installation & Setup:** `npm install` / `pip install`.
    2.  **Core Headless SDK:**
        *   How to initialize the client.
        *   The primary method: `getContext()`.
        *   Clear code example showing how to integrate the response into a call to an LLM (e.g., OpenAI, Anthropic).
    3.  **UI SDK (for React):**
        *   Detailed guide on using `<JeanProvider>`, `<JeanChat />`, and the `useJean` hook.
        *   Show a custom UI example using the hook, demonstrating how to use `agent.user`, `agent.messages`, `agent.sendMessage`, etc. Crucially, it will show the auth flow using `<SignInWithJean onSuccess={(user) => agent.setUser(user)} />`.
    4.  **Advanced Usage (Aspirational):**
        *   Briefly mention that future versions will allow for more granular control, such as specifying context strategies (`deep_understanding` vs. `relevant_context`) or using deterministic tools (`add_memory`, `search_memory`).

---

### **`/authentication` (The Gateway to Memory)**

*   **Goal:** Clearly document our secure authentication flows.
*   **Content:**
    *   **Philosophy:** We use OAuth 2.1 because security and user trust are non-negotiable.
    *   **Flow 1: Browser-Based (for Frontends):**
        *   Explain the PKCE flow.
        *   Deep dive into the `<SignInWithJean />` React component, explaining its props (`apiKey`, `onSuccess`, `onError`). Show how `onSuccess` provides the `user` object and `userToken`.
    *   **Flow 2: Server-to-Server (for Backends):**
        *   Explain the standard Authorization Code Grant flow for headless services that need to access Jean Memory on a user's behalf.
        *   Provide examples using `curl` and a Node.js library.

---

### **`/context-engineering` (Our Secret Sauce)**

*   **Goal:** Detail our key differentiator and provide a path for custom solutions.
*   **Content:**
    *   (Keep much of the existing content which is good).
    *   Deep dive into **Smart Triage**, **Dual-Path Processing**, and **Strategic Orchestration**.
    *   **New Section: "Your Logic, Our Engine"**
        *   "We offer pre-built context strategies like `deep_understanding` and `relevant_context`."
        *   "For advanced use cases, you can design your own context engineering flows. Our platform is built to be extensible. If you have a unique challenge, reach out to our solutions team to discuss a custom implementation."

---

### **`/use-cases` (Inspiring the Developer)**

*   **Goal:** Show, don't just tell.
*   **Content:**
    *   Expand on the key use cases.
    *   For each use case (Agentic AI, Personalized Education, Proactive Assistant):
        *   Provide a short description.
        *   Show a simplified code example of how it would be implemented.
        *   **Future Goal:** Embed an interactive demo (e.g., CodeSandbox, StackBlitz) for each.

---

### **DEPRECATED / REMOVED**
*   **Tools Page:** The concept of "Tools" will be folded into the "Advanced Usage" section of the SDK docs. A top-level page is not needed for the initial launch, to maintain simplicity.
