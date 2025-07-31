# Claude Code Multi-Agent Security Requirements

## Overview

The Claude Code multi-agent coordination system includes powerful coordination tools that enable cross-terminal collaboration. **These tools must ONLY be available to Claude Code MCP clients** and never exposed to other MCP clients like Cursor, Chorus, ChatGPT, or API users.

## 🚨 Critical Security Rule

**ONLY Claude Code MCP connections may access coordination tools.**

All other MCP clients (Cursor, Chorus, ChatGPT, API users, Default profile) must be **completely blocked** from coordination tools.

## Security Implementation

### Client Detection Mechanism

**Header-Based Authentication:**
- Claude Code MCP sends: `x-client-name: 'claude'` ⭐ (CONFIRMED)
- Other clients send different values: `cursor`, `chorus`, etc.
- Detection happens in `app/routing/mcp.py`
- **Supported Claude Code variants**: `'claude'`, `'claude-code'`, `'claude code'`

### Authorization Flow

```
1. MCP Request → app/routing/mcp.py
   ├─ Extract x-client-name header
   ├─ Parse virtual user ID for session info
   └─ Pass client_name in session_info to client profile

2. Client Profile → app/clients/claude.py
   ├─ Check: is_multi_agent AND is_claude_code
   ├─ if TRUE: Add coordination tools to schema
   └─ if FALSE: Block tools + log security warning

3. Response → Claude Code or Other Client
   ├─ Claude Code: Gets coordination tools
   └─ Other clients: Get standard tools only
```

### Code Implementation

**In `app/routing/mcp.py`:**
```python
# Pass client name to profile for authorization
enhanced_session_info = session_info.copy()
enhanced_session_info["client_name"] = client_name_from_header
tools_schema = client_profile.get_tools_schema(
    include_annotations=(client_version == "2025-03-26"),
    session_info=enhanced_session_info
)
```

**In `app/clients/claude.py`:**
```python
# Security check before exposing coordination tools
client_name = session_info.get("client_name", "") if session_info else ""
is_claude_code = client_name.lower() in ["claude code", "claude-code", "claude"]

# Only add coordination tools for Claude Code
if is_multi_agent and is_claude_code:
    # Add all 5 coordination tools
elif is_multi_agent and not is_claude_code:
    logger.warning(f"🚨 SECURITY: Coordination tools blocked for: '{client_name}'")
```

## Tools Access Matrix

| Client Type | Jean Memory | Coordination Tools | Notes |
|-------------|-------------|-------------------|-------|
| **Claude Code MCP** | ✅ | ✅ (Multi-agent only) | Full access authorized |
| **Cursor IDE** | ✅ | ❌ | Standard tools only |
| **Chorus** | ✅ | ❌ | Standard tools only |
| **ChatGPT** | Search/Fetch only | ❌ | Custom tool set |
| **API Users** | Enhanced tools | ❌ | API-specific tools |
| **Default/Unknown** | ✅ | ❌ | Standard tools only |

## Coordination Tools (Claude Code Only)

### Planning Tools (Planner Agent Only)
- `analyze_task_conflicts` - Task analysis and agent distribution planning
- `create_task_distribution` - Terminal command and prompt generation

### Execution Tools (All Agents)
- `claim_file_lock` - Cross-session file locking
- `sync_progress` - Progress broadcasting across terminals
- `check_agent_status` - Agent monitoring

## Security Validation

### Testing Commands

**Test Claude Code (should show coordination tools):**
```bash
curl -X POST https://jean-memory-api-dev.onrender.com/mcp/v2/claude/test_user__session__test_session__planner \
  -H "Content-Type: application/json" \
  -H "x-client-name: claude" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}'
```

**Test Cursor (should NOT show coordination tools):**
```bash
curl -X POST https://jean-memory-api-dev.onrender.com/mcp/v2/cursor/test_user \
  -H "Content-Type: application/json" \
  -H "x-client-name: cursor" \
  -d '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}'
```

### Security Checklist

- [x] Claude Code MCP shows all coordination tools when in multi-agent session ✅
- [x] Cursor IDE connections show NO coordination tools ✅
- [x] Chorus connections show NO coordination tools ✅
- [x] ChatGPT connections show NO coordination tools ✅
- [x] API key users show NO coordination tools ✅
- [x] Default/unknown clients show NO coordination tools ✅
- [x] Security warnings logged for blocked attempts ✅
- [x] All client profiles tested individually ✅

### Log Monitoring

**Expected Security Logs:**
```
🔧 [CLAUDE PROFILE] client_name: 'claude', is_claude_code: True, is_multi_agent: True
🎯 Adding planner-specific coordination tools

🔧 [CLAUDE PROFILE] client_name: 'cursor', is_claude_code: False, is_multi_agent: False
🚨 SECURITY: Multi-agent coordination tools blocked for non-Claude Code client: 'cursor'
```

## Incident Response

### If Coordination Tools Appear in Wrong Client

1. **Immediate Action**: Investigate client detection logic
2. **Check**: `x-client-name` header values in logs
3. **Verify**: `is_claude_code` evaluation in `claude.py`
4. **Review**: Client inheritance chains for security bypass

### If Tools Missing from Claude Code

1. **Check**: Virtual user ID format (`user__session__session__agent`)
2. **Verify**: `x-client-name: 'claude code'` header
3. **Confirm**: `is_multi_agent` and `is_claude_code` both true
4. **Review**: Session info passing from routing to profile

## Security Updates

When modifying MCP functionality:

1. **Always check**: Does this change affect client tool exposure?
2. **Test all clients**: Verify security boundaries after any change
3. **Update docs**: Document security implications
4. **Review inheritance**: Check if new clients inherit from ClaudeProfile

## Contact

For security questions or incidents related to coordination tool exposure, escalate immediately to the development team.