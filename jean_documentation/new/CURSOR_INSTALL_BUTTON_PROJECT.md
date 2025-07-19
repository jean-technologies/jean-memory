# Cursor One-Click Install Button Project

## Overview
Adding a Cursor deep link install button to the Jean Memory dashboard, similar to the modern MCP integration patterns used by Claude and other tools.

## Goal
Enable users to install Jean Memory MCP server to Cursor with a single click using Cursor's native deep link protocol: `cursor://anysphere.cursor-deeplink/mcp/install`

## What We Were Trying To Do

### 1. Cursor Deep Link Implementation
- **File**: `openmemory/ui/components/dashboard/Install.tsx`
- **Function**: `generateCursorDeepLink()` 
- **Button**: Blue "Add Jean Memory to Cursor" button above manual install command
- **Protocol**: `cursor://anysphere.cursor-deeplink/mcp/install?name=jean-memory&config=BASE64_CONFIG`

### 2. MCP Configuration for Cursor
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

### 3. Expected User Experience
1. User goes to Jean Memory dashboard
2. Clicks "Cursor" tab in installation section
3. Sees blue "Add Jean Memory to Cursor" button
4. Clicks button → Cursor opens and prompts to install
5. Fallback: Manual `npx install-mcp` command still available

## Current Status

### ✅ Completed
- Added `generateCursorDeepLink()` function to Install.tsx
- Added blue install button with ExternalLink icon
- Imported ExternalLink from lucide-react
- Base64 encoding of MCP configuration
- Conditional rendering for Cursor tab only

### ❌ Blocked By Local Development Issues
- Backend won't start due to `pkg_resources` module errors
- Database schema mismatches causing 500 errors
- Admin security key requirements
- Integration sync field database errors

### 🎯 What We Need To Do
1. **Reset codebase** to clean state
2. **Deploy changes** to production (where they should work)
3. **Test on production** site at app.jeanmemory.com
4. **Fix local dev environment** separately (not blocking this feature)

## Implementation Details

### Changes Made
- **Install.tsx**: Added Cursor-specific deep link button
- **generateCursorDeepLink()**: Creates proper cursor:// protocol URLs
- **Conditional rendering**: `{appKey === "cursor" && (...)}`
- **Styling**: Blue button matching Cursor branding

### Files Modified
- `openmemory/ui/components/dashboard/Install.tsx`
- `openmemory/api/app/utils/gemini.py` (narrative improvements)
- `openmemory/api/app/settings.py` (logger fix)

## Next Steps
1. Reset local codebase to latest clean commit
2. Verify changes are in git history
3. Test on production deployment
4. Document working solution
5. Fix local dev environment as separate issue

## Reference Documentation
- Cursor MCP Install Docs: https://docs.cursor.com/tools/developers
- Jean Memory MCP Config: `manifest.json`
- Deep Link Format: `cursor://anysphere.cursor-deeplink/mcp/install?name=$NAME&config=$BASE64_CONFIG`