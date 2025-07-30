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
    # Get base URL from environment variable
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token",
        "registration_endpoint": f"{base_url}/oauth/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["read", "write"],
    }


@oauth_router.post("/register")
async def register_client(request: Request):
    """Dynamic client registration for Claude"""
    import logging
    logger = logging.getLogger(__name__)
    
    data = await request.json()
    logger.info(f"Client registration request: {data}")
    
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
    logger.info(f"Registered client: {client_id} with info: {client_info}")
    
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
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Authorization request: client_id={client_id}, redirect_uri={redirect_uri}")
    logger.info(f"Current registered clients: {list(registered_clients.keys())}")
    
    # Check if client exists, if not and it's Claude, auto-register it
    if client_id not in registered_clients:
        logger.warning(f"Client {client_id} not found in registered clients")
        if client_id.startswith("claude-") and redirect_uri == "https://claude.ai/api/mcp/auth_callback":
            # Auto-register Claude client
            client_info = {
                "client_id": client_id,
                "client_name": "Claude Web",
                "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
                "grant_types": ["authorization_code"],
                "response_types": ["code"],
                "scope": "read write",
                "token_endpoint_auth_method": "none"
            }
            registered_clients[client_id] = client_info
            logger.info(f"Auto-registered Claude client: {client_id}")
        else:
            logger.error(f"Invalid client: {client_id} with redirect_uri: {redirect_uri}")
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
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Authorize {client_name}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #f8fafc;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 16px;
                    line-height: 1.5;
                }}
                
                .container {{
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                    width: 100%;
                }}
                
                .header {{
                    padding: 32px 32px 24px;
                    text-align: center;
                    border-bottom: 1px solid #f1f5f9;
                }}
                
                .logo {{
                    width: 48px;
                    height: 48px;
                    background: #3b82f6;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 16px;
                    color: white;
                    font-size: 24px;
                    font-weight: 600;
                }}
                
                .company-name {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 4px;
                }}
                
                .tagline {{
                    font-size: 14px;
                    color: #64748b;
                }}
                
                .content {{
                    padding: 24px 32px 32px;
                }}
                
                .auth-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 8px;
                }}
                
                .auth-subtitle {{
                    font-size: 14px;
                    color: #64748b;
                    margin-bottom: 24px;
                }}
                
                .client-info {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 16px;
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                
                .client-logo {{
                    width: 32px;
                    height: 32px;
                    background: #6366f1;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                .client-details {{
                    flex: 1;
                }}
                
                .client-name {{
                    font-weight: 500;
                    color: #1e293b;
                    font-size: 14px;
                }}
                
                .client-desc {{
                    font-size: 12px;
                    color: #64748b;
                }}
                
                .user-info {{
                    background: #fafbfc;
                    border: 1px solid #e5e7eb;
                    border-radius: 6px;
                    padding: 12px 16px;
                    margin-bottom: 24px;
                }}
                
                .user-label {{
                    font-size: 12px;
                    color: #6b7280;
                    margin-bottom: 4px;
                }}
                
                .user-email {{
                    font-size: 14px;
                    color: #1f2937;
                    font-weight: 500;
                }}
                
                .permissions {{
                    margin-bottom: 24px;
                }}
                
                .permissions-title {{
                    font-size: 14px;
                    font-weight: 500;
                    color: #1e293b;
                    margin-bottom: 12px;
                }}
                
                .permissions-list {{
                    list-style: none;
                }}
                
                .permissions-list li {{
                    display: flex;
                    align-items: flex-start;
                    gap: 8px;
                    padding: 8px 0;
                    font-size: 13px;
                    color: #4b5563;
                    border-bottom: 1px solid #f1f5f9;
                }}
                
                .permissions-list li:last-child {{
                    border-bottom: none;
                }}
                
                .permission-check {{
                    width: 16px;
                    height: 16px;
                    background: #22c55e;
                    border-radius: 2px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 10px;
                    flex-shrink: 0;
                    margin-top: 1px;
                }}
                
                .actions {{
                    display: flex;
                    gap: 12px;
                }}
                
                .btn {{
                    flex: 1;
                    padding: 12px 16px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.15s ease;
                    text-align: center;
                    text-decoration: none;
                    border: none;
                }}
                
                .btn-primary {{
                    background: #3b82f6;
                    color: white;
                }}
                
                .btn-primary:hover {{
                    background: #2563eb;
                }}
                
                .btn-secondary {{
                    background: white;
                    color: #374151;
                    border: 1px solid #d1d5db;
                }}
                
                .btn-secondary:hover {{
                    background: #f9fafb;
                    border-color: #9ca3af;
                }}
                
                .footer {{
                    padding: 16px 32px;
                    border-top: 1px solid #f1f5f9;
                    text-align: center;
                }}
                
                .security-text {{
                    font-size: 11px;
                    color: #6b7280;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 4px;
                }}
                
                .security-icon {{
                    font-size: 12px;
                }}
                
                @media (max-width: 480px) {{
                    .container {{
                        margin: 0;
                        border-radius: 0;
                        min-height: 100vh;
                        border: none;
                    }}
                    
                    .actions {{
                        flex-direction: column;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">JM</div>
                    <div class="company-name">Jean Memory</div>
                    <div class="tagline">Personal AI Memory System</div>
                </div>
                
                <div class="content">
                    <div class="auth-title">Authorize {client_name}</div>
                    <div class="auth-subtitle">{client_name} is requesting access to your Jean Memory account</div>
                    
                    <div class="client-info">
                        <div class="client-logo">C</div>
                        <div class="client-details">
                            <div class="client-name">{client_name}</div>
                            <div class="client-desc">AI Assistant</div>
                        </div>
                    </div>
                    
                    <div class="user-info">
                        <div class="user-label">Signed in as</div>
                        <div class="user-email">{current_user.email}</div>
                    </div>
                    
                    <div class="permissions">
                        <div class="permissions-title">This will allow {client_name} to:</div>
                        <ul class="permissions-list">
                            <li>
                                <div class="permission-check">✓</div>
                                <span>Access your memories and conversations</span>
                            </li>
                            <li>
                                <div class="permission-check">✓</div>
                                <span>Store new memories from interactions</span>
                            </li>
                            <li>
                                <div class="permission-check">✓</div>
                                <span>Search your knowledge base</span>
                            </li>
                            <li>
                                <div class="permission-check">✓</div>
                                <span>Provide personalized insights</span>
                            </li>
                        </ul>
                    </div>
                    
                    <div class="actions">
                        <form method="post" action="/oauth/deny" style="flex: 1;">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <button type="submit" class="btn btn-secondary">Cancel</button>
                        </form>
                        <form method="post" action="/oauth/approve" style="flex: 1;">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <button type="submit" class="btn btn-primary">Authorize</button>
                        </form>
                    </div>
                </div>
                
                <div class="footer">
                    <div class="security-text">
                        <span class="security-icon">🔒</span>
                        <span>Secured by OAuth 2.0 • Revoke access anytime</span>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        # User not logged in - show login prompt
        # Get base URL from environment variable
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        login_url = f"https://app.jeanmemory.com/auth?return_url={base_url}/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type={response_type}&state={state}"
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Sign in - Jean Memory</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    background: #f8fafc;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 16px;
                    line-height: 1.5;
                }}
                
                .container {{
                    background: white;
                    border-radius: 8px;
                    border: 1px solid #e2e8f0;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                    width: 100%;
                    text-align: center;
                }}
                
                .header {{
                    padding: 32px 32px 24px;
                    border-bottom: 1px solid #f1f5f9;
                }}
                
                .logo {{
                    width: 48px;
                    height: 48px;
                    background: #3b82f6;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 16px;
                    color: white;
                    font-size: 24px;
                    font-weight: 600;
                }}
                
                .company-name {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 4px;
                }}
                
                .tagline {{
                    font-size: 14px;
                    color: #64748b;
                }}
                
                .content {{
                    padding: 24px 32px 32px;
                }}
                
                .sign-in-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1e293b;
                    margin-bottom: 8px;
                }}
                
                .sign-in-subtitle {{
                    font-size: 14px;
                    color: #64748b;
                    margin-bottom: 24px;
                }}
                
                .client-info {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 16px;
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                
                .client-logo {{
                    width: 32px;
                    height: 32px;
                    background: #6366f1;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 600;
                    font-size: 14px;
                }}
                
                .client-details {{
                    flex: 1;
                    text-align: left;
                }}
                
                .client-name {{
                    font-weight: 500;
                    color: #1e293b;
                    font-size: 14px;
                }}
                
                .client-desc {{
                    font-size: 12px;
                    color: #64748b;
                }}
                
                .login-button {{
                    display: inline-block;
                    background: #3b82f6;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.15s ease;
                    margin-bottom: 24px;
                    width: 100%;
                    text-align: center;
                }}
                
                .login-button:hover {{
                    background: #2563eb;
                }}
                
                .footer {{
                    padding: 16px 32px;
                    border-top: 1px solid #f1f5f9;
                }}
                
                .security-text {{
                    font-size: 11px;
                    color: #6b7280;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 4px;
                }}
                
                .security-icon {{
                    font-size: 12px;
                }}
                
                @media (max-width: 480px) {{
                    .container {{
                        margin: 0;
                        border-radius: 0;
                        min-height: 100vh;
                        border: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">JM</div>
                    <div class="company-name">Jean Memory</div>
                    <div class="tagline">Personal AI Memory System</div>
                </div>
                
                <div class="content">
                    <div class="sign-in-title">Sign in required</div>
                    <div class="sign-in-subtitle">Please sign in to authorize {client_name}</div>
                    
                    <div class="client-info">
                        <div class="client-logo">C</div>
                        <div class="client-details">
                            <div class="client-name">{client_name}</div>
                            <div class="client-desc">wants to connect to your account</div>
                        </div>
                    </div>
                    
                    <a href="{login_url}" class="login-button">
                        Sign in to Jean Memory
                    </a>
                </div>
                
                <div class="footer">
                    <div class="security-text">
                        <span class="security-icon">🔒</span>
                        <span>Secure authentication • We'll redirect you back</span>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    return HTMLResponse(content=html)


@oauth_router.post("/approve")
async def approve_authorization(request: Request, session_id: str = Form(...)):
    """User approved the authorization request"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Approve request: session_id={session_id}")
    logger.info(f"Available sessions: {list(auth_sessions.keys())}")
    
    # Get session
    session = auth_sessions.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found in auth_sessions")
        raise HTTPException(status_code=400, detail="Invalid session - please try the OAuth flow again")
    
    # Get current user from Supabase session cookies
    try:
        # For OAuth approval, user might not have Authorization header
        # Try to get user from session cookies instead
        from app.auth import supabase_service_client
        from app.settings import config
        
        if config.is_local_development:
            # Use local dev user
            from app.local_auth_helper import get_local_dev_user
            user = await get_local_dev_user(request, supabase_service_client, config)
            user_id = str(user.id)
            email = user.email or "dev@example.com"
        else:
            # Try to get user from session cookies
            # First check if there's an access_token cookie
            access_token = request.cookies.get('sb-access-token') or request.cookies.get('supabase-auth-token')
            
            if not access_token:
                # Try to get from other common cookie names
                import json
                # Check for session cookie
                session_cookie = request.cookies.get('sb-session') or request.cookies.get('supabase.auth.token')
                if session_cookie:
                    try:
                        session_data = json.loads(session_cookie)
                        access_token = session_data.get('access_token')
                    except:
                        pass
            
            if not access_token:
                raise HTTPException(status_code=401, detail="Not authenticated - please log in to Jean Memory first")
            
            # Validate token with Supabase
            auth_response = supabase_service_client.auth.get_user(access_token)
            if not auth_response or not auth_response.user:
                raise HTTPException(status_code=401, detail="Invalid session - please log in again")
            
            user = auth_response.user
            user_id = str(user.id)
            email = user.email
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    
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
async def deny_authorization(request: Request, session_id: str = Form(...)):
    """User denied the authorization request"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Deny request: session_id={session_id}")
    logger.info(f"Available sessions: {list(auth_sessions.keys())}")
    
    # Get session
    session = auth_sessions.get(session_id)
    if not session:
        logger.error(f"Session {session_id} not found in auth_sessions")
        raise HTTPException(status_code=400, detail="Invalid session - please try the OAuth flow again")
    
    # Clean up session
    del auth_sessions[session_id]
    
    # Redirect back to Claude with error
    params = {
        "error": "access_denied",
        "error_description": "User denied the request",
        "state": session["state"]
    }
    redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
    
    return RedirectResponse(url=redirect_url, status_code=302)


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
    
    # Validate client - also handle auto-registration for Claude
    if auth_data["client_id"] != client_id:
        raise HTTPException(status_code=400, detail="Client mismatch")
    
    # Ensure client still exists in registered_clients (in case of server restart)
    if client_id not in registered_clients and client_id.startswith("claude-"):
        registered_clients[client_id] = {
            "client_id": client_id,
            "client_name": "Claude Web",
            "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
            "grant_types": ["authorization_code"],
            "response_types": ["code"],
            "scope": "read write",
            "token_endpoint_auth_method": "none"
        }
    
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