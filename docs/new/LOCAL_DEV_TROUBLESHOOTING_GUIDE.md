# Local Development Troubleshooting Guide

**Version**: 2.0  
**Date**: July 28, 2025  
**Context**: Updated after production incident to include critical safety learnings

---

## 1. Overview: Common Local Development Issues

When setting up Jean Memory for local development, developers typically encounter four main issues that prevent the `@jean_memory` tool from appearing in Claude Desktop. These issues must be resolved in order.

**The Golden Rule**: Always check the API server logs from `make -C openmemory dev` before debugging client connections.

---

## 2. Critical Backend Fixes

### Bug #1: Incorrect Python Path in Makefile

*   **Symptom**: `make -C openmemory dev` outputs `/bin/sh: python: command not found`. API server never starts.
*   **Root Cause**: Makefile uses generic `python` command which doesn't resolve in shell PATH.
*   **Fix**: Update Makefile to use explicit path to virtual environment Python.

    **File**: `openmemory/Makefile`
    ```makefile
    _start-servers:
    \t@{ \\
    \t\tcd api && ../../.venv/bin/python -m uvicorn main:app --reload --port 8765 --host 0.0.0.0 & \\
    \t\tAPI_PID=$$!; \\
    ```

### Bug #2: Missing Database Role

*   **Symptom**: Server starts but fails with `FATAL: role "jean_memory" does not exist`.
*   **Root Cause**: Local Supabase doesn't create the required `jean_memory` database role.
*   **Fix**: Add migration to create the role.

    **File**: `openmemory/supabase/migrations/20250728000000_add_jean_memory_role.sql`
    ```sql
    DO
    $$
    BEGIN
       IF NOT EXISTS (
          SELECT FROM pg_catalog.pg_roles
          WHERE  rolname = 'jean_memory') THEN
    
          CREATE ROLE jean_memory WITH LOGIN PASSWORD 'memory_password';
       END IF;
    END
    $$;
    
    GRANT ALL PRIVILEGES ON DATABASE postgres TO jean_memory;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO jean_memory;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO jean_memory;
    GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO jean_memory;
    GRANT CONNECT ON DATABASE postgres TO jean_memory;
    ```

### Bug #3: pgvector Extension Not Installed

*   **Symptom**: Server runs but logs show `Extension Installed: False`. Tools don't appear.
*   **Root Cause**: Migration uses incorrect syntax for Supabase extensions.
*   **Fix**: Update initial schema to use `with schema extensions`.

    **File**: `openmemory/supabase/migrations/20250101000000_initial_schema.sql`
    ```sql
    -- Enable UUID extension
    create extension if not exists "uuid-ossp" with schema extensions;
    
    -- Enable pg_vector extension for document chunks embeddings
    create extension if not exists vector with schema extensions;
    
    -- Enable pg_graphql extension for GraphQL support
    create extension if not exists pg_graphql with schema extensions;
    ```

### Bug #4: Missing get_tools_schema() Implementation

*   **Symptom**: Server healthy but MCP client can't list tools (`NotImplementedError`).
*   **Root Cause**: Base class raises `NotImplementedError` for `get_tools_schema()`.
*   **Fix**: Provide working default implementation in base class.

    **File**: `openmemory/api/app/clients/base.py`
    ```python
    def get_tools_schema(self, include_annotations: bool = False) -> List[Dict[str, Any]]:
        from app.config.tool_config import get_tools_for_client
        
        # Determine client name from class name
        client_name = 'default'
        if 'Claude' in self.__class__.__name__:
            client_name = 'claude'
        elif 'API' in self.__class__.__name__:
            client_name = 'api'
        
        # Get tool definitions from centralized config
        tool_defs = get_tools_for_client(client_name)
        
        # Convert to schema format expected by MCP
        schema_tools = []
        for tool_def in tool_defs:
            if hasattr(tool_def, 'name') and hasattr(tool_def, 'description'):
                schema_tool = {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "inputSchema": getattr(tool_def, 'inputSchema', {})
                }
                if include_annotations and hasattr(tool_def, 'annotations'):
                    schema_tool["annotations"] = tool_def.annotations
                schema_tools.append(schema_tool)
        
        return schema_tools
    ```

---

## 3. ⚠️ Critical Production Safety Learning

**NEVER Override get_tools_schema() in Client Profiles**

During debugging, we initially tried adding `get_tools_schema()` directly to `ClaudeProfile`. This caused a **production outage** because:

1. **Centralized Configuration Exists**: `CLIENT_TOOL_CONFIG` defines which tools each client should see
2. **Claude Gets Limited Tools**: Only `jean_memory` and `store_document`, not the full API toolset
3. **Hardcoded Schemas Break Production**: Bypasses the established tool configuration system

**The Correct Approach**: 
- ✅ Fix the base class to provide working defaults
- ❌ Never override `get_tools_schema()` in individual client profiles
- ✅ Let the centralized configuration system handle tool selection

---

## 4. Client Configuration

For Claude Desktop with `supergateway`:

```json
{
  "mcpServers": {
    "localhost": {
      "command": "npx",
      "args": [
        "-y",
        "supergateway",
        "--sse",
        "http://localhost:8765/mcp/claude/sse/00000000-0000-0000-0000-000000000000"
      ]
    }
  }
}
```

---

## 5. Debugging Workflow

1. **Apply All Backend Fixes**: Ensure all four bugs above are fixed
2. **Reset Database**: `make -C openmemory db-reset` 
3. **Start Server**: `make -C openmemory dev`
4. **Verify Success Indicators**:
   - No `python: command not found`
   - No `role "jean_memory" does not exist`  
   - Logs show `Extension Installed: True`
   - No `NotImplementedError` in MCP calls
5. **Connect Client**: Only after server is healthy

---

## 6. Expected Tools for Claude

Claude should see exactly these tools from `CLIENT_TOOL_CONFIG["claude"]`:
- `jean_memory` (primary orchestration tool)
- `store_document` (document storage)

If you see other tools like `add_memories`, `search_memory_v2`, etc., the centralized configuration is being bypassed - this indicates a bug.