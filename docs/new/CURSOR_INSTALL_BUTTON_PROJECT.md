# Cursor One-Click Install Button Project

## Overview
Adding a Cursor deep link install button to the Jean Memory dashboard, similar to the modern MCP integration patterns used by Claude and other tools.

## Goal
Enable users to install Jean Memory MCP server to Cursor with a single click using Cursor's native deep link protocol: `cursor://anysphere.cursor-deeplink/mcp/install`. The installation must use the high-performance HTTP v2 transport.

## Final Implementation

### 1. Correct MCP Configuration
The core issue was a malformed MCP configuration object being Base64 encoded into the install link. The final, correct configuration uses the `stdio` transport with the `supergateway` command, pointing to the v2 backend endpoint.

**Correct Configuration (`stdio` transport):**
```json
{
  "command": "npx",
  "args": [
    "-y",
    "supergateway",
    "--stdio",
    "https://jean-memory-api-virginia.onrender.com/mcp/v2/cursor/${userId}"
  ]
}
```

**Incorrect Configuration (old `sse` transport):**
```json
{
  "jean-memory": {
    "command": "npx",
    "args": [
      "-y",
      "supergateway",
      "--sse",
      "https://api.jeanmemory.com/mcp/cursor/sse/${userId}"
    ]
  }
}
```

### 2. Code Fixes
The fix required updating two separate files that were generating the install link and manual command with incorrect data:
- `openmemory/ui/components/dashboard/InstallModal.tsx`
- `openmemory/ui/components/dashboard/Install.tsx`

Both files were updated to use the correct MCP configuration, backend URL (`https://jean-memory-api-virginia.onrender.com`), and transport protocol (`stdio` via `supergateway`).

### 3. Correct Manual Install Command
The manual install command displayed to users was also corrected to match the one-click install's configuration:
`npx -y supergateway --stdio https://jean-memory-api-virginia.onrender.com/mcp/v2/cursor/${userId}`

## User Experience
1. User goes to Jean Memory dashboard.
2. Clicks "Cursor" tab in installation section.
3. Sees blue "Add Jean Memory to Cursor" button.
4. Clicks button → Cursor opens and prompts to install a working tool.
5. Fallback: The manual command is now correct and also works.

## Current Status

### ✅ Completed
- Fixed `generateCursorDeepLink()` in both `Install.tsx` and `InstallModal.tsx`.
- Corrected the manual installation command generation.
- Ensured one-click install uses the performant HTTP v2 transport.
- The feature is now fully functional and deployed.

## Reference Documentation
- Cursor MCP Install Docs: https://docs.cursor.com/tools/developers
- Deep Link Format: `cursor://anysphere.cursor-deeplink/mcp/install?name=$NAME&config=$BASE64_CONFIG`