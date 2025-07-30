"""OAuth client registry and management"""

import secrets
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class OAuthClient(BaseModel):
    """OAuth client configuration"""
    
    client_id: str
    client_name: str
    client_type: str  # "claude", "chatgpt", "cursor", etc.
    redirect_uris: List[str]
    allowed_scopes: List[str] = ["read", "write"]
    created_at: datetime = datetime.utcnow()
    metadata: Dict = {}  # Client-specific config
    

class ClientRegistry:
    """Manages OAuth clients"""
    
    def __init__(self):
        self.clients: Dict[str, OAuthClient] = {}
        self._init_default_clients()
    
    def _init_default_clients(self):
        """Initialize known clients"""
        
        # Claude - Fixed client ID for well-known client
        claude_client = OAuthClient(
            client_id="claude-ai",  # Fixed ID for Claude
            client_name="Claude",
            client_type="claude",
            redirect_uris=[
                "https://claude.ai/api/mcp/auth_callback",
                "https://claude.anthropic.com/api/mcp/auth_callback"
            ],
            allowed_scopes=["read", "write"]
        )
        self.clients["claude-ai"] = claude_client
        
        # Future: ChatGPT
        # self.register_client(
        #     client_name="ChatGPT",
        #     client_type="chatgpt",
        #     redirect_uris=["https://chat.openai.com/auth/callback"]
        # )
        
        # Future: Cursor
        # self.register_client(
        #     client_name="Cursor",
        #     client_type="cursor",
        #     redirect_uris=["cursor://auth/callback"]
        # )
    
    def register_client(
        self,
        client_name: str,
        client_type: str,
        redirect_uris: List[str],
        allowed_scopes: List[str] = None
    ) -> OAuthClient:
        """Register a new OAuth client"""
        
        client_id = f"{client_type}_{secrets.token_urlsafe(16)}"
        
        client = OAuthClient(
            client_id=client_id,
            client_name=client_name,
            client_type=client_type,
            redirect_uris=redirect_uris,
            allowed_scopes=allowed_scopes or ["read", "write"]
        )
        
        self.clients[client_id] = client
        return client
    
    def get_client(self, client_id: str) -> Optional[OAuthClient]:
        """Get client by ID"""
        return self.clients.get(client_id)
    
    def validate_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """Validate if redirect URI is allowed for client"""
        
        client = self.get_client(client_id)
        if not client:
            return False
        
        # Exact match or prefix match for dynamic callbacks
        for allowed_uri in client.redirect_uris:
            if redirect_uri == allowed_uri or redirect_uri.startswith(allowed_uri + "?"):
                return True
        
        return False
    
    def validate_scope(self, client_id: str, requested_scope: str) -> bool:
        """Validate if scope is allowed for client"""
        
        client = self.get_client(client_id)
        if not client:
            return False
        
        requested_scopes = set(requested_scope.split())
        allowed_scopes = set(client.allowed_scopes)
        
        return requested_scopes.issubset(allowed_scopes)


# Global client registry
client_registry = ClientRegistry() 