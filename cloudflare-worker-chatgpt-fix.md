# ChatGPT SSE Connection Fix - Cloudflare Worker Required

## Problem Summary
ChatGPT requires a Cloudflare Worker proxy because:
1. **ChatGPT POSTs to the SSE endpoint** - Our backend only accepts GET to `/mcp/chatgpt/sse/{user_id}`
2. **SSE formatting issue** - The current api.jeanmemory.com adds indentation to SSE data fields, breaking the spec
3. **Session management** - ChatGPT needs persistent sessions via Durable Objects

## Logs Showing the Issue
```
[POST] 405 jean-memory-api-virginia.onrender.com/mcp/chatgpt/sse/2822dc63-74a4-4ba1-b406-166352591123
INFO: 52.176.139.188:0 - "POST /mcp/chatgpt/sse/2822dc63-74a4-4ba1-b406-166352591123 HTTP/1.1" 405 Method Not Allowed
```

## Solution: Deploy Cloudflare Worker

The Cloudflare Worker (in `docs/new/latest/cloudflare-worker-updated.ts`) handles:
- **POST to SSE**: Accepts both GET and POST to `/sse` endpoint
- **Proper SSE formatting**: No indentation in `data:` fields
- **Durable Objects**: Maintains persistent sessions

### Key Code from Worker:
```typescript
// Handles both GET and POST to SSE
if (path === "/sse" && request.method === "GET") {
  return this.handleSseRequest(request);
} else if (path === "/sse" && request.method === "POST") {
  return this.handlePostMessage(request);  // <-- Critical for ChatGPT
}

// Proper SSE formatting
const endpointEvent = `event: endpoint\ndata: ${endpointPath}\n\n`;
// NOT: `event: endpoint\n          data: ${endpointPath}\n\n`
```

## Deployment Steps

### 1. Create Cloudflare Worker Project
```bash
mkdir cloudflare-mcp-proxy
cd cloudflare-mcp-proxy
npm init -y
npm install wrangler --save-dev
```

### 2. Create wrangler.toml
```toml
name = "jean-memory-mcp"
main = "src/index.ts"
compatibility_date = "2024-06-01"

[env.production]
vars = { BACKEND_URL = "https://jean-memory-api-virginia.onrender.com" }

[[durable_objects.bindings]]
name = "MCP_SESSION"
class_name = "McpSession"

[[migrations]]
tag = "v1"
new_classes = ["McpSession"]
```

### 3. Copy Worker Files
- Copy `docs/new/latest/cloudflare-worker-updated.ts` to `src/index.ts`
- Split the McpSession class into `src/mcp-session.ts`

### 4. Deploy
```bash
npx wrangler login
npx wrangler deploy --env production
```

### 5. Configure Custom Domain
In Cloudflare Dashboard:
1. Go to Workers & Pages
2. Select your worker
3. Settings → Triggers → Custom Domains
4. Add: `api.jeanmemory.com` (or a subdomain like `mcp.jeanmemory.com`)

## Testing

### Test Direct Backend (FAILS):
```bash
# This will return 405 Method Not Allowed
curl -X POST https://jean-memory-api-virginia.onrender.com/mcp/chatgpt/sse/USER_ID
```

### Test Cloudflare Worker (WORKS):
```bash
# After deployment, this should work
curl -X POST https://api.jeanmemory.com/mcp/chatgpt/sse/USER_ID
```

## Why This Worked Before

Looking at commit `8c3374bf` from the old repository, the Cloudflare Worker was properly deployed and handling:
1. ChatGPT-specific routing
2. POST to SSE conversion
3. Proper SSE formatting

The issue now is that either:
- The Cloudflare Worker isn't deployed
- Or it's deployed but misconfigured/outdated

## Immediate Action Required

1. **Check Cloudflare Dashboard** - Is there a worker deployed at api.jeanmemory.com?
2. **Update/Deploy Worker** - Use the code from `docs/new/latest/cloudflare-worker-updated.ts`
3. **Test ChatGPT Connection** - Use the Cloudflare URL, not direct backend