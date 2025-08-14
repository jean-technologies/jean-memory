# Project Brief: Aligning the Jean Connect SDKs & Documentation

**Status:** Strategic Plan
**Date:** 2025-08-10

## 1. Project Goal

The primary goal of this project is to refactor and align our SDKs, backend APIs, and public documentation with a new, more mature strategic vision. This vision positions Jean Memory as a flexible, developer-first "Context Engine" and prioritizes security, modularity, and an exceptional developer experience.

This document summarizes the new vision, the specific problems we've identified in the current codebase, and the collaborative workflow we will use to implement the necessary changes.

---

## 2. The New Vision: Jean Memory as a "Context Engine"

(This is a summary of the key decisions from `IDEAL_SDK_DESIGN.md`)

Our new strategy is guided by several core principles:

*   **We Provide Context, Not Chatbots:** Our primary product is a "Context Engine." We give developers a block of rich, relevant user context; they use that context with their own LLM to generate the final response. This makes our product more flexible and powerful.

*   **Two-Layer SDK Architecture:**
    1.  **Headless Core (`@jeanmemory/core`):** A UI-agnostic library for maximum flexibility.
    2.  **Optional UI (`@jeanmemory/react-ui`):** Pre-built components for developers who want a fast, "Chatbase-like" integration.

*   **Secure, Standardized Authentication:** All authentication will be handled via a secure **OAuth 2.1 flow**. Direct email/password logins from the SDK will be removed. We will support both a frontend (PKCE) flow and a backend (Standard) flow.

*   **A Clean, Purpose-Built API:** We will consolidate our confusing backend endpoints into a single, primary endpoint: `POST /v1/context/enhance`. Endpoints that fall outside our core mission (like `/sdk/synthesize`) will be deprecated.

*   **The Ideal Message Flow:**
    1.  Developer's app calls our API with a user message.
    2.  We perform "Context Engineering" (searching, ranking, assembling).
    3.  We return a single, coherent block of context.
    4.  The developer combines our context with their prompt and sends it to their LLM.

---

## 3. The Problem: Current State vs. Ideal State

(This is a summary of the findings from `SDK_STATE_OF_THE_UNION.md`)

The current codebase is functional but does not reflect our new vision.

*   **Misaligned Purpose:** The SDKs currently act as all-in-one chatbots, including synthesizing final responses, which is not our core mission.
*   **Insecure Auth Patterns:** The SDKs and docs promote an insecure direct email/password login flow instead of the more secure OAuth 2.1 standard we have in place.
*   **Monolithic SDKs:** The core logic is tightly coupled with UI, forcing developers to adopt our UI to use our memory features.
*   **Confusing API Surface:** The backend has multiple, overlapping endpoints that are confusing for developers and hard to maintain.

---

## 4. Action Plan & Collaborative Workflow

To address these issues, we will make a series of surgical edits to the documentation and then the codebase.

**Our Agreed-Upon Workflow:**
The core principle of this project is to **improve the codebase and documentation without losing the valuable elements that already exist.** We will not perform large, sweeping rewrites.

Instead, the agent will:
1.  Propose a single, specific, surgical edit in the chat, referencing the `PROPOSED_DOCS_EDITS.md` file.
2.  Provide the reasoning for the change and a clear before-and-after code snippet.
3.  **Wait for explicit user approval** for that specific change.
4.  Once approved, the agent will apply only that single change.
5.  This process will be repeated for each subsequent edit, ensuring the user has full control over the process.

### 4.1 Proposed Documentation Edits

(This is a summary of the actionable items from `PROPOSED_DOCS_EDITS.md`)

The following is the initial list of surgical edits we will make to the documentation, one by one, following the workflow described above.

#### **File: `openmemory/ui/docs-mintlify/sdk/react.mdx`**
1.  **Remove Email/Password Warning:** Delete the outdated warning about email/password accounts, as the new OAuth flow supports all sign-in methods.
2.  **Update `useJeanAgent` Hook Docs:** Update the hook's documented return values to remove the insecure `signIn` function and add new methods like `connect` and `setUser`.
3.  **Update Custom `useJeanAgent` Example:** Update the code example to use the correct and secure authentication pattern with the `<SignInWithJean />` component.

#### **File: `openmemory/ui/docs-mintlify/sdk/python.mdx`**
1.  **Add Production Auth Note:** Add a clear warning that the current `authenticate` method is for development only and that production apps should use a proper server-to-server OAuth flow.

#### **File: `openmemory/ui/docs-mintlify/sdk/nodejs.mdx`**
1.  **Correct Quickstart Example:** Replace the incorrect `agent.run()` example with a correct example showing how to create a Next.js API route handler.
