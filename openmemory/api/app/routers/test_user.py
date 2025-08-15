"""
Auto Test User API - Creates test users automatically for new API keys
Makes onboarding incredibly simple: install SDK → use immediately
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional
import hashlib
import logging
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Test User Auto-Creation"])

class TestUserResponse(BaseModel):
    user_token: str
    message: str
    is_new_user: bool

@router.get("/test-user")
async def get_or_create_test_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TestUserResponse:
    """
    Get or create a test user automatically based on the API key.
    Each API key gets its own consistent test user for simple onboarding.
    
    This endpoint:
    1. Takes the API key from auth
    2. Derives a consistent test user ID from the API key
    3. Creates the test user if it doesn't exist
    4. Returns the test user token
    
    Makes the SDK experience: install → use immediately (no auth setup)
    """
    try:
        # Get API key from the authenticated user context
        api_key = getattr(current_user, 'api_key_used', None)
        if not api_key:
            # Fallback: try to get from Authorization header
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer jean_sk_'):
                api_key = auth_header.replace('Bearer ', '')
            else:
                raise HTTPException(400, "Could not determine API key for test user creation")
        
        # Create consistent test user ID from API key
        # Same API key always gets same test user
        api_key_hash = hashlib.md5(api_key.encode()).hexdigest()[:12]
        test_user_id = f"test_user_{api_key_hash}"
        
        # Check if test user already exists
        existing_user = db.query(User).filter(User.user_id == test_user_id).first()
        
        if existing_user:
            logger.info(f"Returning existing test user: {test_user_id}")
            return TestUserResponse(
                user_token=test_user_id,
                message="Using existing test user for this API key",
                is_new_user=False
            )
        
        # Create new test user
        new_test_user = User(
            user_id=test_user_id,
            email=f"{test_user_id}@test.jeanmemory.com"
        )
        
        db.add(new_test_user)
        db.commit()
        db.refresh(new_test_user)
        
        logger.info(f"Created new test user: {test_user_id} for API key: {api_key[-8:]}")
        
        return TestUserResponse(
            user_token=test_user_id,
            message="Created new test user for this API key",
            is_new_user=True
        )
        
    except Exception as e:
        logger.error(f"Failed to create test user: {e}")
        raise HTTPException(500, f"Failed to create test user: {str(e)}")

@router.get("/test-user/info")
async def get_test_user_info(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get information about the test user associated with this API key.
    Useful for debugging and understanding the auto-test-user system.
    """
    try:
        # Same logic as above to derive test user ID
        api_key = getattr(current_user, 'api_key_used', 'unknown')
        api_key_hash = hashlib.md5(api_key.encode()).hexdigest()[:12]
        test_user_id = f"test_user_{api_key_hash}"
        
        return {
            "test_user_id": test_user_id,
            "api_key_suffix": api_key[-8:] if len(api_key) >= 8 else "unknown",
            "description": "This test user is automatically created for your API key",
            "usage": "All SDK calls without explicit user tokens will use this test user",
            "isolation": "Each API key gets its own test user with isolated memory space"
        }
        
    except Exception as e:
        return {"error": f"Could not get test user info: {str(e)}"}