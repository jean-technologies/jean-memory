# Refined Product Strategy: The Jean Memory Context Engine

**Status:** Master Plan
**Date:** 2025-08-10

## 1. The Core of Our Business: A Headless Context Engine

Our primary product is a **headless context engine**, delivered via a simple, secure API. Our mission is to provide developers with the rich, personal context they need to make their AI applications truly intelligent. We are a specialized tool that integrates into their existing stack.

The UI we offer is a powerful convenience and a demonstration of our core product, but it is an *optional layer*, not the product itself.

### The Ideal Integration Flow
This is the "golden path" that our SDKs and documentation must champion.

1.  **Frontend (Auth):** A developer uses our simple `<SignInWithJean />` component to securely authenticate a user via OAuth 2.1. This provides the developer with a `userToken`.
2.  **Backend (Context):** The developer's backend receives this `userToken` and uses our headless SDK (e.g., `@jeanmemory/node`) to call our core API.
3.  **The Magic:** Our API, the "Context Engine," does its work: searching the memory graph, ranking results, and assembling a coherent block of context.
4.  **The Handoff:** We return this raw context string to the developer's backend. Our job is now done.
5.  **Developer's Control:** The developer takes our context, combines it with their own prompt and logic, and sends it to their LLM of choice.

## 2. Key Architectural Concepts

(This section preserves the valuable architectural and context engineering details from `JEAN_MEMORY_BIBLE.md` and our discussions.)

### Memory Architecture: The Tri-Database Design
To deliver powerful context, we use a specialized, multi-database architecture:
*   **PostgreSQL:** For structured metadata (users, memories, apps). The reliable foundation.
*   **Qdrant (Vector DB):** For lightning-fast semantic search and relevance ranking (RAG).
*   **Neo4j (Graph DB):** For understanding the deep relationships and connections between memories.

### Context Engineering, Not Just Retrieval
This is our key differentiator. We don't just fetch data; we *engineer* context. This involves:
*   **Smart Triage:** An AI-powered filter that decides what information is meaningful enough to remember.
*   **Dual-Path Processing:** A fast, immediate search for instant context, followed by a deeper, asynchronous analysis that creates new "insight memories."
*   **Strategic Orchestration:** Using different context strategies (`deep_understanding`, `relevant_context`) depending on the user's needs.

## 3. The "Sign In with Jean" Experience

"Sign In with Jean" is more than a button; it's the gateway to the user's memory. It's how a user grants an application permission to access their context layer.

The flow must be:
1.  **Secure:** Always a full-page redirect to `jeanmemory.com` for the primary login, using the OAuth 2.1 PKCE standard.
2.  **User-Centric:** After login, the user should be given a clear choice: return to the application or optionally connect more memory sources.
3.  **Seamless:** The SDK must handle the token exchange in the background, making the return to the application smooth and transparent.

## 4. The Ideal SDKs: A Two-Layer Model

To support both headless and UI--based integrations, our SDKs will be modular.

*   **The Core SDK (e.g., `@jeanmemory/core`):** A headless, UI-agnostic library. Its primary method will be `getContext({ token, message })`. This is the product for most developers.
*   **The UI SDK (e.g., `@jeanmemory/react-ui`):** An optional wrapper that provides pre-built components like `<JeanAgent />` for the fastest possible visual integration.

## 5. Example Use Cases (Inspiring the Developer)

Our documentation must show developers what's possible with a powerful context engine.
*   **Agentic AI:** An AI that can perform multi-step tasks because it has the user's entire project history as context.
*   **Personalized Education:** An AI tutor that remembers a student's knowledge gaps and learning style, adapting its lessons in real-time.
*   **Proactive Assistants:** An AI that can anticipate a user's needs (e.g., "I see you have a flight to London tomorrow, should I check for delays?") because it has access to their calendar and travel history.

---
This document will now serve as our single source of truth for all subsequent development and documentation efforts.
