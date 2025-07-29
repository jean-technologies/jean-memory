"""
Minimal Claude OAuth Implementation

This provides OAuth 2.0 support with Dynamic Client Registration (DCR)
for Claude MCP integration. Completely isolated and additive.
"""

import os
import secrets
import time
from typing import Dict, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["claude-oauth"])

# Simple in-memory storage (use Redis in production)
memory_store = {
    "clients": {},      # Dynamically registered clients
    "auth_codes": {},   # Authorization codes
    "tokens": {}        # Access tokens
}

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com")
TOKEN_EXPIRY = 3600  # 1 hour

@router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth 2.0 discovery endpoint for Claude"""
    return {
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/oauth/authorize",
        "token_endpoint": f"{BASE_URL}/oauth/token",
        "registration_endpoint": f"{BASE_URL}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"]  # Public client
    }

@router.post("/oauth/register")
async def dynamic_client_registration(request: Request):
    """Dynamic Client Registration (RFC 7591) for Claude"""
    try:
        body = await request.json()
        
        # Generate unique client ID
        client_id = f"claude_{secrets.token_urlsafe(16)}"
        
        # Store client info
        memory_store["clients"][client_id] = {
            "client_name": body.get("client_name", "Claude"),
            "redirect_uris": body.get("redirect_uris", []),
            "grant_types": body.get("grant_types", ["authorization_code"]),
            "created_at": time.time()
        }
        
        logger.info(f"Registered new OAuth client: {client_id}")
        
        # Return registration response
        return {
            "client_id": client_id,
            "client_name": body.get("client_name", "Claude"),
            "redirect_uris": body.get("redirect_uris", []),
            "grant_types": body.get("grant_types", ["authorization_code"]),
            "token_endpoint_auth_method": "none"  # Public client
        }
        
    except Exception as e:
        logger.error(f"Client registration failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid registration request")

@router.get("/oauth/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    state: str,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256"
):
    """OAuth authorization endpoint"""
    
    # Validate client
    if client_id not in memory_store["clients"]:
        raise HTTPException(status_code=400, detail="Invalid client")
    
    # Validate response type
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response type")
    
    # Store auth session
    session_id = secrets.token_urlsafe(16)
    memory_store["auth_codes"][session_id] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": time.time()
    }
    
    # Return simple authorization page
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Connect Claude to Jean Memory</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 2rem;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                max-width: 400px;
                width: 100%;
            }}
            h2 {{ margin: 0 0 1rem 0; }}
            input {{
                width: 100%;
                padding: 0.75rem;
                margin: 0.5rem 0 1rem 0;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
            }}
            button {{
                width: 100%;
                padding: 0.75rem;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 1rem;
            }}
            button:hover {{ background: #0056b3; }}
            .info {{ color: #666; font-size: 0.875rem; margin-top: 1rem; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🧠 Connect Claude to Jean Memory</h2>
            <p>Enter your Jean Memory API key to authorize Claude:</p>
            <form method="post" action="/oauth/callback">
                <input type="hidden" name="session_id" value="{session_id}">
                <label for="api_key">API Key:</label>
                <input type="password" name="api_key" id="api_key" 
                       placeholder="jean_sk_..." required 
                       pattern="jean_sk_.*">
                <button type="submit">Authorize</button>
            </form>
            <p class="info">
                Get your API key from 
                <a href="https://jeanmemory.com/settings" target="_blank">Jean Memory Settings</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)

@router.post("/oauth/callback")
async def process_authorization(
    session_id: str = Form(...),
    api_key: str = Form(...)
):
    """Process authorization and redirect with code"""
    
    # Validate session
    session = memory_store["auth_codes"].get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    # Validate API key format
    if not api_key.startswith("jean_sk_"):
        raise HTTPException(status_code=400, detail="Invalid API key")
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store auth code with API key
    memory_store["auth_codes"][auth_code] = {
        **session,
        "api_key": api_key,
        "used": False
    }
    
    # Clean up session
    del memory_store["auth_codes"][session_id]
    
    # Redirect back to Claude
    params = {
        "code": auth_code,
        "state": session["state"]
    }
    redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
    
    return RedirectResponse(url=redirect_url, status_code=302)

@router.post("/oauth/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    client_id: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None)
):
    """OAuth token endpoint"""
    
    if grant_type == "authorization_code":
        # Validate code
        if not code or code not in memory_store["auth_codes"]:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        auth_data = memory_store["auth_codes"][code]
        
        # Check if already used
        if auth_data.get("used"):
            raise HTTPException(status_code=400, detail="Authorization code already used")
        
        # Validate client and redirect URI
        if auth_data["client_id"] != client_id:
            raise HTTPException(status_code=400, detail="Invalid client")
        
        if redirect_uri and auth_data["redirect_uri"] != redirect_uri:
            raise HTTPException(status_code=400, detail="Invalid redirect URI")
        
        # TODO: Validate PKCE code_verifier if provided
        # For now, we'll skip PKCE validation for simplicity
        
        # Mark code as used
        auth_data["used"] = True
        
        # Generate tokens
        access_token = f"jean_oauth_{secrets.token_urlsafe(32)}"
        refresh_token_value = f"jean_refresh_{secrets.token_urlsafe(32)}"
        
        # Store tokens
        memory_store["tokens"][access_token] = {
            "api_key": auth_data["api_key"],
            "client_id": client_id,
            "expires_at": time.time() + TOKEN_EXPIRY
        }
        
        memory_store["tokens"][refresh_token_value] = {
            "api_key": auth_data["api_key"],
            "client_id": client_id,
            "type": "refresh",
            "expires_at": time.time() + (30 * 24 * 3600)  # 30 days
        }
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY,
            "refresh_token": refresh_token_value
        }
    
    elif grant_type == "refresh_token":
        # Validate refresh token
        if not refresh_token or refresh_token not in memory_store["tokens"]:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        
        token_data = memory_store["tokens"][refresh_token]
        
        if token_data.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")
        
        if time.time() > token_data["expires_at"]:
            raise HTTPException(status_code=400, detail="Refresh token expired")
        
        # Generate new access token
        new_access_token = f"jean_oauth_{secrets.token_urlsafe(32)}"
        
        memory_store["tokens"][new_access_token] = {
            "api_key": token_data["api_key"],
            "client_id": token_data["client_id"],
            "expires_at": time.time() + TOKEN_EXPIRY
        }
        
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXPIRY
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant type")

@router.post("/mcp/oauth/{user_id}")
async def claude_mcp_endpoint(user_id: str, request: Request):
    """MCP endpoint that accepts OAuth tokens"""
    
    # Extract OAuth token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Validate token
    token_data = memory_store["tokens"].get(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check expiry
    if time.time() > token_data.get("expires_at", 0):
        raise HTTPException(status_code=401, detail="Token expired")
    
    # Get API key from token
    api_key = token_data["api_key"]
    
    # Now use existing MCP handler with the API key
    from starlette.datastructures import MutableHeaders
    from app.routing.mcp import handle_request_logic
    from fastapi import BackgroundTasks
    
    # Add API key to headers
    headers = MutableHeaders(request.headers)
    headers["x-api-key"] = api_key
    headers["x-user-id"] = user_id
    headers["x-client-name"] = "claude"
    
    # Create modified request
    request._headers = headers
    
    # Process with existing MCP logic
    body = await request.json()
    background_tasks = BackgroundTasks()
    
    return await handle_request_logic(request, body, background_tasks)

# Utility function for cleaning expired tokens (call periodically)
def cleanup_expired_tokens():
    """Remove expired tokens from memory"""
    current_time = time.time()
    
    # Clean auth codes older than 10 minutes
    expired_codes = [
        code for code, data in memory_store["auth_codes"].items()
        if current_time - data.get("created_at", 0) > 600
    ]
    for code in expired_codes:
        del memory_store["auth_codes"][code]
    
    # Clean expired tokens
    expired_tokens = [
        token for token, data in memory_store["tokens"].items()
        if current_time > data.get("expires_at", 0)
    ]
    for token in expired_tokens:
        del memory_store["tokens"][token]
    
    if expired_codes or expired_tokens:
        logger.info(f"Cleaned up {len(expired_codes)} auth codes and {len(expired_tokens)} tokens") # OAuth deployment trigger
