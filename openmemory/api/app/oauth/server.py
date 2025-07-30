"""OAuth 2.0 server implementation"""

import os
import secrets
import time
from typing import Optional, Dict
from urllib.parse import urlencode, urlparse
from fastapi import APIRouter, Request, HTTPException, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import logging

from .jwt_utils import create_access_token, create_refresh_token, validate_token
from .clients import client_registry
from app.auth import supabase_service_client
from app.settings import config

logger = logging.getLogger(__name__)

oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])

# Temporary storage (use Redis in production)
auth_sessions: Dict[str, Dict] = {}

BASE_URL = config.API_BASE_URL


@oauth_router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth 2.0 discovery endpoint"""
    
    return {
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/oauth/authorize",
        "token_endpoint": f"{BASE_URL}/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
        "scopes_supported": ["read", "write"],
    }


@oauth_router.post("/register")
async def dynamic_client_registration(request: Request):
    """Dynamic client registration - Claude auto-registers here"""
    
    try:
        data = await request.json()
        logger.info(f"Client registration request: {data}")
        
        # Extract registration data
        client_name = data.get("client_name", "Unknown Client")
        redirect_uris = data.get("redirect_uris", [])
        grant_types = data.get("grant_types", ["authorization_code"])
        
        # Detect Claude by redirect URI or client name
        client_type = "claude" if (
            any("claude.ai" in uri or "anthropic.com" in uri for uri in redirect_uris) or 
            "claude" in client_name.lower()
        ) else "unknown"
        
        # For Claude, use a fixed client ID for consistency
        if client_type == "claude":
            client_id = "claude-ai"
            # Update existing Claude client or create if doesn't exist
            if client_id in client_registry.clients:
                client = client_registry.clients[client_id]
                # Update redirect URIs to include new ones
                for uri in redirect_uris:
                    if uri not in client.redirect_uris:
                        client.redirect_uris.append(uri)
            else:
                client = client_registry.register_client(
                    client_name=client_name,
                    client_type=client_type,
                    redirect_uris=redirect_uris,
                    allowed_scopes=["read", "write"]
                )
                client.client_id = client_id
                client_registry.clients[client_id] = client
        else:
            # Dynamic registration for other clients
            client = client_registry.register_client(
                client_name=client_name,
                client_type=client_type,
                redirect_uris=redirect_uris,
                allowed_scopes=data.get("scope", "read write").split()
            )
        
        logger.info(f"Registered client: {client.client_id} ({client.client_name})")
        
        # Return RFC 7591 compliant response
        response = {
            "client_id": client.client_id,
            "client_name": client.client_name,
            "redirect_uris": client.redirect_uris,
            "grant_types": grant_types,
            "scope": " ".join(client.allowed_scopes),
            "token_endpoint_auth_method": "none"  # Public client
        }
        
        # Add client_secret if required (though Claude uses public client flow)
        if data.get("token_endpoint_auth_method") == "client_secret_basic":
            response["client_secret"] = "not-required-for-pkce"
        
        return response
        
    except Exception as e:
        logger.error(f"Client registration error: {e}")
        raise HTTPException(status_code=400, detail="Invalid registration request")


@oauth_router.get("/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str,
    state: str,
    scope: Optional[str] = "read write",
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256"
):
    """OAuth authorization endpoint - shows login page"""
    
    # Validate client
    client = client_registry.get_client(client_id)
    if not client:
        raise HTTPException(status_code=400, detail="Invalid client")
    
    # Validate redirect URI
    if not client_registry.validate_redirect_uri(client_id, redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect URI")
    
    # Validate response type
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response type")
    
    # Create session
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
    
    # Return login page (redirects to existing Jean Memory auth)
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Connect to Jean Memory</title>
        <script>
            // Store session for after login
            localStorage.setItem('oauth_session', '{session_id}');
            localStorage.setItem('oauth_client', '{client.client_name}');
            
            // Redirect to Jean Memory login with return URL
            const returnUrl = encodeURIComponent('{BASE_URL}/oauth/callback');
            window.location.href = 'https://app.jeanmemory.com/auth?return_url=' + returnUrl;
        </script>
    </head>
    <body>
        <p>Redirecting to Jean Memory login...</p>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@oauth_router.get("/callback")
async def oauth_callback(request: Request):
    """Handle callback after Jean Memory login"""
    
    # This page runs in the user's browser after they log in to Jean Memory
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Completing authorization...</title>
    </head>
    <body>
        <script>
            // Get stored session
            const sessionId = localStorage.getItem('oauth_session');
            const clientName = localStorage.getItem('oauth_client');
            
            // Check if user is logged in to Jean Memory
            // This would need to communicate with Jean Memory frontend
            // For now, we'll show a completion form
            
            if (sessionId) {
                // In production, this would verify the Jean Memory session
                // and automatically complete the OAuth flow
                window.location.href = `/oauth/complete?session_id=${sessionId}`;
            } else {
                alert('Authorization failed - session lost');
                window.close();
            }
        </script>
        <p>Completing authorization...</p>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@oauth_router.get("/complete")
async def complete_authorization(session_id: str, request: Request):
    """Complete OAuth flow after successful Jean Memory login"""
    
    # Get session
    session = auth_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    # Get user info from Supabase session
    # Check for Supabase session cookie or token
    try:
        from app.auth import get_user_from_supabase_session
        
        # Try to get user from Supabase session
        user = await get_user_from_supabase_session(request)
        if user and hasattr(user, 'user_id') and hasattr(user, 'email'):
            user_id = str(user.user_id)
            email = user.email
        else:
            # Fallback for testing - check for manual auth headers
            user_id = request.headers.get("x-user-id")
            email = request.headers.get("x-user-email")
            
            if not user_id or not email:
                # No valid user session found
                raise HTTPException(
                    status_code=401,
                    detail="User not authenticated. Please log in to Jean Memory first."
                )
    except ImportError:
        # Fallback if auth module not available
        user_id = request.headers.get("x-user-id", "test-user-id")
        email = request.headers.get("x-user-email", "test@example.com")
    
    # Generate authorization code
    auth_code = secrets.token_urlsafe(32)
    
    # Store auth code with user info
    auth_sessions[auth_code] = {
        **session,
        "user_id": user_id,
        "email": email,
        "code": auth_code,
        "created_at": time.time()
    }
    
    # Clean up original session
    del auth_sessions[session_id]
    
    # Redirect back to client with auth code
    params = {
        "code": auth_code,
        "state": session["state"]
    }
    redirect_url = f"{session['redirect_uri']}?{urlencode(params)}"
    
    return RedirectResponse(url=redirect_url)


@oauth_router.post("/token")
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
        
        # Get auth data
        auth_data = auth_sessions.get(code)
        if not auth_data or "user_id" not in auth_data:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        # Validate client
        if auth_data["client_id"] != client_id:
            raise HTTPException(status_code=400, detail="Client mismatch")
        
        # TODO: Validate PKCE if provided
        
        # Get client info
        client = client_registry.get_client(client_id)
        if not client:
            raise HTTPException(status_code=400, detail="Invalid client")
        
        # Create tokens
        access_token = create_access_token(
            user_id=auth_data["user_id"],
            email=auth_data["email"],
            client_name=client.client_type,
            scope=auth_data.get("scope", "read write")
        )
        
        refresh_token_value = create_refresh_token(
            user_id=auth_data["user_id"],
            email=auth_data["email"],
            client_name=client.client_type
        )
        
        # Clean up auth code
        del auth_sessions[code]
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token_value,
            "scope": auth_data.get("scope", "read write")
        }
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Missing refresh token")
        
        try:
            # Validate refresh token
            payload = validate_token(refresh_token, token_type="refresh")
            
            # Create new access token
            access_token = create_access_token(
                user_id=payload["sub"],
                email=payload["email"],
                client_name=payload["client"],
                scope="read write"  # Use original scope in production
            )
            
            return {
                "access_token": access_token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "read write"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid refresh token")
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant type")


# Cleanup expired sessions periodically
async def cleanup_expired_sessions():
    """Remove expired auth sessions"""
    
    current_time = time.time()
    expired = []
    
    for session_id, data in auth_sessions.items():
        # Sessions expire after 10 minutes
        if current_time - data["created_at"] > 600:
            expired.append(session_id)
    
    for session_id in expired:
        del auth_sessions[session_id] 