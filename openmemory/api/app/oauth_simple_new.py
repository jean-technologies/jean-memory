"""
Simple OAuth 2.0 implementation for Claude Web MCP connector

This creates a standalone OAuth authorization page that handles authentication
without redirecting to the main Jean Memory site.
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
    code_challenge_method: Optional[str] = "S256",
    oauth_session: Optional[str] = None  # Session ID from post-auth redirect
):
    """OAuth authorization endpoint - shows login/authorization page"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Authorization request: client_id={client_id}, redirect_uri={redirect_uri}, oauth_session={oauth_session}")
    
    # Check if this is a post-authentication callback with session ID
    if oauth_session and oauth_session in auth_sessions:
        logger.info(f"🔄 Post-authentication callback with session: {oauth_session}")
        
        # Retrieve stored session data
        session_data = auth_sessions[oauth_session]
        
        # Use stored session data instead of URL parameters
        client_id = session_data["client_id"]
        redirect_uri = session_data["redirect_uri"]
        state = session_data["state"]
        scope = session_data["scope"]
        code_challenge = session_data["code_challenge"]
        code_challenge_method = session_data["code_challenge_method"]
        
        logger.info(f"📋 Restored session data: client_id={client_id}, redirect_uri={redirect_uri}")
    
    # Check if client exists, if not and it's Claude, auto-register it
    if client_id not in registered_clients:
        if client_id.startswith("claude-") and redirect_uri == "https://claude.ai/api/mcp/auth_callback":
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
            raise HTTPException(status_code=400, detail="Invalid client")
    
    # Validate redirect URI
    client_info = registered_clients[client_id]
    if redirect_uri not in client_info["redirect_uris"]:
        raise HTTPException(status_code=400, detail="Invalid redirect URI")
    
    # Create or update auth session
    if not oauth_session:
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
        logger.info(f"🆕 Created new OAuth session: {session_id}")
    else:
        session_id = oauth_session
        logger.info(f"🔄 Using existing OAuth session: {session_id}")
    
    # Try to get current user using OAuth-specific authentication
    current_user = None
    try:
        from app.auth import get_oauth_user
        current_user = await get_oauth_user(request)
        if current_user:
            logger.info(f"✅ Found authenticated user: {current_user.email}")
        else:
            logger.info("❌ No authenticated user found")
    except Exception as e:
        logger.error(f"❌ OAuth user detection error: {e}")
    
    client_name = client_info.get("client_name", "Unknown Client")
    
    if current_user:
        # User is authenticated - auto-approve for Claude
        if client_id.startswith("claude-") and redirect_uri == "https://claude.ai/api/mcp/auth_callback":
            logger.info(f"🚀 Auto-approving Claude client for authenticated user: {current_user.email}")
            
            # Generate authorization code immediately
            auth_code = secrets.token_urlsafe(32)
            
            # Get session data
            session = auth_sessions[session_id]
            
            # Store auth code with user info and PKCE challenge
            auth_sessions[auth_code] = {
                **session,
                "user_id": str(current_user.id),
                "email": current_user.email,
                "code": auth_code,
                "authorized_at": time.time(),
                "client_id": client_id
            }
            
            # Clean up original session
            del auth_sessions[session_id]
            
            # Redirect back to Claude with auth code
            params = {
                "code": auth_code,
                "state": session["state"]
            }
            redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
            logger.info(f"🎯 Auto-approval complete - redirecting to Claude: {redirect_url}")
            
            return RedirectResponse(url=redirect_url)
    
    # Show login/authorization page with preserved OAuth session
    # Store the session_id in the URL so we can retrieve it after login
    oauth_session_param = f"oauth_session={session_id}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Sign in to Jean Memory</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://unpkg.com/@supabase/supabase-js@2"></script>
        <style>
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f8fafc;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 16px;
            }}
            
            .container {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                max-width: 400px;
                width: 100%;
                padding: 32px;
                text-align: center;
            }}
            
            .logo {{
                width: 48px;
                height: 48px;
                background: #3b82f6;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 24px;
                color: white;
                font-size: 24px;
                font-weight: 600;
            }}
            
            h1 {{
                font-size: 24px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 8px;
            }}
            
            p {{
                color: #64748b;
                margin-bottom: 32px;
            }}
            
            .client-info {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 32px;
                display: flex;
                align-items: center;
                gap: 12px;
                text-align: left;
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
            
            .client-name {{
                font-weight: 500;
                color: #1e293b;
            }}
            
            .client-desc {{
                font-size: 12px;
                color: #64748b;
            }}
            
            .login-button {{
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                width: 100%;
                margin-bottom: 16px;
                transition: background 0.2s;
            }}
            
            .login-button:hover {{
                background: #2563eb;
            }}
            
            .login-button:disabled {{
                background: #94a3b8;
                cursor: not-allowed;
            }}
            
            .security-text {{
                font-size: 12px;
                color: #64748b;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 4px;
            }}
            
            .error {{
                background: #fef2f2;
                border: 1px solid #fecaca;
                color: #dc2626;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 16px;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">JM</div>
            <h1>Sign in to Jean Memory</h1>
            <p>To connect with {client_name}</p>
            
            <div class="client-info">
                <div class="client-logo">C</div>
                <div>
                    <div class="client-name">{client_name}</div>
                    <div class="client-desc">AI Assistant</div>
                </div>
            </div>
            
            <div class="error" id="error"></div>
            
            <button class="login-button" onclick="signInWithGoogle()" id="loginBtn">
                Continue with Google
            </button>
            
            <div class="security-text">
                <span>🔒</span>
                <span>Secure OAuth 2.0 authentication</span>
            </div>
        </div>
        
        <script>
            // Initialize Supabase
            const supabase = window.supabase.createClient(
                'https://masapxpxcwvsjpuymbmd.supabase.co',
                'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hc2FweHB4Y3d2c2pwdXltYm1kIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjYxODI3MjYsImV4cCI6MjA0MTc1ODcyNn0.1nSe1h0I9bN_yROdVPJX4L3X0QlqtyFfKMtCJ6XnK9w'
            );
            
            async function signInWithGoogle() {{
                const button = document.getElementById('loginBtn');
                const error = document.getElementById('error');
                
                button.disabled = true;
                button.textContent = 'Signing in...';
                error.style.display = 'none';
                
                try {{
                    // Build redirect URL with session preservation
                    const currentUrl = new URL(window.location.href);
                    
                    // Add oauth_session parameter if not already present
                    if (!currentUrl.searchParams.has('oauth_session')) {{
                        currentUrl.searchParams.set('oauth_session', '{session_id}');
                    }}
                    
                    const {{ data, error: signInError }} = await supabase.auth.signInWithOAuth({{
                        provider: 'google',
                        options: {{
                            redirectTo: currentUrl.toString()
                        }}
                    }});
                    
                    if (signInError) {{
                        throw signInError;
                    }}
                }} catch (err) {{
                    console.error('Sign in error:', err);
                    error.textContent = 'Sign in failed. Please try again.';
                    error.style.display = 'block';
                    button.disabled = false;
                    button.textContent = 'Continue with Google';
                }}
            }}
            
            // Check if user is already signed in when page loads
            supabase.auth.onAuthStateChange((event, session) => {{
                if (event === 'SIGNED_IN' && session) {{
                    // User is signed in, ensure session parameter is preserved and reload
                    const currentUrl = new URL(window.location.href);
                    if (!currentUrl.searchParams.has('oauth_session')) {{
                        currentUrl.searchParams.set('oauth_session', '{session_id}');
                        window.location.href = currentUrl.toString();
                    }} else {{
                        window.location.reload();
                    }}
                }}
            }});
            
            // Check initial session
            supabase.auth.getSession().then({{ data: {{ session }} }}) => {{
                if (session) {{
                    // User is already signed in, ensure session parameter and reload
                    const currentUrl = new URL(window.location.href);
                    if (!currentUrl.searchParams.has('oauth_session')) {{
                        currentUrl.searchParams.set('oauth_session', '{session_id}');
                        window.location.href = currentUrl.toString();
                    }} else {{
                        window.location.reload();
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@oauth_router.post("/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None)
):
    """Exchange authorization code for access token"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Token exchange request: grant_type={grant_type}, client_id={client_id}, code={code[:8]}...")
    
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant type")
    
    # Get auth data
    auth_data = auth_sessions.get(code)
    if not auth_data or "user_id" not in auth_data:
        logger.error(f"Invalid authorization code: {code}")
        raise HTTPException(status_code=400, detail="Invalid authorization code")
    
    # Validate client
    if auth_data["client_id"] != client_id:
        logger.error(f"Client mismatch: expected {auth_data['client_id']}, got {client_id}")
        raise HTTPException(status_code=400, detail="Client mismatch")
    
    # Validate PKCE (REQUIRED per MCP spec)
    if not code_verifier:
        logger.error("Missing code_verifier - PKCE required")
        raise HTTPException(status_code=400, detail="code_verifier required")
    
    if "code_challenge" not in auth_data:
        logger.error("Missing code_challenge in stored auth data")
        raise HTTPException(status_code=400, detail="Invalid authorization code - missing challenge")
    
    # Verify PKCE challenge using SHA256
    import hashlib
    import base64
    
    verifier_hash = hashlib.sha256(code_verifier.encode()).digest()
    verifier_challenge = base64.urlsafe_b64encode(verifier_hash).decode().rstrip('=')
    
    if verifier_challenge != auth_data["code_challenge"]:
        logger.error(f"PKCE verification failed: expected {auth_data['code_challenge']}, got {verifier_challenge}")
        raise HTTPException(status_code=400, detail="Invalid code verifier")
    
    logger.info("✅ PKCE verification successful")
    
    # Create access token
    access_token = create_access_token(
        user_id=auth_data["user_id"],
        email=auth_data["email"],
        client_name="claude"
    )
    
    logger.info(f"Created access token for user {auth_data['email']}")
    
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