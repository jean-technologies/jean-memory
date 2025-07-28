
# Jean Memory: V2 Testing Strategy for a Resilient Orchestrator

## 1. Core Mission & Lessons Learned
Our previous testing strategy was a good start, but it missed the mark. After a thorough review of our incident reports and architectural vision, it's clear we need a strategy that is less about individual function performance and more about the **resilience, intelligence, and speed of the end-to-end orchestration flow**.

This V2 strategy is built on the key lessons learned from our real-world failures:
-   **Timeouts are catastrophic**: A slow AI planner not only degrades the user experience but also causes memory loss.
-   **The client is not always predictable**: We cannot assume the client AI will correctly interpret our responses.
-   **Asynchronicity is our strength**: Our architecture is designed to provide a fast initial response while handling deep analysis in the background. Our testing must reflect this.

## 2. The Critical Paths Under Test (V2)

### Path A: The "Fast Path" (Immediate Response)
This is the user-facing, synchronous path that must be fast and reliable every single time.
1.  `jean_memory` tool receives a user message.
2.  It **immediately** performs a simple, fast vector search.
3.  It **simultaneously** triggers the "Asynchronous Deep Analysis Path."
4.  It returns the results of the simple search in under 3 seconds.

### Path B: Asynchronous Deep Analysis & Synthesis
This is the background path where the "heavy thinking" happens.
1.  The background worker receives the user message from the "Fast Path."
2.  **AI Planner**: It uses an AI model to create a "context plan."
3.  **Deep Analysis**: It executes the plan, which may involve multiple searches and synthesis steps.
4.  **Synthesize & Save**: It saves the result as a new, high-quality, pre-computed memory that will be instantly available for future queries.

## 3. Key Metrics & Targets (V2)
Our metrics are now focused on the end-to-end user experience and the resilience of the system.

| Metric | Path | Target (P95) | Rationale |
| --- | --- | --- | --- |
| **Fast Path End-to-End Latency** | Fast Path | **< 3 seconds** | The user must get a useful, initial response quickly. This is our most critical user-facing metric. |
| **Deep Analysis Latency** | Deep Analysis | **< 60 seconds** | The asynchronous deep analysis has a longer time budget to ensure it can perform high-quality synthesis. |
| **Timeout Resilience** | Fast Path | **100%** | If the deep analysis path fails or times out, the user must still receive the "Fast Path" response. We will test this by simulating failures. |
| **Context Quality Score** | Fast Path & Deep Analysis | **> 90%** | A qualitative score that measures both the immediate relevance of the "Fast Path" response and the quality of the synthesized memories from the "Deep Analysis" path. |
| **Memory Triage Accuracy** | Deep Analysis | **> 95%** | How accurately the AI triage process matches a human-labeled "golden set" of memorable vs. non-memorable statements. |
| **Client Contract Adherence** | Fast Path | **100%** | A new test to ensure that when we return a "Context is not required" response, the client AI does not inject its own persona. |

## 4. Focused Testing Suites (V2)

### Suite 1: `performance`
-   **Location**: `openmemory/api/tests/performance/`
-   **Purpose**: To measure the raw latency of our two critical paths.
-   **Method**: We will create end-to-end tests that simulate a user query and measure the time it takes to get a "Fast Path" response, and the time it takes for the "Deep Analysis" path to complete in the background.

### Suite 2: `quality` (Replaces `relevance` and `triage`)
-   **Location**: `openmemory/api/tests/quality/`
-   **Purpose**: To measure the intelligence and accuracy of our system.
-   **Method**: We will create a "golden set" of user scenarios. Each scenario will have:
    -   A user query.
    -   An expected "Fast Path" response.
    -   A label indicating if the memory should be saved (`REMEMBER` or `SKIP`).
    -   An expected synthesized memory if the message is memorable.
-   The test will run the scenario and assert against all four of these conditions.

### Suite 3: `resilience` (New)
-   **Location**: `openmemory/api/tests/resilience/`
-   **Purpose**: To ensure our system can gracefully handle failures.
-   **Method**: We will create tests that simulate failures in the "Deep Analysis" path (e.g., by patching the AI planner to raise a `TimeoutError`). These tests will assert that the "Fast Path" response is still returned to the user, and that the failure is logged correctly.

### Suite 4: `client_contract` (New)
-   **Location**: `openmemory/api/tests/client_contract/`
-   **Purpose**: To solve the "Persona Problem" by ensuring the client AI adheres to our contract.
-   **Method**: We will create a test that calls the `jean_memory` tool with `needs_context: false`. The test will then need to simulate the client AI's behavior and assert that it does not inject any additional context. This will likely require a mock of the client-side AI model.

## 5. Continuous Improvement Loop
Our CI/CD pipeline will be updated to run all four of these test suites on every pull request. A failure in any of these suites, or a significant regression in our performance metrics, will block the pull request from being merged. This will ensure that every change we make is not only functional but also fast, intelligent, and resilient. 