# JIRA Task: Data Plane Layer - Scope & Permissions Architecture

**Task Name:** Data Plane Layer - Memory Scope & Permission System Implementation  
**Task Type:** Epic/Feature  
**Priority:** P1  
**Epic:** Privacy & Data Control  
**Story Points:** 13  

---

## Task Description

Implement a comprehensive Data Plane Layer that enables fine-grained permission control over memory access in Jean Memory SDKs. This system allows developers to request specific scopes of memory access (e.g., all memories, app-specific only, time-bounded) while giving users granular control over what data they share with each application. This creates a trust-based ecosystem where users maintain sovereignty over their memories while developers can build powerful, personalized AI experiences.

**Current State:** No scope/permission system - all applications get full memory access  
**Target State:** Granular permission system with user consent and developer scope declarations

---

## Mini-FRD (What & Why)

### What
Build a permission system that sits between user authentication and memory access, enabling developers to declare memory scopes (all_memories, app_specific, time_bounded) and users to grant/modify those permissions through a consent interface.

### Why  
- **User Privacy Control**: Users need sovereignty over their personal memory data
- **Developer Trust**: Clear permission model builds user confidence in SDK applications
- **Platform Differentiation**: Privacy-first approach sets Jean Memory apart from competitors
- **Enterprise Readiness**: Enterprise customers require granular data access controls
- **Regulatory Compliance**: Supports GDPR/privacy law requirements for data access transparency

### Scope

**In Scope (MVP):**
- Memory scope system: `all_memories`, `app_specific`, `time_bounded`
- User permission grant/deny interface during SDK authentication
- JWT token enhancement with scope-based access controls
- Memory filtering based on granted permissions at runtime
- Permission management dashboard for users
- Scope declaration in SDK components (JeanAgent, etc.)

**Out of Scope (Future Phases):**
- Category-based filtering (e.g., "only work memories")
- Semantic content filtering (e.g., "exclude personal information")
- Real-time permission modification during sessions
- Cross-application memory sharing permissions
- Advanced audit logging and usage analytics

### Acceptance Criteria
- [ ] Developers can declare memory scope in JeanAgent: `scope="all_memories"` or `scope="app_specific"`
- [ ] Users see permission request UI during first SDK authentication
- [ ] Users can grant full requested permissions or modify to more restrictive scope
- [ ] JWT tokens include granted scope information for runtime filtering
- [ ] Memory search/retrieval respects granted permission scope automatically
- [ ] Users can view and revoke application permissions in dashboard
- [ ] App-specific scope only returns memories created within that application
- [ ] Time-bounded scope only returns memories within specified date range
- [ ] Permission violations are gracefully handled with clear error messages
- [ ] Existing applications continue working with default `all_memories` scope

---

## Mini-EDD (How)

### Chosen Approach
Implement a layered permission system that extends the existing JWT authentication with scope-based access controls. The system intercepts memory operations at the API layer and applies filtering based on user-granted permissions stored in the database. This approach leverages existing infrastructure while adding minimal complexity to the developer experience.

### Key Components / Code Areas
- `openmemory/api/app/models/` - Permission grant database schemas
- `openmemory/api/app/routers/sdk_oauth.py` - Permission request/grant endpoints
- `openmemory/api/app/utils/data_plane_scoping.py` - Scope validation and filtering logic
- `jean_memory/search.py` - Memory filtering integration  
- `jean_memory/mem0_adapter_optimized.py` - App-specific memory scoping
- `sdk/react/SignInWithJean.tsx` - Permission request UI
- `openmemory/ui/app/dashboard/` - Permission management interface

### Implementation Steps
1. **Database Schema for Permissions** (1 day)
   - Create `user_permission_grants` table for storing app permissions
   - Add permission tracking fields to user/application relationship
   - Migrate existing users to default `all_memories` permissions

2. **JWT Token Enhancement** (1 day)
   - Extend JWT payload with granted scope information
   - Add scope validation middleware for memory API endpoints
   - Implement scope downgrade logic (users can only reduce, not expand scope)

3. **Permission Request Flow** (2 days)
   - Create permission request API endpoints (`/sdk/permissions/request`, `/sdk/permissions/grant`)
   - Build permission consent UI component for SDK authentication
   - Implement permission modification interface (grant subset of requested scope)

4. **Memory Filtering Implementation** (3 days)
   - Add scope-aware filtering to hybrid search system (mem0 + Graphiti)
   - Implement app-specific memory isolation using `client_name` parameter
   - Add time-bounded filtering for date-range restricted access
   - Update memory add/search methods to respect permission scope

5. **SDK Integration** (2 days)
   - Add `scope` parameter to JeanAgent component initialization
   - Update authentication flow to handle permission requests
   - Add scope declaration to Python and Node.js SDKs
   - Implement graceful degradation when permissions are restricted

6. **User Dashboard & Management** (2 days)
   - Build permission management interface for users
   - Add application permission listing with grant/revoke controls
   - Implement permission audit trail and usage visibility
   - Add notification system for permission requests

7. **Testing & Validation** (2 days)
   - Test permission flows across all SDK types
   - Validate memory isolation between applications
   - Test permission modification scenarios and edge cases
   - Security testing for permission bypass attempts

### Risks & Mitigation
- **Performance impact of filtering** → Implement efficient database queries with proper indexing, cache frequent permission lookups
- **Complex permission edge cases** → Start with simple binary permissions (grant/deny), add complexity in later phases  
- **User confusion about permissions** → Design clear, non-technical permission descriptions with usage examples
- **Developer adoption friction** → Make permission system optional with sensible defaults, provide clear migration path
- **Memory isolation bugs** → Comprehensive testing with multiple applications, automated permission validation tests

### Testing Plan
- **Permission Isolation**: Create multiple test applications, verify memory separation
- **Scope Enforcement**: Test that restricted tokens cannot access out-of-scope memories
- **User Experience**: Test permission grant/modification flows across devices
- **Performance**: Benchmark memory operations with permission filtering enabled
- **Security**: Attempt to bypass permission checks, validate JWT scope tampering protection

---

## Implementation Notes

### Current Infrastructure Analysis  
✅ **Foundation Available:**
- JWT authentication system with scope support already implemented
- Existing OAuth flow can be extended with permission requests
- Database infrastructure ready for permission storage
- Dual-system memory architecture (mem0 + Graphiti) identified for scoping

✅ **Critical Gaps:**  
- No user permission storage or management system
- Memory operations don't filter based on application scope
- No UI for permission consent or management
- SDK components don't support scope declaration

### Architecture Integration Points
Based on existing `DATA_PLANE_LAYER_V1_IMPLEMENTATION.md`, the system must integrate with:
- **mem0 Integration**: Add `agent_id` scoping to `mem0_adapter_optimized.py:186-208`
- **Graphiti Integration**: Add `group_id` scoping to `integrations.py:419,443`  
- **Unified Search**: Update `search.py:354-358` for dual-system permission filtering
- **OAuth Scopes**: Extend `oauth_simple_new.py:98` with memory scopes: `"memory:all"`, `"memory:app_specific"`

### Permission Model Details
```typescript
interface PermissionGrant {
  user_id: string;
  developer_api_key: string;  
  application_name: string;
  requested_scope: MemoryScope;
  granted_scope: MemoryScope;  // Can be more restrictive than requested
  grant_modifications: {
    excluded_apps?: string[];
    time_boundary?: Date;
  };
  granted_at: Date;
  expires_at?: Date;
  revoked_at?: Date;
}

type MemoryScope = 
  | "all_memories"      // Full access to user's memory vault
  | "app_specific"      // Only memories from this app  
  | "time_bounded"      // Memories within time range
  | { type: "custom", ...restrictions };
```

### Breaking Changes Assessment
- **Minimal impact expected** - System designed to be backward compatible
- Existing applications without scope declaration default to `all_memories`
- Permission grant is one-time during initial authentication
- Memory filtering happens transparently at API layer

---

## Definition of Ready Checklist
- [x] FRD and EDD sections completed with technical depth
- [x] Acceptance criteria clearly defined and testable
- [x] Integration points with existing architecture identified  
- [x] Database schema requirements specified
- [x] Security and privacy implications thoroughly reviewed
- [x] Performance considerations addressed
- [x] Breaking changes assessment completed (minimal impact)

## Subtasks
1. **JMS-101**: Database schema design and permission storage system
2. **JMS-102**: JWT token enhancement with scope validation middleware  
3. **JMS-103**: Permission request/grant API endpoints and consent flow
4. **JMS-104**: Memory filtering integration (mem0 + Graphiti dual-system scoping)
5. **JMS-105**: SDK scope declaration and authentication flow updates
6. **JMS-106**: User permission management dashboard and interfaces
7. **JMS-107**: Comprehensive testing and security validation
8. **JMS-108**: Documentation and developer migration guide

---

**Ready for Development** ✅  
**Estimated Timeline**: 3-4 sprints (6-8 weeks)  
**Dependencies**: OAuth Sign-in Support task (for enhanced authentication flow)