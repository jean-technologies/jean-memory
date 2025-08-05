# Jean Memory MCP Cloudflare Worker

This Cloudflare Worker is **REQUIRED** for ChatGPT integration. It handles protocol conversion and SSE stream management that ChatGPT requires.

## Why This Worker is Necessary

1. **ChatGPT POSTs to SSE endpoint** - Our backend only accepts GET, but ChatGPT sends POST
2. **SSE Format Compliance** - Ensures proper SSE formatting without indentation
3. **Session Persistence** - Uses Durable Objects to maintain connection state
4. **Protocol Translation** - Converts between ChatGPT's expected format and our backend

## Quick Deploy

```bash
# Install dependencies
npm install

# Login to Cloudflare
npx wrangler login

# Deploy to production
npm run deploy
```

## Configuration

Edit `wrangler.toml` to set your backend URL:
```toml
[env.production]
vars = { BACKEND_URL = "https://jean-memory-api-virginia.onrender.com" }
```

## Testing

### Test SSE endpoint (GET and POST both work):
```bash
# GET request (standard SSE)
curl -N https://your-worker.workers.dev/mcp/chatgpt/sse/USER_ID

# POST request (ChatGPT style)
curl -X POST https://your-worker.workers.dev/mcp/chatgpt/sse/USER_ID
```

### Test messages endpoint:
```bash
curl -X POST https://your-worker.workers.dev/mcp/chatgpt/messages/USER_ID \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

## Custom Domain Setup

1. Deploy the worker first
2. In Cloudflare Dashboard → Workers & Pages → Your Worker
3. Settings → Triggers → Custom Domains
4. Add your domain (e.g., `api.jeanmemory.com`)

## Monitoring

```bash
# View real-time logs
npm run tail

# Check deployment status
npx wrangler deployments list
```

## Supported Endpoints

- `/mcp/chatgpt/sse/{user_id}` - ChatGPT SSE (GET/POST)
- `/mcp/chatgpt/messages/{user_id}` - ChatGPT messages
- `/mcp/claude/sse/{user_id}` - Claude SSE
- `/mcp/claude/messages/{user_id}` - Claude messages
- `/mcp/chorus/sse/{user_id}` - Chorus SSE
- `/mcp/chorus/messages/{user_id}` - Chorus messages

## Troubleshooting

### "Method not allowed" errors
- Make sure you're using the Cloudflare Worker URL, not the direct backend
- The backend returns 405 for POST to SSE, but the worker handles it

### SSE formatting issues
- Check the worker logs for malformed responses
- Ensure no proxy is adding indentation to SSE data fields

### Connection drops
- Check Durable Object state in Cloudflare Dashboard
- Verify keep-alive messages are being sent (45-second intervals)