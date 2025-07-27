# Project Status & Next Steps: Life Graph Performance Enhancement

**Date:** July 27, 2025

## 🎯 **CRITICAL ISSUE: Life Graph Takes 30+ Seconds to Load**

**The Problem:** The "Life Graph" feature in the Jean Memory dashboard currently takes **30-40 seconds** to load, making it completely unusable for users.

**The Solution:** This document outlines the entity extraction backfill process needed to make the Life Graph load **instantly** by pre-computing entity data instead of processing it in real-time.

**Current Status:** New memories are automatically processed (✅ **FIXED FOR NEW DATA**), but **9,181 existing memories** need backfill processing to complete the performance fix.

## 1. Objective

This document provides a technical overview of the Jean Memory system, details the critical performance issue with the "Life Graph" visualization feature, and outlines the steps already taken to resolve it. The goal is to provide a clear path forward for completing the implementation and **making the Life Graph load instantly** instead of taking 30+ seconds.

## 2. System Architecture Overview

The Jean Memory system is a sophisticated memory layer for AI applications, composed of several key components:

*   **Core API:** A set of granular, tool-based functions for memory operations, including `add_memories`, `search_memory`, `ask_memory`, and `deep_memory_query`.
*   **Intelligent Orchestration Layer:** A primary `jean_memory` tool that acts as a smart controller, analyzing user intent and calling the appropriate core API tools to retrieve or store information.
*   **Data Storage:** A hybrid model using PostgreSQL (via Supabase) for structured data and metadata, Qdrant for vector search, and Neo4j for graph-based relationships.
*   **Frontend:** A dashboard that includes a "Life Graph" feature, designed to visualize the connections and entities within a user's memories.

## 3. The Problem: Unacceptable UI Latency

A critical performance issue was identified in the "Life Graph" feature.

*   **Symptom:** The UI component takes **30-40 seconds** to load, creating an unusable user experience.
*   **Root Cause:** The backend endpoint powering the graph (`/api/v1/memories/life-graph-data`) was performing **real-time, synchronous entity extraction**. For every page load, the system would fetch all relevant memories and then make numerous, slow API calls to a large language model (`GPT-4o-mini`) to identify and extract entities *while the user was waiting*.
*   **Scalability Issue:** This approach does not scale. As the number of memories grows, the load time increases, and the risk of hitting database or API rate limits becomes severe.

## 4. The Solution: Asynchronous, Event-Driven Entity Extraction

To resolve this, we have re-architected the entity extraction process to be asynchronous and event-driven. The goal is to perform the heavy lifting as a one-time background job, allowing the UI to load instantly by querying pre-computed data.

### Implementation Status:

1.  **Schema Modification (Complete):** An `entities` column of type `JSONB` has been added to the `memories` table in the database. This column is indexed and designed to store the structured results of the entity extraction. An Alembic migration script for this change has been created and committed (`8bf2c14a5afa_add_entities_column_to_memories_table.py`).

2.  **Application Logic Update (Complete ✅):**
    *   A new service, `extract_and_store_entities`, has been created to handle the logic of calling the AI model and saving the results.
    *   **IMPORTANT:** The `add_memories` flow has been updated to trigger this service as a non-blocking background task whenever a **new** memory is created. This means **all future memories will have entities pre-computed and will not cause Life Graph slowdowns**.

3.  **Data Backfill for Existing Memories (In Progress):**
    *   **The Gap:** While new memories will be processed correctly, the `entities` field for all **9,181 existing memories** is currently `NULL`.
    *   **The Tool:** A standalone script, `scripts/utils/standalone_backfill.py`, has been created to iterate through all existing memories and run the entity extraction process for them.
    *   **Challenges Encountered:** Initial attempts to run this script on the production environment failed due to `ModuleNotFoundError` and `Max client connections reached` errors.
    *   **Current State:** The script has been significantly refactored to resolve these issues. It now correctly handles its Python path and processes memories in small, sequential batches to avoid overwhelming the database.

## 5. Required Next Steps: Complete the Life Graph Performance Fix

The code for the complete solution has been committed and pushed to the `main` branch. **New memories are already being processed automatically**. However, the final, crucial step is to manually run the backfill script on the production environment to process the existing 9,181 memories. 

**⚠️ Until this backfill is complete, the Life Graph will continue to take 30+ seconds to load for users with existing memories.**

### How to Run the Backfill Job on Render:

1.  **Navigate to the Cron Job:** Go to the Render Dashboard and select the **`narrative-backfill-weekly`** Cron Job.
2.  **Initiate a Manual Run:** Click the **"Trigger Run"** or **"Manual Run"** button.
3.  **Set the Correct Command:** In the dialog or settings page for the manual run, set the command to the following:
    ```bash
    python scripts/utils/standalone_backfill.py entities
    ```
4.  **Execute the Job:** Start the manual run. The job will take a significant amount of time to complete (potentially several hours), but its progress can be monitored via the logs. It is designed to be safe to run in the background.

### Post-Backfill Verification:

*   **SUCCESS CRITERIA:** Once the job is complete, the "Life Graph" feature should load in **under 3 seconds** instead of 30+ seconds.
*   Test the Life Graph with a user account that has many existing memories to confirm the performance improvement.
*   **Crucially, the default command for the `narrative-backfill-weekly` Cron Job should be changed back to `python scripts/utils/standalone_backfill.py narrative` to ensure its normal weekly operation is restored.**

### Expected Impact:

*   **Before Backfill:** Life Graph takes 30-40 seconds to load (unusable)
*   **After Backfill:** Life Graph loads instantly (under 3 seconds)
*   **Long-term:** All new memories will have entities pre-computed, preventing future performance issues 