"""
System-level health checks for Jean Memory
Tests API endpoints, authentication, and background services
"""

import asyncio
import os
import sys
import httpx
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add the API directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../openmemory/api'))

from .base import HealthCheck, HealthCheckResult

logger = logging.getLogger(__name__)

class SystemHealthCheck(HealthCheck):
    """System-level functionality health checks"""
    
    def __init__(self):
        super().__init__("System Components")
        
    def is_critical(self) -> bool:
        """System checks are critical for deployment"""
        return True
    
    async def run_checks(self, level: str = "critical") -> HealthCheckResult:
        """Run system-level health checks"""
        result = HealthCheckResult(self.name)
        
        # Core system checks
        await self._check_authentication_system(result)
        await self._check_background_tasks(result)
        
        # API endpoint checks (if comprehensive)
        if level == "comprehensive":
            await self._check_api_endpoints(result)
        
        return result
    
    async def _check_authentication_system(self, result: HealthCheckResult) -> None:
        """Check authentication system functionality"""
        try:
            # Test 1: Import auth modules
            try:
                from app.auth import get_current_user_or_api_key, verify_jwt_token
                from app.models import User
                result.add_check("Auth - Import", True, "Authentication modules imported successfully")
            except ImportError as e:
                result.add_check("Auth - Import", False, f"Auth import failed: {e}")
                return
            
            # Test 2: Supabase client initialization
            try:
                from app.auth import get_supabase_client
                supabase = get_supabase_client()
                if supabase:
                    result.add_check("Auth - Supabase Client", True, "Supabase client initialized")
                else:
                    result.add_check("Auth - Supabase Client", False, "Supabase client is None")
            except Exception as e:
                result.add_check("Auth - Supabase Client", False, f"Supabase client failed: {e}")
            
            # Test 3: API key validation system
            try:
                from app.auth import verify_api_key
                from app.models import User
                
                # Test with invalid key (should fail gracefully)
                invalid_result = await verify_api_key("invalid_key_test")
                if invalid_result is None:
                    result.add_check("Auth - API Key Validation", True, "API key validation working")
                else:
                    result.add_check("Auth - API Key Validation", False, "Invalid key validation failed")
            except Exception as e:
                result.add_check("Auth - API Key Validation", False, f"API key validation failed: {e}")
            
            # Test 4: Database user model
            try:
                from app.database import get_db
                from app.models import User
                from sqlalchemy import text
                
                # Test user table accessibility
                db = next(get_db())
                try:
                    db.execute(text("SELECT COUNT(*) FROM users LIMIT 1"))
                    result.add_check("Auth - User Database", True, "User database accessible")
                except Exception as e:
                    result.add_check("Auth - User Database", False, f"User database error: {e}")
                finally:
                    db.close()
                    
            except Exception as e:
                result.add_check("Auth - User Database", False, f"Database connection failed: {e}")
                
        except Exception as e:
            result.add_check("Auth - General", False, f"Unexpected auth error: {e}")
    
    async def _check_background_tasks(self, result: HealthCheckResult) -> None:
        """Check background task system functionality"""
        try:
            # Test 1: Import background task modules
            try:
                from fastapi import BackgroundTasks
                from app.context import background_tasks_var
                result.add_check("Background - Import", True, "Background task modules imported")
            except ImportError as e:
                result.add_check("Background - Import", False, f"Background import failed: {e}")
                return
            
            # Test 2: Background task execution test
            try:
                from fastapi import BackgroundTasks
                from app.context import background_tasks_var
                
                # Create a test background tasks instance
                bg_tasks = BackgroundTasks()
                
                # Test function that tracks execution
                execution_tracker = {"executed": False}
                
                def test_background_function():
                    execution_tracker["executed"] = True
                
                # Add the test task
                bg_tasks.add_task(test_background_function)
                
                # Set context and execute
                token = background_tasks_var.set(bg_tasks)
                try:
                    # Tasks execute when the response is sent, so we'll just test the setup
                    result.add_check("Background - Task Setup", True, "Background tasks can be configured")
                finally:
                    background_tasks_var.reset(token)
                    
            except Exception as e:
                result.add_check("Background - Task Setup", False, f"Background task setup failed: {e}")
            
            # Test 3: Background processor service
            try:
                from app.services.background_processor import BackgroundProcessor
                
                # Test processor initialization
                processor = BackgroundProcessor()
                if processor:
                    result.add_check("Background - Processor", True, "Background processor initialized")
                else:
                    result.add_check("Background - Processor", False, "Background processor is None")
                    
            except ImportError:
                result.add_warning("Background - Processor", "Background processor service not found (optional)")
            except Exception as e:
                result.add_check("Background - Processor", False, f"Background processor failed: {e}")
            
            # Test 4: Background sync service
            try:
                from app.services.background_sync import BackgroundSyncService
                
                # Test sync service initialization
                sync_service = BackgroundSyncService()
                if sync_service:
                    result.add_check("Background - Sync Service", True, "Background sync service initialized")
                else:
                    result.add_check("Background - Sync Service", False, "Background sync service is None")
                    
            except ImportError:
                result.add_warning("Background - Sync Service", "Background sync service not found (optional)")
            except Exception as e:
                result.add_check("Background - Sync Service", False, f"Background sync service failed: {e}")
                
        except Exception as e:
            result.add_check("Background - General", False, f"Unexpected background task error: {e}")
    
    async def _check_api_endpoints(self, result: HealthCheckResult) -> None:
        """Check critical API endpoints (comprehensive mode only)"""
        try:
            # This would typically test against a running server
            # For now, we'll just check that the router modules can be imported
            
            # Test 1: Import API routers
            try:
                from app.routers import memories, apps, agent_mcp
                result.add_check("API - Router Import", True, "API routers imported successfully")
            except ImportError as e:
                result.add_check("API - Router Import", False, f"Router import failed: {e}")
                return
            
            # Test 2: Check router dependencies
            try:
                from app.routers.memories import get_memories, create_memory
                from app.routers.apps import get_apps
                from app.routers.agent_mcp import mcp_endpoint
                result.add_check("API - Endpoint Functions", True, "API endpoint functions available")
            except ImportError as e:
                result.add_check("API - Endpoint Functions", False, f"Endpoint functions missing: {e}")
            
            # Test 3: Schema validation
            try:
                from app.schemas import MemoryCreate, MemoryResponse, AppResponse
                result.add_check("API - Schema Import", True, "API schemas imported successfully")
            except ImportError as e:
                result.add_check("API - Schema Import", False, f"Schema import failed: {e}")
            
            # Note: For actual endpoint testing, you'd make HTTP requests to a running server
            # This would be more appropriate for integration tests rather than health checks
            
        except Exception as e:
            result.add_check("API - General", False, f"Unexpected API error: {e}")