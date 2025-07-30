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
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Connect {client_name} to Jean Memory</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                    line-height: 1.6;
                }}
                
                .container {{
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                    max-width: 480px;
                    width: 100%;
                    overflow: hidden;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 32px;
                    text-align: center;
                }}
                
                .logo {{
                    font-size: 48px;
                    margin-bottom: 8px;
                }}
                
                .brand {{
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                
                .subtitle {{
                    font-size: 14px;
                    opacity: 0.9;
                    font-weight: 300;
                }}
                
                .content {{
                    padding: 32px;
                }}
                
                .connection-request {{
                    text-align: center;
                    margin-bottom: 24px;
                    padding: 24px;
                    background: linear-gradient(135deg, #f8f9ff 0%, #f0f2ff 100%);
                    border-radius: 12px;
                    border: 1px solid #e6e8ff;
                }}
                
                .client-name {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #4a5568;
                    margin-bottom: 8px;
                }}
                
                .request-text {{
                    color: #718096;
                    font-size: 14px;
                }}
                
                .user-info {{
                    background: #f7fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 20px;
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                
                .user-avatar {{
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: 600;
                    font-size: 16px;
                }}
                
                .user-details h4 {{
                    color: #2d3748;
                    font-weight: 500;
                    margin-bottom: 2px;
                }}
                
                .user-details p {{
                    color: #718096;
                    font-size: 14px;
                }}
                
                .permissions {{
                    margin-bottom: 32px;
                }}
                
                .permissions h3 {{
                    color: #2d3748;
                    font-size: 16px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }}
                
                .permissions-list {{
                    list-style: none;
                    space-y: 8px;
                }}
                
                .permissions-list li {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px 0;
                    color: #4a5568;
                    font-size: 14px;
                    border-bottom: 1px solid #f1f5f9;
                }}
                
                .permissions-list li:last-child {{
                    border-bottom: none;
                }}
                
                .permission-icon {{
                    width: 20px;
                    height: 20px;
                    background: #48bb78;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 12px;
                    font-weight: bold;
                    flex-shrink: 0;
                }}
                
                .actions {{
                    display: flex;
                    gap: 16px;
                }}
                
                .btn {{
                    flex: 1;
                    padding: 16px 24px;
                    border: none;
                    border-radius: 12px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-decoration: none;
                    text-align: center;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                
                .btn-approve {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                }}
                
                .btn-approve:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
                }}
                
                .btn-deny {{
                    background: #f7fafc;
                    color: #4a5568;
                    border: 1px solid #e2e8f0;
                }}
                
                .btn-deny:hover {{
                    background: #edf2f7;
                    border-color: #cbd5e0;
                }}
                
                .security-note {{
                    margin-top: 24px;
                    padding: 16px;
                    background: #f0fff4;
                    border: 1px solid #c6f6d5;
                    border-radius: 8px;
                    font-size: 12px;
                    color: #276749;
                }}
                
                @media (max-width: 480px) {{
                    .container {{
                        border-radius: 0;
                        min-height: 100vh;
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
                    <div class="logo">🧠</div>
                    <div class="brand">Jean Memory</div>
                    <div class="subtitle">Personal AI Memory System</div>
                </div>
                
                <div class="content">
                    <div class="connection-request">
                        <div class="client-name">{client_name}</div>
                        <div class="request-text">wants to connect to your Jean Memory account</div>
                    </div>
                    
                    <div class="user-info">
                        <div class="user-avatar">{current_user.email[0].upper()}</div>
                        <div class="user-details">
                            <h4>Signed in as</h4>
                            <p>{current_user.email}</p>
                        </div>
                    </div>
                    
                    <div class="permissions">
                        <h3>This will allow {client_name} to:</h3>
                        <ul class="permissions-list">
                            <li>
                                <div class="permission-icon">✓</div>
                                Access your memories and conversations
                            </li>
                            <li>
                                <div class="permission-icon">✓</div>
                                Store new memories from your interactions
                            </li>
                            <li>
                                <div class="permission-icon">✓</div>
                                Search your existing knowledge base
                            </li>
                            <li>
                                <div class="permission-icon">✓</div>
                                Provide personalized context and insights
                            </li>
                        </ul>
                    </div>
                    
                    <div class="actions">
                        <form method="post" action="/oauth/approve" style="flex: 1;">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <button type="submit" class="btn btn-approve">
                                Allow Access
                            </button>
                        </form>
                        <form method="post" action="/oauth/deny" style="flex: 1;">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <button type="submit" class="btn btn-deny">
                                Cancel
                            </button>
                        </form>
                    </div>
                    
                    <div class="security-note">
                        🔒 Your connection is secure and encrypted. You can revoke access at any time from your Jean Memory settings.
                    </div>
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
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Connect {client_name} to Jean Memory</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                    line-height: 1.6;
                }}
                
                .container {{
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                    max-width: 480px;
                    width: 100%;
                    overflow: hidden;
                    text-align: center;
                }}
                
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 48px 32px;
                }}
                
                .logo {{
                    font-size: 64px;
                    margin-bottom: 16px;
                }}
                
                .brand {{
                    font-size: 28px;
                    font-weight: 700;
                    margin-bottom: 8px;
                }}
                
                .subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 300;
                }}
                
                .content {{
                    padding: 48px 32px;
                }}
                
                .connection-request {{
                    margin-bottom: 32px;
                    padding: 32px;
                    background: linear-gradient(135deg, #f8f9ff 0%, #f0f2ff 100%);
                    border-radius: 16px;
                    border: 1px solid #e6e8ff;
                }}
                
                .client-name {{
                    font-size: 24px;
                    font-weight: 600;
                    color: #4a5568;
                    margin-bottom: 12px;
                }}
                
                .request-text {{
                    color: #718096;
                    font-size: 16px;
                    margin-bottom: 8px;
                }}
                
                .login-instruction {{
                    color: #a0aec0;
                    font-size: 14px;
                    font-style: italic;
                }}
                
                .login-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 18px 36px;
                    border-radius: 12px;
                    text-decoration: none;
                    font-size: 16px;
                    font-weight: 600;
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                    transition: all 0.2s ease;
                    margin-bottom: 24px;
                }}
                
                .login-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
                }}
                
                .security-note {{
                    padding: 16px;
                    background: #f0fff4;
                    border: 1px solid #c6f6d5;
                    border-radius: 8px;
                    font-size: 12px;
                    color: #276749;
                }}
                
                @media (max-width: 480px) {{
                    .container {{
                        border-radius: 0;
                        min-height: 100vh;
                    }}
                    
                    .content {{
                        padding: 32px 24px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🧠</div>
                    <div class="brand">Jean Memory</div>
                    <div class="subtitle">Personal AI Memory System</div>
                </div>
                
                <div class="content">
                    <div class="connection-request">
                        <div class="client-name">{client_name}</div>
                        <div class="request-text">wants to connect to your Jean Memory account</div>
                        <div class="login-instruction">Please sign in to continue</div>
                    </div>
                    
                    <a href="{login_url}" class="login-button">
                        Sign in to Jean Memory
                    </a>
                    
                    <div class="security-note">
                        🔒 Your login is secure and encrypted. We'll redirect you back here after authentication.
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
    
    # Get session
    session = auth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
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