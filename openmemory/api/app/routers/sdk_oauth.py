"""
SDK OAuth Router - Provides /sdk/oauth/* endpoints for the React SDK

This router wraps the existing OAuth implementation to provide the endpoints
that the Jean Memory React SDK expects for the "Sign in with Jean" flow.
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.oauth_simple_new import (
    oauth_router as base_oauth_router,
    auth_sessions,
    JWT_SECRET,
    JWT_ALGORITHM,
    credentials_exception,
    bearer_scheme
)
from app.auth import get_current_supa_user

logger = logging.getLogger(__name__)

sdk_oauth_router = APIRouter(prefix="/sdk/oauth", tags=["sdk-oauth"])

@sdk_oauth_router.get("/authorize")
async def sdk_authorize(request: Request):
    """
    OAuth authorization endpoint for React SDK
    Redirects to the existing OAuth authorize endpoint
    """
    # Forward all query parameters to the existing OAuth endpoint
    query_string = str(request.query_params)
    oauth_url = f"/oauth/authorize?{query_string}"
    
    logger.info(f"SDK OAuth authorize request, forwarding to: {oauth_url}")
    
    # Use RedirectResponse to forward to existing OAuth endpoint
    return RedirectResponse(
        url=oauth_url,
        status_code=302
    )

@sdk_oauth_router.post("/token")
async def sdk_token(request: Request):
    """
    OAuth token exchange endpoint for React SDK
    Forwards to the existing OAuth token endpoint
    """
    # Get the request body
    body = await request.body()
    
    # Forward the request to existing OAuth token endpoint
    from fastapi import Request as FastAPIRequest
    from fastapi.datastructures import FormData
    import json
    
    try:
        # Parse JSON body
        json_data = json.loads(body)
        
        # Convert to form data for the existing endpoint
        
        logger.info(f"SDK OAuth token request for client_id: {json_data.get('client_id')}")
        
        # Call the existing token endpoint directly
        from app.oauth_simple_new import token_exchange
        
        response = await token_exchange(
            grant_type=json_data.get('grant_type'),
            client_id=json_data.get('client_id'), 
            code=json_data.get('code'),
            redirect_uri=json_data.get('redirect_uri'),
            code_verifier=json_data.get('code_verifier'),
            scope=json_data.get('scope')
        )
        
        return response
        
    except Exception as e:
        logger.error(f"SDK OAuth token error: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid token request"
        )

@sdk_oauth_router.get("/userinfo")
async def sdk_userinfo(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    OAuth userinfo endpoint for React SDK
    Returns user information from the JWT token
    """
    try:
        # Get token from Bearer header
        token = credentials.credentials
        
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Extract user information
        user_info = {
            "sub": payload.get("sub"),  # User ID
            "email": payload.get("email"),
            "name": payload.get("name", payload.get("email", "")),
            "given_name": payload.get("given_name", ""),
            "family_name": payload.get("family_name", ""),
            "picture": payload.get("picture", ""),
            "email_verified": True  # Assume verified if we have the token
        }
        
        logger.info(f"SDK OAuth userinfo request for user: {user_info['sub']}")
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        logger.error("SDK OAuth userinfo: Token expired")
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        logger.error("SDK OAuth userinfo: Invalid token")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"SDK OAuth userinfo error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )