---
title: Jean Connect - The Ideal SDK & API Design
description: "The strategic vision for the Jean Connect SDKs, APIs, and developer experience."
---

**Version:** 2.2 (Draft)
**Status:** Strategic Vision

## Part 1: Core Philosophy & Vision
(This section is up-to-date and reflects our core tenets.)

---

## Part 2: The Pyramid of Integration - Our Core Model

Our architecture can be understood as a pyramid. Developers can integrate at the layer that best suits their needs, with the SDK being the primary path for most.

```mermaid
graph TD
    D[**Layer 4: The Appliance**<br/>Optional UI Component<br/>`JeanChat` Component] --> C;
    C[**Layer 3: The SDK**<br/>The Developer's Power Cord<br/>`@jeanmemory/core`] --> B;
    B[**Layer 2: MCP**<br/>The AI's Smart Outlet<br/>`JSON-RPC Protocol for Tool Use`] --> A;
    A[**Layer 1: The Foundation**<br/>Core Functions & Basic REST API<br/>`jean_memory()`]

    style D fill:#c9d1d9,stroke:#1e293b,stroke-width:2px
    style C fill:#9fb0c4,stroke:#1e293b,stroke-width:2px
    style B fill:#708090,stroke:#1e293b,stroke-width:2px
    style A fill:#475569,stroke:#1e293b,stroke-width:2px
```

- **Layer 1 (Core API):** The lowest-level functions. Not the primary integration path.
- **Layer 2 (MCP):** The structured protocol our system uses for tool-use. An implementation detail for most.
- **Layer 3 (The SDK):** **The primary product for developers.** A headless, language-specific wrapper that makes it simple to call the MCP and get context.
- **Layer 4 (UI Component):** An optional, pre-built component for the fastest possible visual integration.

---

## Part 3: The Full-Stack Data Flow
(This diagram is up-to-date and reflects the headless-first flow.)

---

## Part 4: Authentication & Connection Flow
(This section is up-to-date and reflects our secure, OAuth-first approach.)

---

## Part 5: The Two-Layer SDK Architecture
(This section is up-to-date.)

---

## Part 6: API & Protocol - A Clearer Definition
(This section is up-to-date.)

---

## Part 7: The Ideal Developer Documentation Experience

Our documentation is a product in itself. It must be architected to get developers to a "moment of success" as quickly as possible. The ideal structure is:

1.  **Introduction:** A 60-second pitch. "What is this and why should I care?"
2.  **Quickstart:** Two simple, parallel paths for immediate value: "Add a Chatbot UI" and "Add Context to Your Backend."
3.  **Core Concepts:** A page explaining the "Pyramid of Integration" so developers understand the flexibility of the platform.
4.  **Guides:** A dedicated "Full-Stack Workflow" guide that connects the dots between frontend authentication and backend context retrieval.
5.  **API Reference:** Granular details for developers deep in implementation.

### Future Documentation Improvements (Suggestions)
- **Interactive Examples:** Embed live CodeSandbox or StackBlitz components directly in the docs.
- **API Explorer:** Use tools like Mintlify's API reference component to allow developers to make live API calls from the documentation.
- **Video Snippets:** Create short, focused video walkthroughs for key concepts like the full-stack workflow.

---

## Part 8: The Future - True Contextual Bias
(This section is up-to-date.)
