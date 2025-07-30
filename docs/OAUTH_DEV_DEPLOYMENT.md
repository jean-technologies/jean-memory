# OAuth Dev Server Deployment Guide

## 🚀 Deployment Status

The clean OAuth implementation has been:
- ✅ Merged into `dev` branch
- ✅ Pushed to GitHub
- 🔄 Will auto-deploy to Render dev server

## 🔧 Environment Variables Required

Make sure these are set on the dev Render service:

```bash
API_BASE_URL=https://jean-memory-api-dev.onrender.com
JWT_SECRET_KEY=your-long-secure-server-secret-here-used-for-signing-all-jwts
```

**Note:** `JWT_SECRET_KEY` is a single server-wide secret used to sign ALL JWT tokens. User identity goes INSIDE the JWT payload, not in the signing key.

## 📋 What's New

### OAuth Endpoints
- `GET /.well-known/oauth-authorization-server` - OAuth discovery
- `GET /oauth/authorize` - Authorization page  
- `POST /oauth/token` - Token exchange
- `POST /oauth/register` - Client registration (dev only)

### New MCP Endpoint
- `POST /mcp` - Universal endpoint (no user ID!)
- `GET /mcp/health` - Health check with OAuth

### Backward Compatible
All existing endpoints continue to work:
- `/mcp/v2/{client}/{user_id}` - Existing tools like jean_memory
- `/mcp/messages/` - Standard MCP
- `/mcp/{client}/sse/{user_id}` - SSE endpoints

## 🧪 Testing

1. **Wait for deployment** (usually 2-5 minutes after push)

2. **Run test script**:
   ```bash
   python test_dev_oauth_clean.py
   ```

3. **Test with Claude**:
   - Use the authorization URL from test output
   - Add to Claude: `https://jean-memory-api-dev.onrender.com/mcp`

## 📊 Expected Results

- OAuth discovery returns proper metadata
- New `/mcp` endpoint requires Bearer token
- Existing endpoints still work with API keys
- No user IDs exposed in OAuth flow

## 🔍 Monitoring

Check Render logs for:
- `OAuth server startup`
- `Client registrations`
- `MCP requests with OAuth`

## 🚨 If Issues

1. Check environment variables are set
2. Verify JWT_SECRET_KEY is configured
3. Check Render build logs
4. Ensure all dependencies installed

## ✅ Success Criteria

- OAuth flow works end-to-end
- Claude can connect via OAuth
- Existing tools still work
- No user IDs in URLs! 