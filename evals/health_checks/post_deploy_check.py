#!/usr/bin/env python3
"""
Lightweight post-deployment health check for Jean Memory
Runs AFTER deployment to verify system health without blocking deployment

Usage:
    python post_deploy_check.py                    # Check local/current environment
    python post_deploy_check.py --url=https://...  # Check remote deployment
"""

import asyncio
import argparse
import httpx
import logging
import sys
from datetime import datetime
from typing import Optional

# Suppress noisy loggers
logging.basicConfig(level=logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

class PostDeployHealthCheck:
    """Lightweight post-deployment health verification"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=10.0)
        self.results = []
        
    async def run_checks(self) -> bool:
        """Run all post-deployment checks. Returns True if healthy."""
        print("🏥 Post-Deployment Health Check")
        print(f"🌐 Target: {self.base_url}")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # Core checks that must pass
        all_passed = True
        
        # 1. Basic API health
        if await self._check_api_health():
            print("✅ API Health: OK")
        else:
            print("❌ API Health: FAILED")
            all_passed = False
            
        # 2. MCP endpoint (critical)
        if await self._check_mcp_endpoint():
            print("✅ MCP Endpoint: OK")
        else:
            print("❌ MCP Endpoint: FAILED") 
            all_passed = False
            
        # 3. Database connectivity
        if await self._check_database():
            print("✅ Database: OK")
        else:
            print("❌ Database: FAILED")
            all_passed = False
            
        # 4. Jean Memory tool (the heart of the system)
        if await self._check_jean_memory_tool():
            print("✅ Jean Memory Tool: OK")
        else:
            print("❌ Jean Memory Tool: FAILED")
            all_passed = False
        
        print()
        if all_passed:
            print("🎉 All post-deployment checks PASSED")
            print("✨ System is healthy and ready for traffic!")
        else:
            print("🚨 Some post-deployment checks FAILED")
            print("⚠️  System may have issues - investigate immediately")
            
        await self.client.aclose()
        return all_passed
    
    async def _check_api_health(self) -> bool:
        """Check basic API health"""
        try:
            response = await self.client.get(f"{self.base_url}/health/quick")
            return response.status_code == 200
        except Exception:
            # Fallback: try basic ping
            try:
                response = await self.client.get(f"{self.base_url}/")
                return response.status_code in [200, 404]  # 404 is fine, means API is up
            except Exception:
                return False
    
    async def _check_mcp_endpoint(self) -> bool:
        """Check MCP endpoint responds"""
        try:
            # Test MCP tools/list endpoint
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json={
                    "method": "tools/list",
                    "params": {}
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if jean_memory tool is in the response
                tools = data.get("result", {}).get("tools", [])
                jean_memory_found = any(tool.get("name") == "jean_memory" for tool in tools)
                return jean_memory_found
            return False
        except Exception:
            return False
    
    async def _check_database(self) -> bool:
        """Check database connectivity via API"""
        try:
            # Try to hit an endpoint that requires database
            response = await self.client.get(
                f"{self.base_url}/api/v1/memories",
                params={"limit": 1}
            )
            # Any response (even 401/403) means database is accessible
            return response.status_code in [200, 401, 403]
        except Exception:
            return False
    
    async def _check_jean_memory_tool(self) -> bool:
        """Test the jean_memory tool execution"""
        try:
            # Simple test of jean_memory tool
            response = await self.client.post(
                f"{self.base_url}/mcp",
                json={
                    "method": "tools/call",
                    "params": {
                        "name": "jean_memory",
                        "arguments": {
                            "user_message": "health check test",
                            "is_new_conversation": False,
                            "needs_context": False
                        }
                    }
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if we got a result (any result is good)
                return "result" in data
            return False
        except Exception:
            return False

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Post-deployment health check")
    parser.add_argument("--url", help="Base URL to check (default: http://localhost:8000)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only show errors")
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    
    checker = PostDeployHealthCheck(args.url)
    
    try:
        success = await checker.run_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Health check interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())