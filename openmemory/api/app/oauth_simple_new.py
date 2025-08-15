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

from fastapi import APIRouter, Request, HTTPException, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.settings import config

# Simple in-memory storage (use Redis in production)
auth_sessions: Dict[str, Dict] = {}
registered_clients: Dict[str, Dict] = {}

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
JWT_ALGORITHM = "HS256"

# OAuth2 scheme for Bearer token authentication
bearer_scheme = HTTPBearer()

# Exception for credential validation failures
credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

# Logger for this module
logger = logging.getLogger(__name__)
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])
bearer_scheme = HTTPBearer(auto_error=True)


def create_access_token(user_id: str, email: str, client_name: str, scopes: list = None) -> str:
    """Create JWT access token with MCP-compliant scopes"""
    if scopes is None:
        # Use both legacy and MCP scopes for maximum compatibility
        scopes = ["read", "write", "mcp:tools", "mcp:resources", "mcp:prompts"]
    
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,
        "email": email,
        "client": client_name,
        "scope": " ".join(scopes),  # OAuth 2.1 standard scope claim
        "iat": datetime.utcnow().timestamp(),
        "exp": expire.timestamp(),
        "aud": "jean-memory-mcp",  # Audience for MCP resource server
        "iss": "https://jean-memory-api-virginia.onrender.com",  # Issuer
        "mcp_capabilities": ["tools", "resources", "prompts"]  # MCP-specific claim
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
        "scopes_supported": ["read", "write", "mcp:tools", "mcp:resources", "mcp:prompts"],
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
    oauth_session: Optional[str] = None
):
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Authorization request: client_id={client_id}, redirect_uri={redirect_uri}, oauth_session={oauth_session}")
    
    if oauth_session and oauth_session in auth_sessions:
        logger.info(f"🔄 Post-authentication callback with session: {oauth_session}")
        session_data = auth_sessions[oauth_session]
        client_id = session_data["client_id"]
        redirect_uri = session_data["redirect_uri"]
        state = session_data["state"]
        scope = session_data["scope"]
        code_challenge = session_data["code_challenge"]
        code_challenge_method = session_data["code_challenge_method"]
        logger.info(f"📋 Restored session data: client_id={client_id}, redirect_uri={redirect_uri}")
    
    if client_id not in registered_clients:
        # If the client is not registered, check if it's a local development client
        is_local_dev = (redirect_uri.startswith("http://localhost:") or 
                       redirect_uri.startswith("http://127.0.0.1:") or
                       redirect_uri == "https://jeanmemory.com/oauth-bridge.html")
        
        if is_local_dev:
            # Auto-register a "Default Local" client for local development
            # Use dynamic validation instead of hardcoded list
            local_client_id = "local-dev-client"
            if local_client_id not in registered_clients:
                client_info = {
                    "client_id": local_client_id,
                    "client_name": "Default Local Client",
                    "redirect_uris": ["*localhost*", "https://jeanmemory.com/oauth-bridge.html"], # Wildcard for dynamic validation
                    "grant_types": ["authorization_code"],
                    "response_types": ["code"],
                    "scope": "read write mcp:tools mcp:resources mcp:prompts openid profile email",
                    "token_endpoint_auth_method": "none"
                }
                registered_clients[local_client_id] = client_info
                logger.info(f"Auto-registered local development client: {local_client_id}")
            client_id = local_client_id # Use this client_id for the rest of the flow

        elif client_id.startswith("claude-") and redirect_uri == "https://claude.ai/api/mcp/auth_callback":
            # Auto-register Claude client
            client_info = {
                "client_id": client_id, "client_name": "Claude Web",
                "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"],
                "grant_types": ["authorization_code"], "response_types": ["code"],
                "scope": "read write", "token_endpoint_auth_method": "none"
            }
            registered_clients[client_id] = client_info
            logger.info(f"Auto-registered Claude client: {client_id}")
        else:
            raise HTTPException(status_code=400, detail="Invalid client")
    
    client_info = registered_clients[client_id]
    
    # Dynamic redirect URI validation for local development
    def is_redirect_uri_allowed(uri: str, allowed_uris: list) -> bool:
        # Direct match
        if uri in allowed_uris:
            return True
        
        # Wildcard match for localhost
        for allowed in allowed_uris:
            if allowed == "*localhost*":
                if (uri.startswith("http://localhost:") or 
                    uri.startswith("http://127.0.0.1:")):
                    return True
        
        return False
    
    if not is_redirect_uri_allowed(redirect_uri, client_info["redirect_uris"]):
        logger.error(f"Invalid redirect URI: {redirect_uri} not in {client_info['redirect_uris']}")
        raise HTTPException(status_code=400, detail="Invalid redirect URI")
    
    if not oauth_session:
        session_id = secrets.token_urlsafe(32)
        auth_sessions[session_id] = {
            "client_id": client_id, "redirect_uri": redirect_uri, "state": state, "scope": scope,
            "code_challenge": code_challenge, "code_challenge_method": code_challenge_method,
            "created_at": time.time()
        }
        logger.info(f"🆕 Created new OAuth session: {session_id}")
    else:
        session_id = oauth_session
        logger.info(f"🔄 Using existing OAuth session: {session_id}")
    
    current_user = None
    if oauth_session:
        try:
            from app.auth import get_oauth_user
            current_user = await get_oauth_user(request)
            if current_user: logger.info(f"✅ Post-auth: Found authenticated user: {current_user.email}")
            else: logger.info("❌ Post-auth: No authenticated user found")
        except Exception as e:
            logger.error(f"❌ Post-auth user detection error: {e}")
    else:
        logger.info("🔄 Initial OAuth request - showing login page for self-contained authentication")
    
    client_name = client_info.get("client_name", "Unknown Client")
    
    if current_user:
        if client_id.startswith("claude-") and redirect_uri == "https://claude.ai/api/mcp/auth_callback":
            logger.info(f"🚀 Auto-approving Claude client for authenticated user: {current_user.email}")
            auth_code = secrets.token_urlsafe(32)
            session = auth_sessions[session_id]
            from app.database import SessionLocal
            from app.models import User
            db = SessionLocal()
            try:
                internal_user = db.query(User).filter(User.user_id == str(current_user.id)).first()
                if not internal_user:
                    logger.error(f"No internal User found for Supabase user_id: {current_user.id}")
                    raise HTTPException(status_code=500, detail="User not found in database")
                internal_user_id = str(internal_user.id)
                logger.info(f"Mapped Supabase user {current_user.id} to internal user {internal_user_id}")
            finally:
                db.close()
            
            auth_sessions[auth_code] = {
                **session, "user_id": internal_user_id, "supabase_user_id": str(current_user.id),
                "email": current_user.email, "code": auth_code, "authorized_at": time.time(), "client_id": client_id
            }
            del auth_sessions[session_id]
            params = {"code": auth_code, "state": session["state"]}
            redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
            logger.info(f"🎯 Auto-approval complete - redirecting to Claude: {redirect_url}")
            
            return RedirectResponse(url=redirect_url)
    
    # Show login/authorization page using the new static template
    try:
        with open("app/static/oauth_authorize.html", "r") as f:
            html_template = f.read()
    except FileNotFoundError:
        logger.error("FATAL: oauth_authorize.html template not found!")
        raise HTTPException(status_code=500, detail="Server misconfiguration: missing OAuth template.")

    # Replace placeholders with actual values
    html_content = html_template.replace("{{CLIENT_NAME}}", client_name)
    html_content = html_content.replace("{{SESSION_ID}}", session_id)
    
    return HTMLResponse(content=html_content)
    
@oauth_router.get("/auth-redirect")
async def universal_auth_redirect(request: Request):
    """Universal auth redirect handler that routes to correct destination based on parameters"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Get all query parameters
    params = dict(request.query_params)
    logger.info(f"🔍 Universal auth redirect received with params: {params}")
    
    # Check if this is an MCP OAuth flow
    oauth_session = params.get('oauth_session')
    flow = params.get('flow')
    
    if flow == "mcp_oauth" and oauth_session:
        logger.info(f"🚀 MCP OAuth flow detected - redirecting to callback with session: {oauth_session}")
        # This is MCP OAuth, redirect to our callback
        callback_url = f"/oauth/callback?oauth_session={oauth_session}&flow=mcp_oauth"
        return RedirectResponse(url=callback_url)
    elif flow == "mcp_oauth":
        # MCP OAuth flow but missing session - try to find active session
        logger.info("🔍 MCP OAuth flow detected but missing session - checking for active sessions")
        
        # Find the most recent OAuth session
        if auth_sessions:
            # Get the most recent session (sessions are created with timestamp)
            recent_sessions = [(session_id, session_data) for session_id, session_data in auth_sessions.items() 
                             if 'created_at' in session_data and not session_data.get('code')]
            
            if recent_sessions:
                # Sort by creation time and get the most recent
                recent_sessions.sort(key=lambda x: x[1]['created_at'], reverse=True)
                most_recent_session = recent_sessions[0][0]
                
                logger.info(f"🔄 Using most recent OAuth session: {most_recent_session}")
                callback_url = f"/oauth/callback?oauth_session={most_recent_session}&flow=mcp_oauth"
                return RedirectResponse(url=callback_url)
        
        logger.warning("⚠️ MCP OAuth flow but no active sessions found")
        return RedirectResponse(url="https://jeanmemory.com")
    else:
        logger.info("🔄 Regular app login detected - redirecting to main app")
        # This is regular app login, redirect to main app
        return RedirectResponse(url="https://jeanmemory.com")


@oauth_router.get("/force-complete")
async def force_oauth_completion(request: Request, oauth_session: str):
    """Emergency OAuth completion endpoint that bypasses Supabase redirects"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚨 FORCE COMPLETE: Emergency OAuth completion for session: {oauth_session}")
    
    # Check if session exists
    if oauth_session not in auth_sessions:
        logger.error(f"❌ FORCE COMPLETE: Invalid OAuth session: {oauth_session}")
        raise HTTPException(status_code=400, detail="Invalid OAuth session")
    
    # Try to get current user from session/cookies
    try:
        from app.auth import get_oauth_user
        current_user = await get_oauth_user(request)
        
        if not current_user:
            logger.error("❌ FORCE COMPLETE: No authenticated user found")
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        logger.info(f"✅ FORCE COMPLETE: Found authenticated user: {current_user.email}")
        
        # Get session data
        session_data = auth_sessions[oauth_session]
        client_id = session_data["client_id"]
        redirect_uri = session_data["redirect_uri"]
        state = session_data["state"]
        
        # Generate authorization code immediately
        auth_code = secrets.token_urlsafe(32)
        
        # Get the internal User.id from database
        from app.database import SessionLocal
        from app.models import User
        
        db = SessionLocal()
        try:
            internal_user = db.query(User).filter(User.user_id == str(current_user.id)).first()
            if not internal_user:
                logger.error(f"❌ FORCE COMPLETE: No internal User found for Supabase user_id: {current_user.id}")
                raise HTTPException(status_code=500, detail="User not found in database")
            
            internal_user_id = str(internal_user.id)
            logger.info(f"✅ FORCE COMPLETE: Mapped Supabase user {current_user.id} to internal user {internal_user_id}")
            
        finally:
            db.close()
        
        # Store auth code with user info
        auth_sessions[auth_code] = {
            **session_data,
            "user_id": internal_user_id,
            "supabase_user_id": str(current_user.id),
            "email": current_user.email,
            "code": auth_code,
            "authorized_at": time.time(),
            "client_id": client_id
        }
        
        # Clean up original session
        del auth_sessions[oauth_session]
        
        # Redirect back to Claude with auth code
        params = {
            "code": auth_code,
            "state": state
        }
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        logger.info(f"🎯 FORCE COMPLETE: Redirecting to Claude: {redirect_url}")
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"❌ FORCE COMPLETE: Failed to complete OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth completion failed: {str(e)}")


@oauth_router.post("/complete-auth")
async def complete_oauth_with_token(request: Request):
    """Complete OAuth flow using Supabase access token from client"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        data = await request.json()
        access_token = data.get('access_token')
        oauth_session = data.get('oauth_session')
        
        logger.info(f"🔄 OAuth completion with token for session: {oauth_session}")
        
        if not access_token or not oauth_session:
            logger.error("❌ Missing access_token or oauth_session")
            return {"error": "Missing required parameters"}
        
        if oauth_session not in auth_sessions:
            logger.error(f"❌ Invalid OAuth session: {oauth_session}")
            return {"error": "Invalid OAuth session"}
        
        # Get user info from Supabase using the access token
        from app.auth import get_service_client
        supabase = await get_service_client()
        
        # Use the access token to get user info
        try:
            user_response = supabase.auth.get_user(access_token)
            if not user_response.user:
                logger.error("❌ Invalid Supabase token")
                return {"error": "Invalid authentication token"}
            
            current_user = user_response.user
            logger.info(f"✅ Retrieved user from token: {current_user.email}")
            
        except Exception as e:
            logger.error(f"❌ Failed to get user from token: {e}")
            return {"error": "Failed to validate authentication token"}
        
        # Get session data
        session_data = auth_sessions[oauth_session]
        client_id = session_data["client_id"]
        redirect_uri = session_data["redirect_uri"]
        state = session_data["state"]
        
        # Generate authorization code
        auth_code = secrets.token_urlsafe(32)
        
        # Get the internal User.id from database
        from app.database import SessionLocal
        from app.models import User
        
        db = SessionLocal()
        try:
            internal_user = db.query(User).filter(User.user_id == str(current_user.id)).first()
            if not internal_user:
                logger.error(f"❌ No internal User found for Supabase user_id: {current_user.id}")
                return {"error": "User not found in database"}
            
            internal_user_id = str(internal_user.id)
            logger.info(f"✅ Mapped Supabase user {current_user.id} to internal user {internal_user_id}")
            
        finally:
            db.close()
        
        # Store auth code with user info and PKCE challenge
        auth_sessions[auth_code] = {
            **session_data,
            "user_id": internal_user_id,
            "supabase_user_id": str(current_user.id),
            "email": current_user.email,
            "code": auth_code,
            "authorized_at": time.time(),
            "client_id": client_id
        }
        
        # Clean up original session
        del auth_sessions[oauth_session]
        
        # Build redirect URL back to Claude
        params = {
            "code": auth_code,
            "state": state
        }
        redirect_url = f"{redirect_uri}?{urlencode(params)}"
        logger.info(f"🎯 OAuth completion successful - redirecting to Claude: {redirect_url}")
        
        return {"redirect_url": redirect_url}
        
    except Exception as e:
        logger.error(f"❌ OAuth completion failed: {e}")
        return {"error": f"OAuth completion failed: {str(e)}"}


@oauth_router.get("/callback")
async def oauth_callback(
    request: Request,
    oauth_session: str,
    flow: Optional[str] = None
):
    """OAuth callback endpoint to handle Supabase authentication and set cookies"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"OAuth callback received for session: {oauth_session}, flow: {flow}")
    
    # Handle different auth flows
    if flow != "mcp_oauth":
        # This is a regular app login, redirect to main app
        logger.info("Regular app login detected - redirecting to main app")
        return RedirectResponse(url="https://jeanmemory.com")
    
    # Check if the session exists (MCP OAuth flow)
    if oauth_session not in auth_sessions:
        logger.error(f"Invalid OAuth session: {oauth_session}")
        raise HTTPException(status_code=400, detail="Invalid OAuth session")
    
    # Get the session data to build the complete authorize URL
    session_data = auth_sessions[oauth_session]
    
    # Build the complete authorize URL with all original OAuth parameters
    authorize_params = {
        "client_id": session_data["client_id"],
        "redirect_uri": session_data["redirect_uri"],
        "response_type": "code",
        "state": session_data["state"],
        "scope": session_data.get("scope", "read write"),
        "oauth_session": oauth_session
    }
    
    # Add PKCE parameters if present
    if session_data.get("code_challenge"):
        authorize_params["code_challenge"] = session_data["code_challenge"]
        authorize_params["code_challenge_method"] = session_data.get("code_challenge_method", "S256")
    
    # Build the complete authorize URL
    authorize_url_with_params = f"/oauth/authorize?{urlencode(authorize_params)}"
    logger.info(f"🎯 Complete authorize URL with all parameters: {authorize_url_with_params}")
    
    # Read the HTML template from the file
    try:
        with open("app/static/oauth_callback.html", "r") as f:
            html_template = f.read()
    except FileNotFoundError:
        logger.error("FATAL: oauth_callback.html template not found!")
        raise HTTPException(status_code=500, detail="Server misconfiguration: missing OAuth template.")

    # Replace placeholders with actual values
    html_content = html_template.replace("{{SUPABASE_URL}}", config.SUPABASE_URL)
    html_content = html_content.replace("{{SUPABASE_ANON_KEY}}", config.SUPABASE_ANON_KEY)
    html_content = html_content.replace("{{AUTHORIZE_URL}}", authorize_url_with_params)
    
    return HTMLResponse(content=html_content)


@oauth_router.post("/token")
async def token_exchange(
    grant_type: str = Form(...),
    code: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    scope: Optional[str] = Form(None)
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
    
    # Create access token with MCP scopes
    requested_scopes = (scope or "mcp:tools mcp:resources mcp:prompts").split()
    access_token = create_access_token(
        user_id=auth_data["user_id"],
        email=auth_data["email"],
        client_name="claude",
        scopes=requested_scopes
    )
    
    logger.info(f"Created access token for user {auth_data['email']}")
    
    # Clean up auth code
    del auth_sessions[code]
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": " ".join(requested_scopes)
    }


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Extract user from JWT token"""
    
    logger.error(f"🔥🔥🔥 GET_CURRENT_USER CALLED:")
    logger.error(f"   - Credentials type: {type(credentials)}")
    logger.error(f"   - Credentials scheme: {getattr(credentials, 'scheme', 'unknown')}")
    logger.error(f"   - Token length: {len(getattr(credentials, 'credentials', '')) if credentials else 0}")
    logger.error(f"   - Token preview: {getattr(credentials, 'credentials', '')[:50] if credentials else 'None'}...")
    
    try:
        # Try to decode with audience validation first (for new tokens)
        try:
            payload = jwt.decode(
                credentials.credentials, 
                JWT_SECRET, 
                algorithms=[JWT_ALGORITHM],
                audience="jean-memory-mcp",
                issuer="https://jean-memory-api-virginia.onrender.com",
                options={"verify_aud": True, "verify_iss": True}
            )
            logger.info("✅ JWT decoded with full validation (aud + iss)")
        except (jwt.InvalidAudienceError, jwt.InvalidIssuerError, jwt.MissingRequiredClaimError) as e:
            # Fallback for tokens without audience/issuer claims (legacy tokens)
            logger.warning(f"⚠️ JWT validation failed ({type(e).__name__}), trying legacy decode...")
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            logger.warning("⚠️ JWT decoded without audience/issuer validation (legacy token)")
            
        email: str = payload.get("email")
        user_id: str = payload.get("sub")
        client: str = payload.get("client") # Client name from token
        
        if email is None or user_id is None:
            logger.error("Token missing email or sub claim")
            raise credentials_exception
            
        logger.info(f"✅ JWT successfully decoded for user: {email}")
        logger.info(f"   - Supabase User ID (sub): {user_id}")
        logger.info(f"   - Client: {client}")
        
        # Extract and validate scopes
        scopes = payload.get("scope", "").split()
        logger.info(f"   - Scopes: {scopes}")
        
        # Validate MCP scopes (allow legacy scopes for backward compatibility)
        valid_mcp_scopes = {"mcp:tools", "mcp:resources", "mcp:prompts"}
        legacy_scopes = {"read", "write"}
        
        has_mcp_scopes = any(scope in valid_mcp_scopes for scope in scopes)
        has_legacy_scopes = any(scope in legacy_scopes for scope in scopes)
        
        if not (has_mcp_scopes or has_legacy_scopes):
            logger.error(f"Invalid scopes: {scopes}")
            raise credentials_exception
        
        # Log scope usage for debugging
        if has_legacy_scopes and has_mcp_scopes:
            logger.info(f"Using hybrid scopes (legacy + MCP): {scopes}")
        elif has_legacy_scopes and not has_mcp_scopes:
            logger.warning(f"Using legacy scopes only: {scopes}. Consider updating to MCP scopes.")
        else:
            logger.info(f"Using MCP scopes: {scopes}")

        return {
            "user_id": user_id, 
            "email": email, 
            "client": client,
            "scopes": scopes
        }
        
    except Exception as e:
        logger.error(f"JWT Error: {e}", exc_info=True)
        raise credentials_exception