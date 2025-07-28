from .claude import ClaudeProfile
from .base import BaseClient

class CursorClient(BaseClient):
    """Client for Cursor."""
    def get_client_name(self) -> str:
        return "cursor"
    
    def get_client_profile(self):
        return CursorProfile()

class CursorProfile(ClaudeProfile):
    """Cursor uses the same tool profile as Claude."""
    pass 