"""OAuth middleware for protecting endpoints"""

from typing import Optional, Dict
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_utils import validate_token

# Use FastAPI's built-in Bearer token security
bearer_scheme = HTTPBearer(auto_error=False)


class OAuthUser:
    """Represents an authenticated OAuth user"""
    
    def __init__(self, user_id: str, email: str, client: str, scope: str):
        self.user_id = user_id
        self.email = email
        self.client = client  # Which AI client (claude, chatgpt, etc)
        self.scope = scope
    
    def has_scope(self, required_scope: str) -> bool:
        """Check if user has required scope"""
        user_scopes = set(self.scope.split())
        return required_scope in user_scopes


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> OAuthUser:
    """Extract and validate the current user from JWT token"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate the JWT token
    try:
        payload = validate_token(credentials.credentials, token_type="access")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create user object from token payload
    return OAuthUser(
        user_id=payload["sub"],
        email=payload["email"],
        client=payload["client"],
        scope=payload.get("scope", "read")
    )


async def oauth_required(
    request: Request,
    user: OAuthUser = Depends(get_current_user)
) -> OAuthUser:
    """Dependency to require OAuth authentication"""
    
    # Store user and client info in request state for downstream use
    request.state.oauth_user = user
    request.state.oauth_client = user.client
    
    return user


async def require_scope(scope: str):
    """Dependency factory to require specific OAuth scopes"""
    
    async def check_scope(user: OAuthUser = Depends(get_current_user)) -> OAuthUser:
        if not user.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient scope. Required: {scope}"
            )
        return user
    
    return check_scope 