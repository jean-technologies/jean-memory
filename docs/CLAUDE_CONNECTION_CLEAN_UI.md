# Clean Claude Connection UI - OAuth Only

## Replace the entire connection dialog with:

---

### Connect to Claude

Jean Memory tracks your projects and builds a working memory.

---

### 🌐 Connect to Claude

**Add this URL to Claude's MCP settings:**

```
{{API_BASE_URL}}/mcp
```

**Setup Steps:**
1. Copy the URL above
2. In Claude: Settings → Feature Preview → Model Context Protocol
3. Add MCP server with the URL
4. Complete OAuth login when prompted
5. Start using Jean Memory in Claude!

**✨ Benefits:**
- ✅ Secure OAuth authentication  
- ✅ No API keys to manage
- ✅ Works on Claude web & mobile
- ✅ Automatic setup

---

**Your User ID:** `{{USER_ID}}`  
*Keep this for support if needed*

---

## Technical Notes:

- `{{API_BASE_URL}}` will be replaced with:
  - **Dev**: `https://jean-memory-api-dev.onrender.com`
  - **Production**: `https://jean-memory-api-virginia.onrender.com`
- Manual terminal setup has been removed - OAuth is the only option
- User ID is shown for support purposes only
- No more hardcoded URLs - environment-aware configuration

## Environment Variable Setup:

To override the auto-detected URL, set:
```bash
# Optional - will auto-detect if not set
API_BASE_URL=https://your-custom-url.com
```

Otherwise it auto-detects:
- `ENVIRONMENT=production` → Virginia server
- `ENVIRONMENT=development` → Dev server
