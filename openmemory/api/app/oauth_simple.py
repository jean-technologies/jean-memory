"""
Simple OAuth 2.0 implementation for Claude Web MCP connector

Based on official Anthropic documentation:
https://help.anthropic.com/en/articles/8996230-getting-started-with-custom-connectors

This is a minimal implementation that Claude Web expects.
"""

import os
import secrets
import time
from typing import Dict, Optional
from urllib.parse import urlencode
import jwt
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.settings import config

# Simple in-memory storage (use Redis in production)
auth_sessions: Dict[str, Dict] = {}
registered_clients: Dict[str, Dict] = {}

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])
bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, email: str, client_name: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "client": client_name,
        "scope": "read write",
        "iat": datetime.utcnow().timestamp(),
        "exp": expire.timestamp(),
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict:
    """Decode JWT access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@oauth_router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth 2.0 discovery endpoint for Claude Web"""
    return {
        "issuer": config.API_BASE_URL,
        "authorization_endpoint": f"{config.API_BASE_URL}/oauth/authorize",
        "token_endpoint": f"{config.API_BASE_URL}/oauth/token",
        "registration_endpoint": f"{config.API_BASE_URL}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["read", "write"],
    }


@oauth_router.post("/register")
async def register_client(request: Request):
    """Dynamic client registration for Claude"""
    data = await request.json()
    
    client_id = f"claude-{secrets.token_urlsafe(8)}"
    client_info = {
        "client_id": client_id,
        "client_name": data.get("client_name", "Claude"),
        "redirect_uris": data.get("redirect_uris", []),
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "scope": "read write",
        "token_endpoint_auth_method": "none"
    }
    
    registered_clients[client_id] = client_info
    
    return client_info


@oauth_router.get("/authorize")
async def authorize(
    request: Request,
    client_id: str,
    redirect_uri: str,
    response_type: str,
    state: str,
    scope: Optional[str] = "read write",
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256"
):
    """OAuth authorization endpoint - shows approval page with Supabase integration"""
    
    # Validate client
    if client_id not in registered_clients:
        raise HTTPException(status_code=400, detail="Invalid client")
    
    # Validate redirect URI
    client_info = registered_clients[client_id]
    if redirect_uri not in client_info["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect URI")
    
    # Create auth session
    session_id = secrets.token_urlsafe(32)
    auth_sessions[session_id] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": scope,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "created_at": time.time()
    }
    
    # Try to get current user from Supabase session
    current_user = None
    try:
        from app.auth import get_current_supa_user
        current_user = await get_current_supa_user(request)
    except:
        pass
    
    # Show authorization page
    client_name = client_info.get("client_name", "Unknown App")
    
    if current_user:
        # User is logged in - show approval form
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connect {client_name} to Jean Memory</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .container {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 400px; width: 100%; }}
                .logo {{ text-align: center; margin-bottom: 30px; }}
                .logo h1 {{ color: #333; margin: 0; font-size: 24px; }}
                .user-info {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .user-info strong {{ color: #495057; }}
                .permissions {{ margin: 20px 0; }}
                .permissions h3 {{ color: #333; font-size: 16px; margin-bottom: 10px; }}
                .permissions ul {{ list-style: none; padding: 0; }}
                .permissions li {{ padding: 8px 0; color: #666; border-bottom: 1px solid #eee; }}
                .permissions li:last-child {{ border-bottom: none; }}
                .permissions li::before {{ content: "✓"; color: #28a745; font-weight: bold; margin-right: 10px; }}
                .buttons {{ display: flex; gap: 10px; margin-top: 30px; }}
                .button {{ flex: 1; padding: 12px; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; text-decoration: none; text-align: center; }}
                .approve {{ background: #007bff; color: white; }}
                .approve:hover {{ background: #0056b3; }}
                .deny {{ background: #6c757d; color: white; }}
                .deny:hover {{ background: #545b62; }}
                .app-info {{ text-align: center; margin-bottom: 20px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🧠 Jean Memory</h1>
                </div>
                
                <div class="app-info">
                    <strong>{client_name}</strong> wants to connect to your Jean Memory account
                </div>
                
                <div class="user-info">
                    <strong>Logged in as:</strong> {current_user.email}
                </div>
                
                <div class="permissions">
                    <h3>This will allow {client_name} to:</h3>
                    <ul>
                        <li>Access your memories and conversations</li>
                        <li>Store new memories from your interactions</li>
                        <li>Search your existing knowledge base</li>
                        <li>Provide personalized context and insights</li>
                    </ul>
                </div>
                
                <div class="buttons">
                    <form method="post" action="/oauth/approve" style="flex: 1;">
                        <input type="hidden" name="session_id" value="{session_id}">
                        <button type="submit" class="button approve">Allow</button>
                    </form>
                    <form method="post" action="/oauth/deny" style="flex: 1;">
                        <input type="hidden" name="session_id" value="{session_id}">
                        <button type="submit" class="button deny">Deny</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        # User not logged in - show login prompt
        login_url = f"https://app.jeanmemory.com/auth?return_url={config.API_BASE_URL}/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&state={state}"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Connect {client_name} to Jean Memory</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
                .container {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); max-width: 400px; width: 100%; text-align: center; }}
                .logo {{ margin-bottom: 30px; }}
                .logo h1 {{ color: #333; margin: 0; font-size: 24px; }}
                .message {{ color: #666; margin-bottom: 30px; line-height: 1.5; }}
                .login-button {{ display: inline-block; background: #007bff; color: white; padding: 15px 30px; border-radius: 6px; text-decoration: none; font-size: 16px; }}
                .login-button:hover {{ background: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🧠 Jean Memory</h1>
                </div>
                
                <div class="message">
                    <strong>{client_name}</strong> wants to connect to your Jean Memory account.
                    <br><br>
                    Please log in to continue.
                </div>
                
                <a href="{login_url}" class="login-button">
                    Log in to Jean Memory
                </a>
            </div>
        </body>
        </html>
        """
    
    return HTMLResponse(content=html)


@oauth_router.post("/approve")
async def approve_authorization(request: Request, session_id: str = Form(...)):
    """User approved the authorization request"""
    
    # Get session
    session = auth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    # Get current user from Supabase
    try:
        from app.auth import get_current_supa_user
        user = await get_current_supa_user(request)
        
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_id = str(user.user_id)
        email = user.email
        
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store auth code with user info
    auth_sessions[auth_code] = {
        **session,
        "user_id": user_id,
        "email": email,
        "code": auth_code,
        "authorized_at": time.time()
    }
    
    # Clean up session
    del auth_sessions[session_id]
    
    # Redirect back to Claude with auth code
    params = {
        "code": auth_code,
        "state": session["state"]
    }
    redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
    
    return RedirectResponse(url=redirect_url)


@oauth_router.post("/deny")
async def deny_authorization(session_id: str = Form(...)):
    """User denied the authorization request"""
    
    # Get session
    session = auth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    # Clean up session
    del auth_sessions[session_id]
    
    # Redirect back to Claude with error
    params = {
        "error": "access_denied",
        "error_description": "User denied the request",
        "state": session["state"]
    }
    redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
    
    return RedirectResponse(url=redirect_url)


@oauth_router.post("/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None)
):
    """Exchange authorization code for access token"""
    
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant type")
    
    # Get auth data
    auth_data = auth_sessions.get(code)
    if not auth_data or "user_id" not in auth_data:
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Validate client
    if auth_data["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Client mismatch")
    
    # Create access token
    access_token = create_access_token(
        user_id=auth_data["user_id"],
        email=auth_data["email"],
        client_name="claude"
    )
    
    # Clean up auth code
    del auth_sessions[code]
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": auth_data.get("scope", "read write")
    }


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    """Extract user from JWT token"""
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        payload = decode_access_token(credentials.credentials)
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "client": payload["client"],
            "scope": payload.get("scope", "read")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")