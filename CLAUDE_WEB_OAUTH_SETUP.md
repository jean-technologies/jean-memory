# 🔗 Connect Jean Memory to Claude Web App

## Quick Setup

### 1. Register Your OAuth Client

First, let's create a client for Claude:

```bash
curl -X POST https://jean-memory-api-dev.onrender.com/oauth/register \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Claude Web",
    "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"]
  }'
```

Save the `client_id` from the response.

### 2. Add MCP Server in Claude

1. Go to Claude Web App: https://claude.ai
2. Click your profile → Settings → Connected Tools
3. Click "Add MCP Server"
4. Enter these details:

   **Server URL:**
   ```
   https://jean-memory-api-dev.onrender.com/mcp/oauth/{your-user-id}
   ```
   
   Replace `{your-user-id}` with: `2282060d-5b91-437f-b068-a710c93bc040`

   **Full URL:**
   ```
   https://jean-memory-api-dev.onrender.com/mcp/oauth/2282060d-5b91-437f-b068-a710c93bc040
   ```

5. Claude will redirect you to authorize
6. Enter your Jean Memory API key
7. Click "Authorize"

### 3. Test It

Once connected, you can ask Claude to use Jean Memory:
- "Store a memory about my meeting today"
- "What do you remember about my preferences?"
- "Search my memories for project ideas"

## Troubleshooting

### If you see "Unsupported provider" error:
This is from Supabase/auth configuration, not OAuth. Your OAuth is working correctly.

### If authorization fails:
1. Make sure you're using your actual Jean Memory API key
2. Check that the client_id exists (run the registration curl command)
3. Verify the redirect URL matches exactly 