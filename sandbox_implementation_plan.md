# Sandbox Environment Implementation Plan

## 1. Main Purpose

The goal is to create a sandbox environment that allows new, unauthenticated users to try out the core functionality of Jean Memory without needing to sign up. This will provide a "Try it now" button on the landing page, leading to a temporary, fully functional version of the application.

To accomplish this, we will implement a system for creating temporary, anonymous user accounts on the backend. These accounts will be restricted to the sandbox and their data will be automatically deleted after 24 hours.

## 2. Backend Implementation (`openmemory/api`)

### 2.1. Database Model Changes

The `User` model needs to be updated to support anonymous users.

**File:** `openmemory/api/app/models.py`

-   In the `User` class, add two new columns:
    -   `is_anonymous` (Boolean, default `False`, indexed)
    -   `last_seen_at` (DateTime, nullable)
-   To ensure compatibility with different database backends (PostgreSQL in production, SQLite in local development), replace any instance of `JSONB` with `JSON` and `ARRAY(Float)` with `JSON`.

```python
# In openmemory/api/app/models.py

# ... imports
from sqlalchemy import (
    Column, String, Boolean, ForeignKey, Enum, Table,
    DateTime, JSON, Integer, UUID, Index, event, UniqueConstraint, Text, func, text
)
# ...

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True, default=lambda: uuid.uuid4())
    # ... existing columns
    is_anonymous = Column(Boolean, default=False, nullable=False, index=True)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_current_utc_time, index=True)
    # ...
```

### 2.2. Database Migration

After modifying the model, a new database migration must be generated and applied.

1.  **Generate the migration:**
    ```bash
    cd openmemory/api
    alembic revision --autogenerate -m "Add anonymous user fields"
    ```
2.  **Apply the migration:**
    ```bash
    alembic upgrade head
    ```
    *Note: If local database issues arise, it may be necessary to reset the local database by deleting `openmemory.db` and regenerating a single initial migration.*

### 2.3. Python 3.10 Compatibility

The codebase uses some features from Python 3.11 that are not available in 3.10. These need to be made backwards-compatible.

1.  **`datetime.UTC`:** Replace all instances of `datetime.UTC` with `datetime.timezone.utc`. Remember to import `timezone` from `datetime`.
    -   **File:** `openmemory/api/app/routers/memories.py`
2.  **`.astext` operator:** The `.astext` operator for querying JSON is not supported by SQLite. Replace it with a standard equality check (`==`).
    -   **File:** `openmemory/api/app/services/background_processor.py`

### 2.4. Create New Sandbox API Endpoints

A new router will be created to handle all sandbox-related logic, keeping it separate from the main application.

1.  **Create the router file:**
    -   **File:** `openmemory/api/app/routers/sandbox.py`

2.  **Implement the endpoints:**
    -   `POST /sandbox/session`: This endpoint will not require authentication. It will:
        -   Create a new `User` in the database with `is_anonymous=True`.
        -   Generate a JWT for this user with a 24-hour expiration.
        -   Return the JWT to the client.
    -   `POST /sandbox/memories`: This endpoint will be protected and require the sandbox JWT. It will:
        -   Validate the JWT and extract the anonymous user's ID.
        -   Create a new `Memory` associated with this user.
        -   Add a `ttl` (Time-To-Live) to the memory's metadata to mark it for deletion after 24 hours.

3.  **Register the new router:**
    -   In `openmemory/api/main.py`, import the sandbox router and include it in the FastAPI app *without* the standard `Depends(get_current_supa_user)` dependency.

## 3. Frontend Implementation (`openmemory/ui`)

### 3.1. Add "Try it now" Button

Modify the landing page to include a "Try it now" button next to the "One-Click Setup" button. This button should link to the `/sandbox` page.

**File:** `openmemory/ui/app/page.tsx`

### 3.2. Create the Sandbox Page

Create a new page that provides the sandbox user experience.

1.  **Create the page file:**
    -   **File:** `openmemory/ui/app/sandbox/page.tsx`

2.  **Implement the page logic:**
    -   The page should have a chat-like interface.
    -   On component mount, it will call the `POST /api/v1/sandbox/session` endpoint to get a session token.
    -   It will store this token in its state.
    -   When the user submits a memory, it will use the token to make an authenticated request to `POST /api/v1/sandbox/memories`.
    -   It should display the new memories in the chat interface.

### 3.3. Fix API URL Configuration

The frontend is currently hardcoded to use the wrong API port. This needs to be corrected.

-   The frontend code uses `process.env.NEXT_PUBLIC_API_URL` but has hardcoded fallbacks to `http://localhost:8765`.
-   Change these fallbacks to `http://localhost:8000`.
-   **Files to check:** `openmemory/ui/hooks/useMemoriesApi.ts` and `openmemory/ui/components/dashboard/Install.tsx`.
-   For local development, ensure the dev server is started with the correct environment variable: `NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev`.

### 3.4. Install Frontend Dependencies
The `uuid` package is a new dependency for the sandbox page.
- Run `pnpm add uuid && pnpm add -D @types/uuid` in the `openmemory/ui` directory.

## 4. Testing

1.  **Clear Browser Data:** Before testing, clear all local storage, session storage, and cookies for `localhost` in your browser. This is crucial to ensure the app does not use a stale authentication token.
2.  **Start the Backend:** `cd openmemory/api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
3.  **Start the Frontend:** `cd openmemory/ui && NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev`
4.  **Test:** Open a new Incognito/Private browser window and navigate to `http://localhost:3000`. The "Try it now" button should be visible. Click it to enter the sandbox. 