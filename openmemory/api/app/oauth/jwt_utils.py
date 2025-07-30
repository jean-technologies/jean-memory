"""JWT token utilities for OAuth 2.0"""

import os
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, status

# Get secret from environment or generate a secure one
JWT_SECRET = os.getenv("JWT_SECRET_KEY", os.getenv("ADMIN_SECRET_KEY", "your-secret-key-here"))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(
    user_id: str,
    email: str,
    client_name: str,
    scope: str = "read write"
) -> str:
    """Create a JWT access token"""
    
    now = datetime.utcnow()
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "sub": user_id,                    # Subject (user ID)
        "email": email,                    # User email
        "client": client_name,             # Which AI client (claude, chatgpt, etc)
        "scope": scope,                    # Permissions
        "type": "access",                  # Token type
        "iat": now.timestamp(),            # Issued at
        "exp": expire.timestamp(),         # Expiry
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    email: str,
    client_name: str
) -> str:
    """Create a JWT refresh token"""
    
    now = datetime.utcnow()
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "email": email,
        "client": client_name,
        "type": "refresh",
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
    }
    
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict:
    """Decode and validate a JWT token"""
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def validate_token(token: str, token_type: str = "access") -> Dict:
    """Validate a token and check its type"""
    
    payload = decode_token(token)
    
    if payload.get("type") != token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected {token_type}"
        )
    
    return payload 