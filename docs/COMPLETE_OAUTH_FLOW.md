# Complete OAuth Flow & Connection Deep Dive

## 🎯 TL;DR - Simple Claude Web Integration

**We built a minimal OAuth implementation that Claude Web expects.**

Based on official Anthropic documentation:
https://help.anthropic.com/en/articles/8996230-getting-started-with-custom-connectors

Key components:
- **OAuth Discovery**: `/.well-known/oauth-authorization-server`
- **MCP Server**: `/mcp` with Bearer token authentication  
- **Same MCP Logic**: Routes to existing `handle_request_logic`

Then we inject it into the SAME headers and use the SAME MCP logic!

## 🔄 Step-by-Step OAuth Flow

### 1. 🚀 User Adds MCP Server in Claude
```
User action: "Add MCP Server" 
URL entered: {{API_BASE_URL}}/mcp
```

**Environment-aware URLs:**
- **Dev**: `https://jean-memory-api-dev.onrender.com/mcp`
- **Production**: `https://jean-memory-api-virginia.onrender.com/mcp`

### 2. 🔍 Claude Discovers OAuth (Automatic)
```http
GET /.well-known/oauth-authorization-server

Response:
{
  "authorization_endpoint": "https://jean-memory-api-dev.onrender.com/oauth/authorize",
  "token_endpoint": "https://jean-memory-api-dev.onrender.com/oauth/token"
}
```

### 3. 🔐 Claude Initiates Authorization
```http
GET /oauth/authorize?client_id=claude_xyz&redirect_uri=https://claude.ai/callback&response_type=code&state=abc123
```

### 4. 👤 User Logs Into Jean Memory
Our server shows login form → User enters their Jean Memory email/password

### 5. 🎫 Generate Authorization Code
```python
# After successful login:
auth_code = "temp_auth_xyz789"
auth_sessions[auth_code] = {
    "user_id": "2282060d-5b91-437f-b068-a710c93bc040",  # YOUR actual user ID!
    "email": "you@example.com",
    "client_id": "claude_xyz"
}
```

### 6. ↩️ Redirect Back to Claude
```http
HTTP/1.1 302 Found
Location: https://claude.ai/callback?code=temp_auth_xyz789&state=abc123
```

### 7. 🔄 Claude Exchanges Code for JWT Token
```http
POST /oauth/token
{
  "grant_type": "authorization_code", 
  "code": "temp_auth_xyz789",
  "client_id": "claude_xyz"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIyMjgyMDYwZC01YjkxLTQzN2YtYjA2OC1hNzEwYzkzYmMwNDAiLCJlbWFpbCI6InlvdUBleGFtcGxlLmNvbSIsImNsaWVudCI6ImNsYXVkZSIsImV4cCI6MTYzNDU2Nzg5MH0.signature",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

When that JWT is decoded, it contains:
```json
{
  "sub": "2282060d-5b91-437f-b068-a710c93bc040",  // YOUR user ID!
  "email": "you@example.com",
  "client": "claude", 
  "exp": 1634567890
}
```

### 8. 💾 Claude Stores JWT Token
Claude now has your JWT token and will include it in every MCP request.

## 🔌 How MCP Requests Actually Work

### When Claude Makes an MCP Request:

```http
POST /mcp
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "search_memory", 
  "params": {"query": "remember my meeting tomorrow"},
  "id": 1
}
```

### Here's What Happens In Our Code:

#### Step 1: JWT Middleware Decodes Token
```python
# app/oauth/middleware.py - get_current_user()
credentials = request.headers["authorization"]  # "Bearer eyJ0eXAi..."
token = credentials.replace("Bearer ", "")
payload = jwt.decode(token, JWT_SECRET_KEY)  # Decode with server secret

user = OAuthUser(
    user_id=payload["sub"],      # "2282060d-5b91-437f-b068-a710c93bc040"
    email=payload["email"],      # "you@example.com" 
    client=payload["client"],    # "claude"
    scope=payload["scope"]       # "read write"
)
```

#### Step 2: Inject User Info Into Headers
```python
# app/routers/mcp_oauth.py - unified_mcp_endpoint()
headers = MutableHeaders(request.headers)
headers["x-user-id"] = user.user_id        # "2282060d-5b91-437f-b068-a710c93bc040"
headers["x-user-email"] = user.email       # "you@example.com"
headers["x-client-name"] = user.client     # "claude"

request._headers = headers  # Modify request with user info
```

#### Step 3: Call Existing MCP Logic
```python
# Same function used by /mcp/v2/claude/{user_id} endpoints!
response = await handle_request_logic(request, body, background_tasks)
```

#### Step 4: Existing MCP Logic Sees Headers
```python
# app/routing/mcp.py - handle_request_logic()
user_id_from_header = request.headers.get("x-user-id")        # "2282060d-5b91-437f-b068-a710c93bc040"
client_name_from_header = request.headers.get("x-client-name") # "claude"

# Set context variables (same as before!)
user_token = user_id_var.set(user_id_from_header)
client_token = client_name_var.set(client_name_from_header)

# Get client profile and process MCP method (same as before!)
client_profile = get_client_profile(client_name_from_header)
# ... rest of existing MCP logic
```

## 🧠 Memory Search - Exact Same Logic!

When you search memories, it works identically:

### Before (URL-based):
```python
# URL: /mcp/v2/claude/2282060d-5b91-437f-b068-a710c93bc040
user_id = path_params["user_id"]  # "2282060d-5b91-437f-b068-a710c93bc040"
memories = search_user_memories(user_id, query="meeting tomorrow")
```

### After (JWT-based):  
```python
# URL: /mcp, JWT: {"sub": "2282060d-5b91-437f-b068-a710c93bc040"}
user_id = request.headers["x-user-id"]  # "2282060d-5b91-437f-b068-a710c93bc040"  
memories = search_user_memories(user_id, query="meeting tomorrow")  # SAME FUNCTION!
```

**It's the exact same `search_user_memories` function with the exact same user ID!**

## 🔑 JWT_SECRET_KEY - Generate It Now

```bash
# Generate a secure secret (run this once):
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(64))"

# Example output:
JWT_SECRET_KEY=a8f5f167f44f4964e6c998dee827110c62e77e4f5d2e72b8f0baadf5b2c8b51c3c8a8d1f9f2e8b3c7d6e4f1a9b8c5d0e2f7a6b1c8d9e5f4a3b0c9d8f7e6b2a1c5d8f3b6e9c0a7b4c1d6f2e3b8a5c9e2f1c8d7b0a3e6f9c5b8d1e2a7c4f0b3e6
```

Add this to your Render environment variables.

## 🚨 Connection & Session Management

### "How is the connection held?"
It's **stateless**! No persistent connections:

1. **Claude stores the JWT token** (client-side)
2. **Every MCP request includes the token** in Authorization header
3. **Our server validates token on each request** (no session storage needed)
4. **JWT contains all user info** (no database lookups)

### "How does it know who it's talking to?"
The JWT token IS the identity:
```
JWT payload = {
  "sub": "YOUR_ACTUAL_USER_ID",
  "email": "YOUR_EMAIL", 
  "client": "claude"
}
```

Every request decodes this token → extracts your user ID → uses existing memory functions.

## 🎯 Your Concerns - Answered

### ❓ "We've never built OAuth connection before"
**Correct!** But we're not changing the MCP system. We're just changing authentication from:
- URL params (`/claude/{user_id}`) → JWT headers (`Authorization: Bearer`)

### ❓ "It won't know who it's talking with"  
**Wrong!** The JWT contains your exact user ID: `"sub": "2282060d-5b91-437f-b068-a710c93bc040"`

### ❓ "How do we search memories by JWT?"
**Same function!** We extract user_id from JWT, then call `search_user_memories(user_id)` - identical to before.

### ❓ "Constant JWT lookups?"
**No database!** JWT decode is pure computation (milliseconds). No storage/lookups needed.

## 🚀 Path Forward

1. **Your existing setup keeps working** (`/mcp/v2/claude/{user_id}` with API keys)
2. **New OAuth provides secure alternative** (`/mcp` with JWT tokens)  
3. **Same Jean Memory functionality** - just different authentication
4. **Set JWT_SECRET_KEY** environment variable
5. **Test with Claude** using OAuth flow

The beauty is: **we're not breaking anything**. Your current setup continues working while providing a secure OAuth option for new users! 