# Fix Memory Count Inconsistency Between Dashboard and Memories Pages

## Task Description

Fix the inconsistency in memory count calculation between the `/dashboard` page and `/memories` page. Currently, these pages show different numbers of total memories due to different filtering logic in their respective backend API endpoints.

## Mini-FRD (What & Why)

### 1. What
Align memory counting logic between the dashboard progress bar ("X Memories Created") and grid items with the total memory count displayed in the /memories page so users see consistent numbers across the application.

### 2. Why
Currently, users see different memory counts on different pages which creates confusion and undermines trust in the application's data integrity. The dashboard uses `/api/v1/apps/` endpoint while the memories page uses `/api/v1/memories/` endpoint, each with different filtering criteria for what constitutes a "valid" memory to count.

### 3. Scope

**In Scope:**
- Standardize memory filtering logic between `/api/v1/apps/` and `/api/v1/memories/` endpoints
- Ensure dashboard memory count matches memories page count
- Update frontend memory count aggregation logic to be consistent
- Verify "Source App" column in memories page uses same app identification logic as dashboard grid items

**Out of Scope:**
- Changes to memory deletion/archiving workflows
- UI design changes beyond fixing the count discrepancy
- Performance optimizations unrelated to the counting logic

### 4. Acceptance Criteria
- Dashboard progress bar shows same total memory count as memories page
- Each app's memory count in dashboard grid matches the count when filtering by that app in memories page
- Source App column in memories page uses same app identification logic (client_id/app_id) as dashboard
- Memory counts update consistently across both pages when memories are created/deleted/archived

## Mini-EDD (How)

### 1. Chosen Approach
Standardize on the `/api/v1/memories/` filtering logic as the single source of truth since it provides more granular state-based filtering. Update the `/api/v1/apps/` endpoint to use the same memory state filtering instead of `deleted_at.is_(None)`.

### 2. Key Components / Code Areas
- `openmemory/api/app/routers/apps.py:40-52` (memory count subquery)
- `openmemory/api/app/routers/memories.py:71-76` (memory filtering logic)
- `openmemory/ui/app/dashboard/page.tsx:238-244` (frontend total calculation)
- `openmemory/ui/hooks/useMemoriesApi.ts:149-152` (memory count return)
- `openmemory/ui/hooks/useAppsApi.ts:113-122` (apps API response handling)

### 3. Implementation Steps
- Analyze current memory state vs deleted_at field usage patterns in database
- Update apps.py memory count query to filter by Memory.state instead of deleted_at
- Verify app identification logic consistency between endpoints (app_id vs client_id)
- Test memory counts on both pages with various memory states
- Add integration tests to prevent future count discrepancies

### 4. Risks & Mitigation
- Memory state enum values inconsistency → audit all MemoryState usages before changes
- Database migration needed if deleted_at logic differs from state logic → analyze existing data first
- Cached memory counts on frontend → ensure both pages refresh after backend changes
- Performance impact from changing query logic → benchmark before and after query performance

### 5. Testing Plan
- Create memories with different states (active, paused, archived, deleted) from different apps
- Verify counts match between dashboard and memories page
- Test filtering by specific apps in memories page matches dashboard grid numbers
- Confirm Source App column shows consistent app names with dashboard grid items
- Test memory creation/deletion flows to ensure counts update consistently across pages