# JWT Deep Dive - What's Really Happening

## 🔑 JWT_SECRET_KEY Explained

### What is it?
```bash
# A long, random, server-side secret - like a master password
JWT_SECRET_KEY=hsdf89h23f9h2f3h9f23hf92h3f9h23f9h2f3h9f23hf92h3f9h2f3h9f23hf92h3f
```

### Where do you get it?
Generate it once:
```bash
# Option 1: Use existing admin secret
JWT_SECRET_KEY=$ADMIN_SECRET_KEY

# Option 2: Generate new one
openssl rand -hex 64
# OR
python3 -c "import secrets; print(secrets.token_hex(64))"
```

### What's its purpose?
Think of it like a **signature stamp**:

1. **When creating JWT** (user logs in):
   ```python
   # Server creates token with user info + signs with secret
   token = jwt.encode({
       "sub": "user-123",
       "email": "user@example.com"
   }, JWT_SECRET_KEY)
   ```

2. **When validating JWT** (every request):
   ```python
   # Server verifies signature with same secret
   payload = jwt.decode(token, JWT_SECRET_KEY)
   # If signature invalid = token was forged = reject
   ```

**Key point**: Without the secret, you can't create valid tokens. This prevents forgery.

## 🔄 The Complete OAuth Flow

### Step 1: User Initiates Connection in Claude
```
User in Claude: "Add MCP Server"
URL: https://jean-memory-api-dev.onrender.com/mcp
```

### Step 2: Claude Discovers OAuth
```http
GET /.well-known/oauth-authorization-server
Response: {
  "authorization_endpoint": "/oauth/authorize",
  "token_endpoint": "/oauth/token"
}
```

### Step 3: Claude Redirects to Authorization
```http
GET /oauth/authorize?client_id=claude_abc123&redirect_uri=...
```

### Step 4: User Logs Into Jean Memory
Our server shows login page → user enters Jean Memory credentials

### Step 5: Generate Authorization Code
```python
# After successful login, we generate a code
auth_code = "temp_code_xyz789"
# Store: auth_codes[auth_code] = {user_id: "user-123", email: "user@test.com"}
```

### Step 6: Redirect Back to Claude
```http
HTTP/1.1 302 Found
Location: https://claude.ai/callback?code=temp_code_xyz789&state=...
```

### Step 7: Claude Exchanges Code for Token
```http
POST /oauth/token
{
  "grant_type": "authorization_code",
  "code": "temp_code_xyz789",
  "client_id": "claude_abc123"
}

Response: {
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer"
}
```

### Step 8: Claude Stores JWT Token
Claude now has: `eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

When decoded, this contains:
```json
{
  "sub": "user-123",           // The actual user ID!
  "email": "user@test.com",
  "client": "claude",
  "exp": 1234567890
}
```

## 🔌 How MCP Requests Work Now

### Before (URL-based):
```http
POST /mcp/v2/claude/user-123
X-API-Key: user_api_key_here
{
  "jsonrpc": "2.0",
  "method": "search_memory",
  "params": {"query": "test"}
}
```

### After (JWT-based):
```http
POST /mcp
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
{
  "jsonrpc": "2.0", 
  "method": "search_memory",
  "params": {"query": "test"}
}
```

## 🧠 Memory Search - No Constant Lookups!

You're worried about performance, but it's actually simple:

```python
@router.post("/mcp")
async def unified_mcp_endpoint(
    request: Request,
    user: OAuthUser = Depends(get_current_user)  # JWT decoded HERE
):
    # user.user_id = "user-123" (extracted from JWT)
    # user.email = "user@test.com" 
    # user.client = "claude"
    
    # Now we know who this is! Use existing memory logic:
    memories = search_memories(user_id=user.user_id, query="test")
    
    # Same backend code, just different source of user_id
```

**No database lookups for JWT → user_id**. The user_id IS IN the JWT!

## 🤔 Why This Change?

### Before (Security Issues):
- User ID exposed in URL: `/mcp/v2/claude/user-123` 
- Anyone can see/guess user IDs
- API keys in headers (less secure)

### After (More Secure):
- User ID hidden in encrypted JWT token
- No exposed user information
- Standard OAuth 2.0 (industry best practice)

## 🚨 Your Concerns Addressed

### "How does /mcp know who it's talking to?"
The JWT token in the `Authorization: Bearer` header contains the user ID:

```python
# JWT middleware automatically decodes token
headers = {"Authorization": "Bearer eyJ0eXAi..."}
decoded = jwt.decode(token, JWT_SECRET_KEY)
user_id = decoded["sub"]  # "user-123"
```

### "Will we need constant JWT lookups?"
No! JWT decoding is:
- ✅ **Fast** (milliseconds, no database)
- ✅ **Stateless** (no server storage needed)  
- ✅ **One decode per request** (not constant)

### "How do we search memories?"
Exactly the same as before:

```python
# Before: user_id from URL parameter
user_id = path_params["user_id"]  # "user-123"
memories = search_memories(user_id)

# After: user_id from JWT token  
user_id = jwt_payload["sub"]      # "user-123" 
memories = search_memories(user_id)  # SAME FUNCTION!
```

## 🎯 The Path Forward

1. **Existing system keeps working** - no changes needed for your current setup
2. **New OAuth system** provides secure alternative
3. **Same memory operations** - just different authentication
4. **Better security** - no exposed user IDs

The core Jean Memory functionality is unchanged. We're just changing HOW we identify users (JWT vs URL params). 