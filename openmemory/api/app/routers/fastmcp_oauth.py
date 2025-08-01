"""
FastAPI router for FastMCP OAuth integration.
This provides a clean integration point with our existing FastAPI application.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.mcp_fastmcp_oauth import get_fastmcp_oauth_app

logger = logging.getLogger(__name__)

# Create router for FastMCP OAuth endpoints
fastmcp_router = APIRouter(prefix="/fastmcp", tags=["fastmcp-oauth"])

@fastmcp_router.get("/status")
async def fastmcp_status():
    """Status endpoint for FastMCP OAuth implementation"""
    try:
        # Check if dependencies are available
        from app.mcp_fastmcp_oauth import FASTMCP_AVAILABLE, MCPAUTH_AVAILABLE
        
        status = "ready" if (FASTMCP_AVAILABLE and MCPAUTH_AVAILABLE) else "partial"
        implementation = "fastmcp + mcpauth" if (FASTMCP_AVAILABLE and MCPAUTH_AVAILABLE) else "fallback"
        
        return {
            "status": status,
            "implementation": implementation,
            "oauth_version": "2.1",
            "fastmcp_available": FASTMCP_AVAILABLE,
            "mcpauth_available": MCPAUTH_AVAILABLE,
            "specs": [
                "RFC 7591 - Dynamic Client Registration",
                "RFC 9728 - Protected Resource Metadata", 
                "RFC 8707 - Resource Indicators",
                "OAuth 2.1 with PKCE"
            ],
            "endpoints": {
                "oauth_discovery": "/.well-known/oauth-authorization-server",
                "protected_resource": "/.well-known/oauth-protected-resource",
                "mcp_endpoint": "/mcp"
            }
        }
    except Exception as e:
        logger.error(f"FastMCP status check failed: {e}")
        return {
            "status": "error",
            "implementation": "unknown",
            "error": str(e)
        }

@fastmcp_router.get("/test-oauth")
async def test_oauth_config():
    """Test OAuth configuration and endpoints"""
    try:
        app = get_fastmcp_oauth_app()
        
        # Get the routes to verify endpoints are registered
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append({
                    "path": route.path,
                    "methods": getattr(route, 'methods', [])
                })
        
        return {
            "status": "oauth_configured",
            "routes_registered": len(routes),
            "key_routes": [r for r in routes if 'oauth' in r['path'] or 'mcp' in r['path']],
            "fastmcp_app": "initialized"
        }
    except Exception as e:
        logger.error(f"OAuth config test failed: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth test failed: {str(e)}")

# Health check for the FastMCP implementation
@fastmcp_router.get("/health")
async def fastmcp_health():
    """Health check for FastMCP OAuth server"""
    try:
        app = get_fastmcp_oauth_app()
        return {
            "status": "healthy",
            "fastmcp": "ready",
            "oauth": "enabled",
            "timestamp": "2025-07-31"
        }
    except Exception as e:
        logger.error(f"FastMCP health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "implementation": "fastmcp"
            }
        )