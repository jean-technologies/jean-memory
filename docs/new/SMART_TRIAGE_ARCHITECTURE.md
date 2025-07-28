# Jean Memory: The "Smart Triage" Architecture

This document outlines the current, improved architecture for the `jean_memory` tool. It is designed to be fast, effective, and reliable, addressing the challenges identified in the `AGENTIC_MEMORY_FLOW_ANALYSIS_JULY_28_2025.md` document.

The core principle is **asynchronous processing**: the system provides an immediate, useful response while handling complex analysis and memory saving in the background.

---

## High-Level Flow

The system now operates on two parallel paths: an immediate, synchronous path for user-facing responsiveness, and two independent, asynchronous paths for background processing.

```mermaid
graph TD
    A[User Message] --> B{jean_memory tool};

    subgraph "Foreground: Immediate Response (< 3s)"
        B --> C{Fast Vector Search};
        C --> D[Vector DB];
        D --> C;
        C --> E[Return Fast Context];
        E --> B;
    end
    
    subgraph "Background Task 1: Smart Triage & Save"
        B -- triggers --> F(Async Triage Worker);
        F --> G{AI Memory Analysis (Fast)};
        G -- "Is message memorable?" --> H{Decision};
        H -- No --> I[Discard];
        H -- Yes --> J(Save to All DBs);
    end

    subgraph "Background Task 2: Deep Analysis (if needs_context)"
        B -- also triggers --> K(Async Deep Analysis Worker);
        K --> L{Advanced AI Analysis (Slow)};
        L --> M[Synthesize New Insight];
        M --> N(Save Insight to All DBs);
    end

    subgraph "Database Layer"
        subgraph "mem0 Library"
            direction LR
            J --> O[Vector DB: Qdrant];
            J --> P[Graph DB: Neo4j];
            N --> O;
            N --> P;
        end
        J --> Q[Metadata DB: PostgreSQL];
        N --> Q;
    end

    style J fill:#bbf,stroke:#333,stroke-width:2px;
    style N fill:#bbf,stroke:#333,stroke-width:2px;
```
---

## Detailed Implementation

### 1. The `jean_memory` Tool (User-Facing)

-   **Path**: `openmemory/api/app/tools/orchestration.py`
-   **Responsibility**: To be the fast, non-blocking entry point.
-   **Actions**:
    1.  Receives the `user_message`.
    2.  Immediately triggers the "Smart Triage" background task for the message.
    3.  If `needs_context` is true, it also triggers the "Deep Analysis" background task.
    4.  Performs a quick, simple vector search for immediately relevant context.
    5.  Returns the results of the fast search to the user in under 3 seconds.

### 2. Background Task 1: Smart Triage & Save

-   **Path**: `triage_and_save_memory_background` in `openmemory/api/app/mcp_orchestration.py`
-   **Responsibility**: To intelligently decide if a message is worth saving.
-   **Actions**:
    1.  Uses a fast AI model to analyze the message content (`_ai_memory_analysis`).
    2.  Looks for salient, personal information (facts, preferences, goals) and ignores conversational filler or generic questions.
    3.  **If memorable**: It calls the robust `_add_memory_background` function to save the extracted content.
    4.  **If not memorable**: It logs the decision and discards the message.

### 3. Background Task 2: Deep Analysis & Synthesis

-   **Path**: `run_deep_analysis_and_save_as_memory` in `openmemory/api/app/mcp_orchestration.py`
-   **Responsibility**: To perform deep, "heavy thinking" and enrich the memory store over time.
-   **Actions**:
    1.  Uses a powerful AI model (e.g., Gemini 2.5 Pro) to perform a comprehensive analysis of the user's message in the context of their existing memories. This is the step that can take up to 60 seconds.
    2.  It synthesizes the findings into a new, high-quality insight.
    3.  It saves this new insight as a new memory, prefixed with `[System Insight based on: ...]`.

### 4. Memory Saving: The `_add_memory_background` Function

-   **Path**: `openmemory/api/app/mcp_orchestration.py`
-   **Responsibility**: To be the single, reliable function for writing to the databases.
-   **Verification**: This function's logic has been confirmed to be correct and robust. It reliably:
    1.  Calls `mem0.add()` to write to the **Vector DB (Qdrant)** and **Graph DB (Neo4j)**.
    2.  Receives the new memory ID from `mem0`.
    3.  Writes a corresponding record to the **Metadata DB (PostgreSQL)**, linking everything together.

## Benefits of this Architecture

-   **Effective**: The system is now highly selective, ensuring the memory store remains high-quality.
-   **Reliable**: The memory saving process is robust and handles all three databases correctly. Critical interactions are no longer lost due to timeouts.
-   **Responsive**: The user always gets a fast response, as all time-consuming operations happen in the background.
-   **Intelligent**: The system benefits from both immediate context and long-term, deep analysis, creating a "compounding intelligence" effect.
-   **Scalable & Maintainable**: The decoupled, asynchronous design allows for future optimization and easier maintenance. 