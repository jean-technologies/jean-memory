
# Jean Memory: V3 Testing Strategy - Grounded in Core Architecture

## 1. Back to Basics: The Core Mission
This document outlines a new testing strategy that is grounded in the foundational principles of our core architectural documents. We are moving away from any potentially flawed recent implementations and back to the original vision: a simple, powerful, and resilient server-side orchestration system.

The mission is to test and guarantee the performance of the architecture laid out in `JEAN_MEMORY_REVAMP.md` and `AGENTIC_MEMORY_FLOW_ANALYSIS_JULY_28_2025.md`.

## 2. The Ground-Truth Architecture Under Test
This is the architecture we will test against.

### The Tool Signature (The "Contract")
```python
async def jean_memory(
    user_message: str,
    is_new_conversation: bool = False,
    needs_context: bool = True
) -> str:
```
-   **The Client's Job is Simple**: The client's only job is to provide these three parameters. All intelligence resides on the server.

### The Two Critical Paths

1.  **The Fast Path (Synchronous, User-Facing)**
    -   Receives the user message.
    -   **Immediately** triggers the "Asynchronous Path."
    -   Performs a fast, simple vector search for immediate context.
    -   Returns this context to the user in **under 3 seconds**.

2.  **The Asynchronous Path (Background "Heavy Thinking")**
    -   Receives the user message from the Fast Path.
    -   **AI Planner**: Decides on the optimal context strategy (e.g., "deep analysis," "targeted search").
    -   **Deep Analysis & Synthesis**: Executes the plan, which can take up to 60 seconds.
    -   **Synthesize & Save**: Saves the rich, synthesized result as a *new, high-quality memory*.
    -   **AI Triage**: Intelligently decides if the original user message is worth saving and saves it if necessary.

## 3. Key Metrics & Targets (Grounded in the Vision)

| Metric | Path | Target (P95) | Rationale |
| --- | --- | --- | --- |
| **Fast Path Latency** | Fast Path | **< 3 seconds** | This is the most critical user-facing metric. |
| **Deep Analysis Latency** | Asynchronous Path | **< 60 seconds** | The "heavy thinking" has a longer time budget to ensure quality. |
| **Timeout Resilience** | Fast Path & Async Path | **100%** | A timeout in the Async Path must **never** block the Fast Path. The memory saving process must also be resilient to timeouts. |
| **Context Quality** | Both Paths | **> 90%** | The Fast Path must return relevant context. The Async Path must create high-quality, synthesized memories. |
| **Memory Triage Accuracy** | Asynchronous Path | **> 95%** | The AI Triage must accurately decide what is and is not worth saving. |

## 4. A New, Focused Testing Plan

We will create three new, focused test suites that directly map to our architectural vision.

### Suite 1: `latency_and_resilience`
-   **Location**: `openmemory/api/tests/latency_and_resilience/`
-   **Purpose**: To enforce our latency targets and ensure the system is resilient to failures.
-   **Key Tests**:
    -   `test_fast_path_latency.py`: Measures the end-to-end latency of the Fast Path.
    -   `test_deep_analysis_latency.py`: Measures the end-to-end latency of the Asynchronous Path.
    -   `test_timeout_resilience.py`: Simulates a timeout in the Asynchronous Path and asserts that the Fast Path still succeeds and the memory is still saved.

### Suite 2: `context_quality`
-   **Location**: `openmemory/api/tests/context_quality/`
-   **Purpose**: To measure the quality and relevance of the context we provide.
-   **Key Tests**:
    -   `test_fast_path_relevance.py`: Uses a "golden set" of user queries to assert that the Fast Path returns relevant, useful context.
    -   `test_synthesis_quality.py`: Uses a "golden set" of user queries to assert that the Asynchronous Path creates high-quality, accurate, and insightful synthesized memories.

### Suite 3: `triage_accuracy`
-   **Location**: `openmemory/api/tests/triage_accuracy/`
-   **Purpose**: To measure the accuracy of our AI-powered memory saving decisions.
-   **Key Tests**:
    -   `test_triage_decision_accuracy.py`: Uses a "golden set" of user messages labeled as `REMEMBER` or `SKIP` to assert that the AI Triage makes the correct decision.

## 5. Implementation Plan
1.  **Archive the `evals` folder**: To avoid confusion, we will archive the existing `evals` folder.
2.  **Create the new test suite directories**: I will create the `latency_and_resilience`, `context_quality`, and `triage_accuracy` directories.
3.  **Implement one key test**: As a starting point, I will implement the `test_fast_path_latency.py` test to demonstrate the new testing methodology.

This new strategy is a direct reflection of our core architectural vision. It is focused, measurable, and designed to ensure we build the resilient, high-performance system we've designed. 