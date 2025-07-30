# OAuth Architecture Clarification

## 🚨 Important: Two Parallel Authentication Systems

We now have **TWO separate authentication methods** that work in parallel:

### 1. Existing API Key System (Still Works!)
```
URL: https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/2282060d-5b91-437f-b068-a710c93bc040
Auth: X-API-Key header
Users: All existing users, tools like jean_memory
```

### 2. New OAuth System (Additive)
```
URL: https://jean-memory-api-virginia.onrender.com/mcp
Auth: Bearer JWT token
Users: New OAuth-enabled clients like Claude web
```

## 🔑 JWT_SECRET_KEY Explained

**You're absolutely right!** `JWT_SECRET_KEY` is:
- ✅ **Server-wide secret** - ONE key for the entire server
- ✅ **Used to sign/verify tokens** - Not stored per-user
- ✅ **User identity is IN the JWT payload** - Not in the signing key

```bash
# Correct: Single server secret
JWT_SECRET_KEY=your-long-secure-server-secret-here

# The user info goes INSIDE the JWT:
{
  "sub": "2282060d-5b91-437f-b068-a710c93bc040",  # User ID here
  "email": "user@example.com",                     # User email here
  "client": "claude"                               # Client name here
}
```

## 🛣️ How They Connect (or Don't)

The OAuth flow does **NOT** magically enable existing endpoints. They are separate:

### Existing Flow (Unchanged)
1. User has API key
2. Uses URL: `/mcp/v2/claude/{user_id}` 
3. Sends `X-API-Key` header
4. ✅ Works exactly as before

### New OAuth Flow
1. User goes through OAuth in Claude
2. Gets JWT token
3. Uses URL: `/mcp` (no user ID!)
4. Sends `Authorization: Bearer {jwt}` header
5. ✅ New secure flow

## 🤔 The Confusion

Your existing setup:
```
https://jean-memory-api-virginia.onrender.com/mcp/v2/claude/2282060d-5b91-437f-b068-a710c93bc040
```

**This will continue to work with API keys!** 

The OAuth is for NEW connections where:
- User doesn't want to share API keys
- Claude web app wants proper OAuth
- More secure token-based auth

## 💡 Recommendation

For now, keep both systems:
1. **Existing users** - Keep using API key endpoints
2. **New Claude web users** - Use OAuth endpoint
3. **Future** - Gradually migrate to OAuth-only

The systems don't interfere with each other! 