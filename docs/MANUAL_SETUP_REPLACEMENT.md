# Exact Replacement for "Need manual terminal setup instead?" Section

## Replace the current manual setup section with:

### ✅ Need Claude Web setup instead?

**For Claude Web & Mobile (Recommended):**

```
https://jean-memory-api-virginia.onrender.com/mcp
```

1. Copy the URL above
2. In Claude: Settings → MCP → Add Server  
3. Paste URL and complete OAuth login
4. Done! No terminal needed.

**Why use this?**
- ✅ Secure OAuth (no API keys)
- ✅ Works on web & mobile
- ✅ Automatic setup

---

### Current manual setup (Claude Desktop only):

```bash
npx -y supergateway --stdio https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/2282060d-5b91-437f-b068-a710c93bc040
```

Run this command in terminal, then restart Claude Desktop.
