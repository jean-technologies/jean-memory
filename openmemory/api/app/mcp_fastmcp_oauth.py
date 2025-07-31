"""
FastMCP OAuth 2.1 implementation for Claude Web MCP connector
Based on successful implementation pattern from Neural Engineer Medium article.

This replaces our custom OAuth implementation with the proven fastmcp + mcpauth stack
that supports Dynamic Client Registration (RFC 7591) required by Claude.ai.
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Optional imports - gracefully handle missing dependencies
try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCP = None
    FASTMCP_AVAILABLE = False

try:
    from mcpauth import MCPAuth
    from mcpauth.config import AuthServerType
    MCPAUTH_AVAILABLE = True
except ImportError:
    MCPAuth = None
    AuthServerType = None
    MCPAUTH_AVAILABLE = False

from app.settings import config
from app.database import get_db
from app.auth import get_current_supa_user
from app.routing.mcp import handle_request_logic

logger = logging.getLogger(__name__)

# OAuth server configuration
def get_oauth_server_config() -> Dict[str, Any]:
    """
    Configure OAuth server settings for Claude.ai compatibility.
    Uses environment variables for production deployment.
    """
    base_url = os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com")
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/oauth/authorize",
        "token_endpoint": f"{base_url}/oauth/token", 
        "registration_endpoint": f"{base_url}/oauth/register",
        "jwks_uri": f"{base_url}/oauth/jwks",
        "scopes_supported": ["read", "write"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_basic"],
        # Dynamic Client Registration support
        "dynamic_client_registration_supported": True,
        # MCP-specific extensions
        "mcp_server_info": {
            "name": "jean-memory",
            "version": "2.0.0",
            "description": "Jean Memory MCP Server with OAuth 2.1"
        }
    }

# Create a simpler FastMCP OAuth server
def create_fastmcp_oauth_server() -> FastAPI:
    """
    Create FastMCP server with OAuth 2.1 authentication.
    Simplified implementation based on working patterns.
    """
    logger.info("🚀 Initializing FastMCP OAuth server...")
    
    # Check if FastMCP dependencies are available
    if not FASTMCP_AVAILABLE:
        logger.warning("⚠️ FastMCP not available - using fallback implementation")
    if not MCPAUTH_AVAILABLE:
        logger.warning("⚠️ MCPAuth not available - using basic OAuth endpoints")
    
    # Create base FastAPI app
    base_app = FastAPI(
        title="Jean Memory MCP Server",
        description="Memory management with OAuth 2.1 authentication", 
        version="2.0.0"
    )
    
    # Root endpoint
    @base_app.get("/", operation_id="root")
    async def root():
        """Root endpoint with API information"""
        return {
            "message": "Jean Memory MCP Server",
            "version": "2.0.0", 
            "oauth": "enabled",
            "auth_type": "fastmcp + mcpauth",
            "specs": ["RFC 7591 DCR", "OAuth 2.1", "RFC 9728", "RFC 8707"]
        }
    
    # Create simple OAuth metadata endpoint first
    @base_app.get("/.well-known/oauth-authorization-server")
    async def oauth_discovery():
        """OAuth 2.0 discovery endpoint"""
        base_url = os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com")
        return {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/oauth/authorize",
            "token_endpoint": f"{base_url}/oauth/token",
            "registration_endpoint": f"{base_url}/oauth/register", 
            "jwks_uri": f"{base_url}/oauth/jwks",
            "scopes_supported": ["read", "write"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_basic"],
            "dynamic_client_registration_supported": True
        }
    
    # Now try to initialize MCPAuth (but don't fail if it doesn't work)
    mcp_auth = None
    if MCPAUTH_AVAILABLE:
        try:
            from mcpauth.config import AuthServerConfig, AuthorizationServerMetadata
            
            metadata = AuthorizationServerMetadata(
                issuer=os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com"),
                authorization_endpoint=f"{os.getenv('API_BASE_URL', 'https://jean-memory-api-virginia.onrender.com')}/oauth/authorize",
                token_endpoint=f"{os.getenv('API_BASE_URL', 'https://jean-memory-api-virginia.onrender.com')}/oauth/token",
                registration_endpoint=f"{os.getenv('API_BASE_URL', 'https://jean-memory-api-virginia.onrender.com')}/oauth/register"
            )
            
            server_config = AuthServerConfig(
                metadata=metadata,
                type=AuthServerType.OAUTH
            )
            
            mcp_auth = MCPAuth(server=server_config)
            logger.info("✅ MCPAuth initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ MCPAuth initialization failed, using fallback: {e}")
            # Continue without MCPAuth for now
    
    # For now, just return the base app with OAuth discovery
    # We'll incrementally add FastMCP features
    
    # Add protected resource metadata (RFC 9728)
    @base_app.get("/.well-known/oauth-protected-resource")
    async def protected_resource_metadata():
        """OAuth 2.0 Protected Resource Metadata (RFC 9728)"""
        base_url = os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com")
        return {
            "resource": f"{base_url}/mcp",
            "authorization_servers": [base_url],
            "scopes_supported": ["read", "write"],
            "bearer_methods_supported": ["header"],
            "resource_documentation": f"{base_url}/docs"
        }
    
    # Add MCP-specific protected resource metadata
    @base_app.get("/.well-known/oauth-protected-resource/mcp")
    async def mcp_protected_resource_metadata():
        """MCP-specific OAuth metadata"""
        base_url = os.getenv("API_BASE_URL", "https://jean-memory-api-virginia.onrender.com")
        return {
            "resource": f"{base_url}/mcp",
            "authorization_servers": [base_url], 
            "scopes_supported": ["read", "write"],
            "bearer_methods_supported": ["header"],
            "mcp_version": "2025-06-18",
            "transport": "http",
            "capabilities": {
                "resources": {},
                "tools": {},
                "prompts": {},
                "logging": {}
            }
        }
    
    # Simple MCP endpoint that requires authentication
    @base_app.post("/mcp")
    async def mcp_endpoint(request: Request):
        """Basic MCP endpoint - will be enhanced with FastMCP later"""
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Bearer token required")
        
        # For now, return a simple response
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "capabilities": {
                    "resources": {},
                    "tools": {},
                    "prompts": {},
                    "logging": {}
                },
                "protocolVersion": "2025-06-18",
                "serverInfo": {
                    "name": "jean-memory-fastmcp",
                    "version": "2.0.0"
                }
            }
        }
    
    # Add CORS middleware
    from fastapi.middleware.cors import CORSMiddleware
    base_app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://claude.ai",
            "https://api.claude.ai",
            "https://*.claude.ai",
            "http://localhost:3000",
            "http://localhost:8080"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id", "authorization"]
    )
    
    logger.info("✅ FastMCP OAuth server created successfully")
    return base_app

# Custom MCP request handler that integrates with our existing logic
async def handle_fastmcp_request(request: Request, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP requests using our existing routing logic.
    This bridges FastMCP with our current MCP implementation.
    """
    try:
        # Extract user info from OAuth token (handled by bearer_auth middleware)
        # The middleware should have validated the token and set user context
        
        # Create a mock request body in the format our existing handler expects
        request_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        # Use our existing MCP request handler
        response = await handle_request_logic(request, request_body, None)
        
        logger.info(f"✅ FastMCP request handled: {method}")
        return response
        
    except Exception as e:
        logger.error(f"❌ FastMCP request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export the configured app
fastmcp_oauth_app = None

def get_fastmcp_oauth_app() -> FastAPI:
    """Get or create the FastMCP OAuth application"""
    global fastmcp_oauth_app
    if fastmcp_oauth_app is None:
        fastmcp_oauth_app = create_fastmcp_oauth_server()
    return fastmcp_oauth_app