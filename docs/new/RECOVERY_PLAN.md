# Jean Memory API Recovery Plan

**Date**: July 28, 2025
**Status**: In Progress
**Objective**: To restore the `main` branch to a known stable state while preserving critical new features and all documentation.

---

## 1. The Problem

Following the introduction of a centralized tool configuration (commit `db508427`), the MCP tool-loading system became unstable, leading to multiple cascading errors in production, including `NotImplementedError` and `TypeError` in the MCP routing layer. Reverting to various commits proved difficult as the true root cause was a flawed architectural change that was never fully stabilized.

## 2. The Recovery Strategy

The plan is to execute a "surgical" reset of the `main` branch, going back to a known-good state and then carefully re-applying only the specific, isolated features that are confirmed to be valuable and stable.

### Step 1: Establish a Clean Baseline

-   The `main` branch will be hard reset to commit `5cacbc2e`. This is the last commit *before* the problematic centralized tool configuration was introduced, representing the last known stable architecture.

### Step 2: Restore Critical Assets

-   **Preserve Documentation:** Immediately following the reset, the entire `docs/` directory from the most recent commit (`f50e0469`) will be checked out and restored to `main`.
-   **Restore Stable Claude Client:** The file `openmemory/api/app/clients/claude.py` will be checked out from commit `da232a19`. This version contains a simple, hard-coded tool list that is known to be stable and bypasses the broken central configuration system.

### Step 3: Re-apply Isolated Features

-   The **Gemini Deep Life Query** feature will be re-introduced by checking out the following files from commit `d2e7d7a`:
    -   `openmemory/api/app/routers/memories.py`
    -   `openmemory/api/app/utils/gemini.py`

### Step 4: Finalize and Deploy

-   All of the above changes will be committed to the local `main` branch in a single, comprehensive commit.
-   The local `main` branch will then be **force-pushed** to the remote repository. This will overwrite the unstable history on the server and trigger a new deployment from a clean, stable, and feature-complete baseline. 