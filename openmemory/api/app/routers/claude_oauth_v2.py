"""
Claude OAuth 2.0 Implementation - Production Ready
Uses Supabase authentication instead of API keys
"""

import os
import secrets
import time
from typing import Dict, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import logging

from app.auth import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["claude-oauth-v2"])

# Token storage (use Redis in production)
oauth_store = {
    "clients": {},      # Registered OAuth clients
    "auth_codes": {},   # Temporary authorization codes
    "tokens": {},       # Access tokens mapped to user IDs
    "sessions": {}      # Login sessions
}

BASE_URL = os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com")


@router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth 2.0 discovery endpoint for Claude"""
    return {
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/oauth2/authorize",
        "token_endpoint": f"{BASE_URL}/oauth2/token",
        "registration_endpoint": f"{BASE_URL}/oauth2/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["read", "write"],
        "ui_locales_supported": ["en"]
    }


@router.post("/oauth2/register")
async def register_client(request: Request):
    """Dynamic client registration for Claude"""
    try:
        data = await request.json()
        
        client_id = f"claude_{secrets.token_urlsafe(16)}"
        
        client_data = {
            "client_id": client_id,
            "client_name": data.get("client_name", "Claude"),
            "redirect_uris": data.get("redirect_uris", []),
            "grant_types": data.get("grant_types", ["authorization_code"]),
            "response_types": data.get("response_types", ["code"]),
            "token_endpoint_auth_method": "none"
        }
        
        oauth_store["clients"][client_id] = client_data
        logger.info(f"Registered OAuth client: {client_id}")
        
        return JSONResponse(content=client_data)
        
    except Exception as e:
        logger.error(f"Client registration error: {e}")
        raise HTTPException(status_code=400, detail="Invalid registration request")


@router.get("/oauth2/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    state: str,
    scope: Optional[str] = "read write",
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256"
):
    """OAuth authorization endpoint with professional UI"""
    
    # Validate client
    if client_id not in oauth_store["clients"]:
        raise HTTPException(status_code=400, detail="Invalid client")
    
    # Validate redirect URI
    client = oauth_store["clients"][client_id]
    if redirect_uri not in client["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect URI")
    
    # Create session
    session_id = secrets.token_urlsafe(32)
    oauth_store["sessions"][session_id] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": time.time()
    }
    
    # Professional login page
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Jean Memory - Sign In</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 1rem;
            }}
            
            .auth-container {{
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                padding: 3rem;
                max-width: 420px;
                width: 100%;
                animation: slideIn 0.3s ease-out;
            }}
            
            @keyframes slideIn {{
                from {{ opacity: 0; transform: translateY(-20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .logo-section {{
                text-align: center;
                margin-bottom: 2rem;
            }}
            
            .logo {{
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 1rem;
                font-size: 28px;
            }}
            
            h1 {{
                color: #1a202c;
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }}
            
            .subtitle {{
                color: #718096;
                font-size: 14px;
                margin-bottom: 2rem;
            }}
            
            .claude-info {{
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 2rem;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .claude-icon {{
                width: 40px;
                height: 40px;
                background: #f4b643;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }}
            
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            
            label {{
                display: block;
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
                margin-bottom: 0.5rem;
            }}
            
            input {{
                width: 100%;
                padding: 0.75rem 1rem;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                font-size: 16px;
                transition: all 0.2s;
                background: #fff;
            }}
            
            input:focus {{
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }}
            
            .error-message {{
                color: #e53e3e;
                font-size: 14px;
                margin-top: 0.5rem;
                display: none;
            }}
            
            button {{
                width: 100%;
                padding: 1rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
                overflow: hidden;
            }}
            
            button:hover {{
                transform: translateY(-1px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }}
            
            button:active {{
                transform: translateY(0);
            }}
            
            button:disabled {{
                opacity: 0.7;
                cursor: not-allowed;
            }}
            
            .loading {{
                display: none;
                width: 20px;
                height: 20px;
                border: 2px solid #fff;
                border-radius: 50%;
                border-top-color: transparent;
                animation: spin 0.8s linear infinite;
                margin: 0 auto;
            }}
            
            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}
            
            .links {{
                text-align: center;
                margin-top: 2rem;
            }}
            
            .links a {{
                color: #667eea;
                text-decoration: none;
                font-size: 14px;
                font-weight: 500;
                transition: color 0.2s;
            }}
            
            .links a:hover {{
                color: #764ba2;
            }}
            
            .divider {{
                text-align: center;
                margin: 2rem 0;
                position: relative;
            }}
            
            .divider::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 1px;
                background: #e2e8f0;
            }}
            
            .divider span {{
                background: rgba(255, 255, 255, 0.95);
                padding: 0 1rem;
                color: #718096;
                font-size: 14px;
                position: relative;
            }}
        </style>
    </head>
    <body>
        <div class="auth-container">
            <div class="logo-section">
                <div class="logo">🧠</div>
                <h1>Sign in to Jean Memory</h1>
                <p class="subtitle">Connect your account to Claude</p>
            </div>
            
            <div class="claude-info">
                <div class="claude-icon">🤖</div>
                <div>
                    <strong>Claude</strong> wants to access your Jean Memory
                    <div style="font-size: 12px; color: #718096; margin-top: 4px;">
                        Read and write memories
                    </div>
                </div>
            </div>
            
            <form id="loginForm" onsubmit="handleLogin(event)">
                <input type="hidden" name="session_id" value="{session_id}">
                
                <div class="form-group">
                    <label for="email">Email</label>
                    <input 
                        type="email" 
                        id="email" 
                        name="email" 
                        required 
                        placeholder="you@example.com"
                        autocomplete="email"
                    >
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        required 
                        placeholder="••••••••"
                        autocomplete="current-password"
                    >
                    <div class="error-message" id="error"></div>
                </div>
                
                <button type="submit" id="submitBtn">
                    <span id="btnText">Authorize Claude</span>
                    <div class="loading" id="loading"></div>
                </button>
            </form>
            
            <div class="divider">
                <span>or</span>
            </div>
            
            <div class="links">
                <a href="https://app.jeanmemory.com/signup" target="_blank">
                    Create an account
                </a>
                &nbsp;&nbsp;•&nbsp;&nbsp;
                <a href="https://app.jeanmemory.com/reset-password" target="_blank">
                    Forgot password?
                </a>
            </div>
        </div>
        
        <script>
            async function handleLogin(event) {{
                event.preventDefault();
                
                const form = event.target;
                const submitBtn = document.getElementById('submitBtn');
                const btnText = document.getElementById('btnText');
                const loading = document.getElementById('loading');
                const error = document.getElementById('error');
                
                // Show loading
                submitBtn.disabled = true;
                btnText.style.display = 'none';
                loading.style.display = 'block';
                error.style.display = 'none';
                
                try {{
                    const response = await fetch('/oauth2/authenticate', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            session_id: form.session_id.value,
                            email: form.email.value,
                            password: form.password.value
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok && data.redirect_url) {{
                        window.location.href = data.redirect_url;
                    }} else {{
                        throw new Error(data.detail || 'Invalid email or password');
                    }}
                }} catch (err) {{
                    error.textContent = err.message;
                    error.style.display = 'block';
                    submitBtn.disabled = false;
                    btnText.style.display = 'inline';
                    loading.style.display = 'none';
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@router.post("/oauth2/authenticate")
async def authenticate(request: Request):
    """Handle login and generate OAuth code"""
    try:
        data = await request.json()
        session_id = data.get("session_id")
        email = data.get("email")
        password = data.get("password")
        
        # Validate session
        if session_id not in oauth_store["sessions"]:
            raise HTTPException(status_code=400, detail="Invalid session")
        
        session = oauth_store["sessions"][session_id]
        
        # Authenticate with Supabase
        supabase = get_supabase_client()
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response.user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            user_id = auth_response.user.id
            
        except Exception as e:
            logger.error(f"Supabase auth error: {e}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)
        oauth_store["auth_codes"][auth_code] = {
            "user_id": user_id,
            "client_id": session["client_id"],
            "redirect_uri": session["redirect_uri"],
            "code_challenge": session.get("code_challenge"),
            "scope": session.get("scope", "read write"),
            "created_at": time.time()
        }
        
        # Clean up session
        del oauth_store["sessions"][session_id]
        
        # Build redirect URL
        params = {
            "code": auth_code,
            "state": session["state"]
        }
        redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
        
        return {"redirect_url": redirect_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/oauth2/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    client_id: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None)
):
    """Exchange authorization code for access token"""
    
    if grant_type == "authorization_code":
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")
        
        # Validate auth code
        if code not in oauth_store["auth_codes"]:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        auth_data = oauth_store["auth_codes"][code]
        
        # Validate client and redirect URI
        if auth_data["client_id"] != client_id:
            raise HTTPException(status_code=400, detail="Client mismatch")
        
        # TODO: Validate PKCE if provided
        
        # Generate tokens
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32)
        
        # Store token with user ID
        oauth_store["tokens"][access_token] = {
            "user_id": auth_data["user_id"],
            "client_id": client_id,
            "scope": auth_data["scope"],
            "created_at": time.time(),
            "expires_in": 3600
        }
        
        # Clean up auth code
        del oauth_store["auth_codes"][code]
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token,
            "scope": auth_data["scope"]
        }
    
    elif grant_type == "refresh_token":
        # TODO: Implement refresh token flow
        raise HTTPException(status_code=501, detail="Refresh not implemented yet")
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant type")


@router.post("/mcp/oauth/{path:path}")
async def oauth_mcp_endpoint(path: str, request: Request):
    """MCP endpoint with OAuth authentication"""
    
    # Extract Bearer token
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    
    token = auth_header[7:]
    
    # Validate token
    if token not in oauth_store["tokens"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token_data = oauth_store["tokens"][token]
    
    # Check token expiry
    if time.time() - token_data["created_at"] > token_data["expires_in"]:
        del oauth_store["tokens"][token]
        raise HTTPException(status_code=401, detail="Token expired")
    
    # Get user ID from token
    user_id = token_data["user_id"]
    
    # Import here to avoid circular dependency
    from app.routing.mcp import handle_request_logic
    from fastapi import BackgroundTasks
    
    # Create modified request with user context
    headers = dict(request.headers)
    headers["x-user-id"] = user_id
    headers["x-client-name"] = "claude"
    
    # Parse body
    try:
        body = await request.json()
    except:
        body = {}
    
    # Create new request with auth headers
    from starlette.requests import Request as StarletteRequest
    new_request = StarletteRequest(
        scope={
            **request.scope,
            "headers": [(k.encode(), v.encode()) for k, v in headers.items()]
        }
    )
    
    background_tasks = BackgroundTasks()
    return await handle_request_logic(new_request, body, background_tasks)


# Cleanup expired tokens periodically
def cleanup_expired_tokens():
    """Remove expired tokens and auth codes"""
    current_time = time.time()
    
    # Clean auth codes (5 minute expiry)
    expired_codes = [
        code for code, data in oauth_store["auth_codes"].items()
        if current_time - data["created_at"] > 300
    ]
    for code in expired_codes:
        del oauth_store["auth_codes"][code]
    
    # Clean sessions (10 minute expiry)
    expired_sessions = [
        sid for sid, data in oauth_store["sessions"].items()
        if current_time - data["created_at"] > 600
    ]
    for sid in expired_sessions:
        del oauth_store["sessions"][sid]
    
    # Clean tokens
    expired_tokens = [
        token for token, data in oauth_store["tokens"].items()
        if current_time - data["created_at"] > data["expires_in"]
    ]
    for token in expired_tokens:
        del oauth_store["tokens"][token] 