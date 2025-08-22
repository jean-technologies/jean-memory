# Refactoring Summary: Improving Context Retrieval Reliability

This document outlines the troubleshooting and refactoring process undertaken to improve the reliability and quality of Jean Memory's context retrieval tools, specifically the `balanced` and `autonomous` modes.

## High-Level Problem

The primary goal was to fix the `autonomous` mode of the `jean_memory` tool, which was silently failing and returning empty context. A secondary goal was to improve the quality and accuracy of the `balanced` mode, which was returning anemic and often incorrect answers due to a limited context window.

During the process, a series of critical deployment-blocking bugs were discovered and resolved.

---

## Issues Encountered & Solutions Implemented

This section details the problems faced in chronological order, the root cause analysis, and the corresponding fix.

### 1. Initial `autonomous` Mode Silent Failure

-   **Problem:** The `autonomous` mode was returning an empty string with no error, making it unreliable for production use.
-   **Initial Analysis:** The logic inside the `_standard_orchestration` function was suspected. The default "middle path" for context retrieval seemed to have a flaw where it could fail to generate context and return an empty string.
-   **Root Cause Discovery:** Through a process of elimination (including forcing a hardcoded return value), it was discovered that the issue was not inside `_standard_orchestration`. The root cause was a **race condition** in the parent `jean_memory` function. A background task (`run_deep_analysis_and_save_as_memory`) was being called at the same time as the main response task. Both were calling the same underlying orchestration logic, causing the background task to interfere with and nullify the response of the main task.
-   **Solution:**
    1.  The `jean_memory` function was refactored to cleanly separate the immediate response logic from the background tasks.
    2.  The `run_deep_analysis_and_save_as_memory` background task was completely overhauled to be fully decoupled. It now runs a true `deep_memory_query` and saves the result as a new memory, providing long-term value without interfering with the immediate response.
    3.  The default "middle path" of the `autonomous` mode was hardened to use the same robust logic as the `balanced` mode.

### 2. Poor Quality of `balanced` and `autonomous` Responses

-   **Problem:** The answers from `balanced` and `autonomous` modes were low-quality, often incorrect, and cited a very low number of memories (typically 10 or fewer).
-   **Root Cause:** The `ask_memory` function, which powers both modes, was using a single, broad semantic search with a `limit` parameter that was being overridden by a lower default in the underlying `mem0` search client. This starved the synthesis model of sufficient context.
-   **Solution:** The context gathering logic in `ask_memory` was completely refactored.
    1.  It no longer relies on a single search. Instead, it performs **three targeted searches in parallel** to gather a rich and diverse set of memories: one for the user's direct query, one for core personality traits, and one for recent activities.
    2.  This new strategy consistently provides a much larger set of unique memories (20+) to the synthesis model, dramatically improving the accuracy and comprehensiveness of the final answer.

### 3. Cascade of Deployment Failures

During the iterative fixing process, several basic but critical bugs were introduced that caused the production deployment to fail repeatedly.

-   **`TypeError: The @tool decorator was used incorrectly`**: A syntax error where `@mcp.tool` was used instead of `@mcp.tool()`.
    -   **Fix:** Corrected the syntax.
-   **`ImportError: Circular Import`**: Refactoring introduced a circular dependency between `memory.py` and `search_operations.py`, where each file was trying to import the other.
    -   **Fix:** Resolved by changing the import statements to pull directly from the source files, breaking the loop.
-   **`NameError: name 'list_memories' is not defined`**: A function was used without being imported at the top of the file.
    -   **Fix:** Added the missing import statement.
-   **`SyntaxError: invalid syntax`**: A stray `finally:` block was left in the code after a refactoring step.
    -   **Fix:** Removed the erroneous code block.
-   **`TypeError: 'coroutine' object does not support the asynchronous context manager protocol`**: An `async` function was called with `async with` when it should have been called with `await`.
    -   **Fix:** Corrected the call from `async with` to `await`.
-   **`TypeError: string indices must be integers, not 'str'`**: The code was not correctly parsing the JSON string returned by the `list_memories` wrapper function, leading to a data type mismatch.
    -   **Fix:** This was ultimately resolved by removing the wrapper function entirely from this path and using direct client calls, which guarantee a consistent data type.

---

## Architectural Improvements

Based on insights gained during the debugging process, two proactive architectural improvements were made:

1.  **New `get_context_by_depth` Tool:** A new, more explicit MCP tool was created. Instead of the ambiguous `autonomous` mode, this tool allows the client (e.g., Claude) to specify the exact context depth it requires (`none`, `fast`, `balanced`, `comprehensive`). This is a more robust and predictable pattern for server-to-server communication.
2.  **New MCP API Documentation:** A new documentation page (`mcp-api.mdx`) was created to provide clear guidance for enterprise users and developers who need to interact directly with the MCP API endpoint, including details on authentication and handling streaming responses.
