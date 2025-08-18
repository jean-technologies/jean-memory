"""
Authentication Configuration for Jean Memory Evaluation Framework

This module provides configuration and helper functions for authenticated
testing with the Jean Memory API.
"""

import os
from typing import Optional
from .auth_helper import SecureTokenManager


class AuthConfig:
    """Authentication configuration for evaluation framework"""
    
    def __init__(self):
        self.api_base_url = "https://jean-memory-api-virginia.onrender.com"
        self.token_manager = SecureTokenManager()
        self._cached_token: Optional[str] = None
    
    def get_auth_headers(self, password: Optional[str] = None) -> dict:
        """Get authentication headers for API requests"""
        token = self.get_token(password)
        if token:
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}
    
    def get_token(self, password: Optional[str] = None) -> Optional[str]:
        """Get authentication token (cached)"""
        if self._cached_token is None:
            self._cached_token = self.token_manager.load_token(password)
        return self._cached_token
    
    def is_authenticated(self) -> bool:
        """Check if authentication is available"""
        return self.token_manager.token_exists()
    
    async def validate_auth(self) -> bool:
        """Validate current authentication"""
        return await self.token_manager.validate_token()
    
    def clear_cache(self):
        """Clear cached token"""
        self._cached_token = None


# Global auth config instance
auth_config = AuthConfig()


def get_auth_headers(password: Optional[str] = None) -> dict:
    """Get authentication headers for API requests"""
    return auth_config.get_auth_headers(password)


def is_authenticated() -> bool:
    """Check if authentication is available"""
    return auth_config.is_authenticated()


async def validate_auth() -> bool:
    """Validate current authentication"""
    return await auth_config.validate_auth()