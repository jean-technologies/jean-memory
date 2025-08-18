# Jean Memory Data Plane Layer - Scope & Permissions Architecture

**Date:** August 7, 2025  
**Status:** Design Phase  
**Purpose:** Balance user privacy control with developer functionality through granular data access permissions

## Executive Summary

The Data Plane Layer introduces a sophisticated permission system that sits between user authentication and memory access. This layer enables developers to request specific scopes of memory access while giving users fine-grained control over what data they share with each application. This creates a trust-based ecosystem where users maintain sovereignty over their memories while developers can build powerful, personalized AI experiences.

## Core Concepts

### Memory Scopes

Developers define the scope of memory access their application requires:

1. **`all_memories`**: Access to the user's complete memory vault across all applications
2. **`app_specific`**: Access only to memories created within the developer's application
3. **`time_bounded`**: Access to memories within a specific time range (e.g., last 30 days)
4. **`category_specific`**: Access to memories tagged with specific categories (future enhancement)

### Data Access Authorization Flow

```
Developer defines scope → User authenticates → Permission UI presented → User grants/modifies → Access token issued
        ↓                      ↓                      ↓                        ↓                    ↓
    JeanAgent               Sign in            Data Access Form          Authorization         Scoped JWT
   scope="all"              with Jean           □ All memories            API Call           with permissions
```

## Developer Experience

### Defining Scope in JeanAgent

**React SDK:**
```typescript
import { JeanAgent } from '@jeanmemory/react';

function MyApp() {
  return <JeanAgent 
    apiKey="jean_sk_..."
    systemPrompt="You are a helpful tutor"
    scope="all_memories"  // Required scope declaration
    scopeReason="To provide personalized tutoring based on your learning history"
  />;
}
```

**Python SDK:**
```python
from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_...",
    system_prompt="You are a supportive therapist",
    scope="all_memories",
    scope_reason="To understand your emotional patterns and provide better support"
)
agent.run()
```

### Available Scope Options

```typescript
type MemoryScope = 
  | "all_memories"      // Full access to user's memory vault
  | "app_specific"      // Only memories from this app
  | "time_bounded"      // Memories within time range
  | {
      type: "custom",
      applications?: string[],     // Specific app memories
      timeRange?: { start: Date, end?: Date },
      categories?: string[],       // Future: category filtering
      excludeApplications?: string[]  // Blacklist specific apps
    };
```

## User Experience

### Permission Authorization UI

When a user signs in to an application using Jean Memory, they see:

```
┌─────────────────────────────────────────────────────┐
│          MathTutor AI Data Access Request           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  MathTutor AI is requesting access to:              │
│                                                     │
│  ☑ All your memories                               │
│    └─ Reason: To provide personalized tutoring     │
│        based on your learning history               │
│                                                     │
│  ⚠️ This includes memories from:                    │
│  • All applications you've used                    │
│  • All time periods                                │
│  • All categories of information                   │
│                                                     │
│  ─────────────────────────────────────             │
│                                                     │
│  Modify Access (Optional):                          │
│  ☐ Only memories from specific apps:               │
│     ☐ Claude Desktop                               │
│     ☐ Cursor AI                                   │
│     ☐ Previous MathTutor sessions                 │
│  ☐ Only recent memories (last 30 days)            │
│                                                     │
│  ⚠️ Warning: Limiting access may affect            │
│     functionality as intended by the developer      │
│                                                     │
│  [Deny All]  [Grant Selected]  [Grant All]         │
└─────────────────────────────────────────────────────┘
```

### User Control Features

1. **Granular Selection**: Users can grant subset of requested permissions
2. **Application Filtering**: Choose specific applications to include/exclude
3. **Time Boundaries**: Limit to recent memories only
4. **Functionality Warning**: Clear notice about potential limitations
5. **Revocation**: Users can revoke permissions at any time from dashboard

## Technical Implementation

### Permission Storage Schema

```typescript
interface UserPermissionGrant {
  id: string;
  user_id: string;
  developer_api_key: string;
  application_name: string;
  requested_scope: MemoryScope;
  granted_scope: MemoryScope;
  grant_modifications: {
    excluded_apps?: string[];
    time_boundary?: Date;
    included_categories?: string[];
  };
  granted_at: Date;
  expires_at?: Date;
  revoked_at?: Date;
}
```

### JWT Token Enhancement

The access token includes permission details:

```json
{
  "sub": "user_id",
  "aud": "developer_api_key",
  "scope": {
    "type": "modified",
    "base": "all_memories",
    "restrictions": {
      "excluded_apps": ["personal_journal"],
      "time_boundary": "2025-01-01T00:00:00Z"
    }
  },
  "iat": 1723046400,
  "exp": 1723050000
}
```

### Memory Filtering at Runtime

```python
async def apply_scope_filter(
    memories: List[Memory], 
    scope: PermissionScope,
    user_id: str
) -> List[Memory]:
    """Filter memories based on granted permissions"""
    
    filtered = memories
    
    # Apply app-specific filtering
    if scope.type == "app_specific":
        filtered = [m for m in filtered if m.source_app == scope.app_id]
    
    # Apply time boundaries
    if scope.time_boundary:
        filtered = [m for m in filtered if m.created_at >= scope.time_boundary]
    
    # Apply exclusions
    if scope.excluded_apps:
        filtered = [m for m in filtered if m.source_app not in scope.excluded_apps]
    
    # Apply category filters (future)
    if scope.included_categories:
        filtered = [m for m in filtered if any(cat in m.categories for cat in scope.included_categories)]
    
    return filtered
```

## API Endpoints

### Permission Request Endpoint

```yaml
POST /sdk/permissions/request
Headers:
  X-Api-Key: developer_api_key
Body:
  requested_scope: MemoryScope
  scope_reason: string
  application_name: string
Response:
  permission_request_id: string
  authorization_url: string
```

### Permission Grant Endpoint

```yaml
POST /sdk/permissions/grant
Headers:
  Authorization: Bearer user_token
Body:
  permission_request_id: string
  granted_scope: MemoryScope
  modifications?: ScopeModifications
Response:
  access_token: string (scoped JWT)
  granted_permissions: PermissionDetails
```

### Permission Revocation

```yaml
POST /sdk/permissions/revoke
Headers:
  Authorization: Bearer user_token
Body:
  developer_api_key: string
  application_name: string
Response:
  status: "revoked"
  revoked_at: Date
```

## Security Considerations

### Permission Validation

1. **Minimum Access Requirement**: At least one memory source must be granted
2. **Scope Downgrading**: Users can only reduce, never expand requested scope
3. **Audit Trail**: All permission grants/modifications are logged
4. **Token Rotation**: Scoped tokens expire and must be refreshed
5. **Developer Verification**: API keys validated before permission requests

### Privacy Protection

```typescript
// Memory access is always filtered through permissions
const getMemoriesForApp = async (userId: string, token: string) => {
  const permissions = await validateAndParseToken(token);
  const allMemories = await fetchUserMemories(userId);
  
  // Critical: Apply permission filters
  const scopedMemories = await applyScopeFilter(
    allMemories, 
    permissions.scope,
    userId
  );
  
  // Additional privacy: Remove sensitive fields
  return scopedMemories.map(sanitizeMemory);
};
```

## User Dashboard Features

### Permission Management UI

Users can manage all granted permissions from their Jean Memory dashboard:

```
Active Application Permissions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MathTutor AI
Granted: August 1, 2025
Scope: All memories (modified)
Restrictions: Excluding personal_journal app
[View Details] [Modify] [Revoke]

TherapyBot Pro  
Granted: July 15, 2025
Scope: All memories
Restrictions: None
[View Details] [Modify] [Revoke]

Writing Assistant
Granted: July 1, 2025  
Scope: App-specific only
Restrictions: Only this app's memories
[View Details] [Modify] [Revoke]
```

## Future Enhancements

### Advanced Scoping Options

1. **Category-Based Access**: 
   - "Only professional memories"
   - "Only health-related memories"
   - "Exclude personal/family memories"

2. **Temporal Patterns**:
   - "Only memories from work hours"
   - "Only weekend memories"
   - "Memories from specific date ranges"

3. **Confidence Levels**:
   - "Only high-confidence memories"
   - "Include/exclude uncertain memories"

4. **Semantic Filtering**:
   - "Only positive memories"
   - "Exclude memories containing specific topics"

### Transaction Capabilities

Future data plane transactions:

```typescript
interface DataTransaction {
  type: "read" | "write" | "delete" | "share";
  scope: MemoryScope;
  conditions?: {
    requireUserConfirmation?: boolean;
    notificationRequired?: boolean;
    auditLogLevel?: "basic" | "detailed";
  };
}
```

## Implementation Phases

### Phase 1: Basic Scoping (MVP)
- `all_memories` scope
- `app_specific` scope  
- Basic permission UI
- Grant/deny functionality

### Phase 2: Advanced Controls
- Time-bounded access
- Application inclusion/exclusion
- Permission modification
- Revocation features

### Phase 3: Granular Filtering  
- Category-based filtering
- Custom scope definitions
- Advanced privacy controls
- Audit dashboard

### Phase 4: Smart Permissions
- ML-based permission recommendations
- Usage-based scope suggestions
- Anomaly detection for unusual access patterns
- Automated permission expiry

## Developer Guidelines

### Best Practices

1. **Request Minimum Necessary Scope**: Only ask for what you need
2. **Provide Clear Reasons**: Explain why you need each permission
3. **Handle Scope Reduction**: Gracefully degrade functionality
4. **Respect User Choice**: Never pressure for more permissions
5. **Cache Appropriately**: Don't repeatedly fetch same scoped data

### Example: Handling Reduced Permissions

```typescript
const initializeAgent = async (grantedScope: MemoryScope) => {
  if (grantedScope.type === "app_specific") {
    console.log("Limited to app-specific memories - some features may be limited");
    // Adjust UI to show limited feature set
  }
  
  if (grantedScope.restrictions?.time_boundary) {
    console.log(`Only accessing memories from ${grantedScope.restrictions.time_boundary} onwards`);
    // Adjust prompts to acknowledge temporal limitation
  }
  
  // Initialize with granted permissions
  return new JeanAgent({
    scope: grantedScope,
    onScopeViolation: (requested) => {
      // Handle when trying to access beyond granted scope
      showPermissionUpgradePrompt(requested);
    }
  });
};
```

## Success Metrics

1. **User Trust**: % of users granting full requested permissions
2. **Developer Satisfaction**: Average time to implement scoped access
3. **Permission Modifications**: % of users who modify default permissions
4. **Revocation Rate**: % of permissions revoked after initial grant
5. **Functionality Impact**: % of features working with reduced permissions

## Conclusion

The Data Plane Layer creates a sophisticated balance between user privacy and developer functionality. By giving users granular control over their data while providing developers with clear patterns for requesting access, we build a trusted ecosystem where both parties benefit. Users maintain sovereignty over their memories while developers can create powerful, personalized AI experiences with confidence.

This permission system positions Jean Memory as the privacy-respecting choice for AI memory infrastructure, setting a new standard for user control in the AI application ecosystem.