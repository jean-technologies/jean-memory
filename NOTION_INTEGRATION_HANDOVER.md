# Notion Integration Handover & Post-Mortem

**Version: 3.0**

**To the next engineer:** This document is a handover of the Notion integration feature. The initial implementation attempt encountered significant, cascading issues that have now been fully reverted. This document contains an exhaustive post-mortem of those issues and a precise, safe plan for completing the feature without repeating past mistakes.

---

## 1. Project Goal & Current State

*   **Objective:** To build a B2B2C onboarding flow for users to connect their Notion account via OAuth 2.0 and import selected pages into Jean Memory.
*   **Current Git State:** The local git repository has been fully reset (`git reset --hard HEAD`) and cleaned (`git clean -fd`). It is in a clean state, identical to the last stable commit on the `main` branch. All broken code has been deleted.
*   **Current Database State:** The production Supabase database has been **manually and safely reverted** to its pre-incident state. The deployment-breaking issue is resolved. You can safely redeploy the current `main` branch.

---

## 2. Exhaustive Post-Mortem of Failures

It is critical to understand the root causes of the initial failures to ensure they are not repeated. The issues stemmed from a combination of code, procedural, and database errors.

### 2.1. Code Errors: The Configuration Cascade

The primary bug was a series of mistakes related to application configuration.

1.  **Initial `ImportError`:**
    *   **Mistake:** A new file was created at `openmemory/api/app/config.py`. This conflicted with the existing **directory** at `openmemory/api/app/config/`, which is a Python package. When other modules tried to `import app.config`, Python's import system became confused, leading to a crash.
    *   **Learning:** Before adding new files to core application directories, always check for naming conflicts with existing files *and directories*.

2.  **Second `ValidationError`:**
    *   **Mistake:** To fix the above, `config.py` was renamed to `settings.py`. However, this new file was created with an *incomplete* Pydantic `Settings` class, defining only the new Notion variables. The application requires many other variables (`OPENAI_API_KEY`, `DATABASE_URL`, etc.) to be defined. When the server started, Pydantic correctly identified that these required fields were missing and threw a `ValidationError`, crashing the server again.
    *   **Learning:** The application's `Settings` class is a strict contract. Any modification must account for *all* required configuration variables.

### 2.2. Procedural Errors: Ignoring the `README.md`

The code errors were compounded by a failure to follow established procedures for running the application.

*   **Mistake:** Instead of using the project's `Makefile` commands, the servers were started with generic commands like `uvicorn app.main:app` and `npm run dev` from incorrect directories. This led to `ModuleNotFoundError`s (because the Python path was wrong) and "Address already in use" errors.
*   **Learning:** The `README.md` is the single source of truth. The **only** correct way to run the development environment is:
    1.  `cd openmemory`
    2.  Terminal 1: `make dev-api`
    3.  Terminal 2: `make dev-ui`

### 2.3. Critical Database Error & Recovery

This was the most serious issue and the one that broke the production deployment.

1.  **Discovery of Schema Drift:** The command `alembic revision --autogenerate` was run against the live production database. The output revealed a major **schema drift**—the database schema contained tables and columns that were not present in the local SQLAlchemy models.
2.  **The Mistake:** A migration (`128aa64496db_...py`) was generated and then applied directly to the production database using the provided database URL. This updated the `alembic_version` table in your database, effectively telling it, "My current version is now `128aa64496db`".
3.  **The Consequence:** This migration file was **never committed to git**. When you later updated an environment variable on Render, it triggered a new deployment. The deployment process pulled the latest code from GitHub (which did not have the new migration file) and ran its pre-deploy command, `alembic upgrade head`. This failed catastrophically because the database claimed to be at a version that the codebase did not recognize.
4.  **The Recovery:** The production database was manually repaired with the following `psql` commands. This is a log of the actions taken to restore stability:
    *   `DROP TABLE user_integrations;` *(This removed the table that was incorrectly added).*
    *   `UPDATE alembic_version SET version_num = '49aad20c1d17';` *(This reset the database's version number back to the last valid revision that actually exists in the codebase).*

---

## 3. The Safe Path Forward: Rebuilding Without Migrations

**CRITICAL WARNING:** **DO NOT ATTEMPT TO RUN DATABASE MIGRATIONS.** The schema drift is a real and dangerous issue that must be addressed separately. The following plan will add the Notion feature **without requiring any schema changes.**

### 3.1. Strategy: Use the `User.metadata` Field

The `User` model in `openmemory/api/app/models.py` already has a flexible `metadata = Column(JSONB, default=dict)` field. We will use this to store the Notion access token.

### 3.2. Step-by-Step Re-Implementation Plan

1.  **Configuration:**
    *   Create a file at `openmemory/api/app/settings.py`.
    *   Populate it with a complete Pydantic `Settings` class (including all variables like `OPENAI_API_KEY`, etc., plus the new Notion variables). Export an instance named `config`.
    *   Modify `openmemory/api/app/database.py` to correctly import `config` from `app.settings`.

2.  **Backend Logic (No Model Changes):**
    *   Create `openmemory/api/app/integrations/notion_service.py`.
    *   Add the necessary endpoints (`/auth`, `/callback`, `/pages`, `/sync`) to `openmemory/api/app/routers/integrations.py`.
    *   **In the `/callback` endpoint:**
        *   After getting the access token from Notion, fetch the `User` object.
        *   Update the metadata: `user.metadata['notion_access_token'] = token_data`.
        *   **Crucially**, import `flag_modified` from `sqlalchemy.orm.attributes` and mark the change: `flag_modified(user, "metadata")`. This is required to make SQLAlchemy save the JSON change.
        *   Commit the session.
    *   **In the `/pages` and `/sync` endpoints:**
        *   Retrieve the token via `user.metadata.get('notion_access_token')`.

3.  **Frontend:**
    *   Create the UI at `openmemory/ui/app/onboarding/page.tsx`.
    *   Implement the multi-step flow using `useState` and `useSearchParams` to handle the redirect from Notion.

4.  **Running & Testing:**
    *   From the `openmemory/` directory, run `make dev-api` and `make dev-ui`.
    *   Test the full flow at `http://localhost:3000/onboarding`.

5.  **Deployment:**
    *   Only after the feature works perfectly locally, commit all new and modified files and push to `main`. This will trigger a safe deployment on Render.
