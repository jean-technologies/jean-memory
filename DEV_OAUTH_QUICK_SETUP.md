# Quick OAuth Setup for Dev Server

## ✅ What's Been Done
- OAuth code merged to `dev` branch
- Pushed to GitHub
- Render will auto-deploy to `jean-memory-api-dev`

## 📋 What You Need to Do

### 1. Add Environment Variable (Required)

Go to Render Dashboard → `jean-memory-api-dev` → Environment tab:

```
API_BASE_URL = https://jean-memory-api-dev.onrender.com
```

Click **Save Changes** and wait for redeploy (~2-3 minutes).

### 2. Run Tests

Once deployed, run the comprehensive test:

```bash
python test_dev_oauth_comprehensive.py
```

This will verify:
- ✅ OAuth endpoints work
- ✅ Existing MCP endpoints still work
- ✅ No breaking changes

### 3. Test OAuth Flow Manually

1. Visit in browser:
   ```
   https://jean-memory-api-dev.onrender.com/oauth/authorize?client_id=test&redirect_uri=https://test.com&response_type=code&state=123
   ```

2. You should see the authorization page

3. Enter a test API key (format: `jean_sk_xxxxx`)

### 4. Test with Claude

URL for Claude:
```
https://jean-memory-api-dev.onrender.com/mcp/oauth/{your_user_id}
```

## 🔍 Monitor During Testing

Watch logs in Render Dashboard:
- Look for: "Registered new OAuth client"
- Check for any errors
- Monitor MCP requests

## ⚠️ Important Notes

- **No Redis**: Tokens stored in memory (lost on restart)
- **Token Expiry**: 1 hour for access tokens
- **Auth Codes**: Expire in 10 minutes
- **Completely Isolated**: Won't affect existing auth

## 🚨 If Something Breaks

The OAuth implementation is completely isolated. If there are issues:
1. Check the specific OAuth endpoints
2. Existing MCP should still work fine
3. Check logs for specific errors

## ✅ Success Criteria

When all tests pass, you can:
1. Test with real Claude client
2. Plan production deployment
3. Add Redis for token persistence 