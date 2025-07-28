"""
Health check endpoint for Jean Memory API
Provides real-time health monitoring after deployment

To integrate into your FastAPI app, add this to main.py:

from evals.health_checks.health_endpoint import health_router
app.include_router(health_router, prefix="/health")

Then access via:
GET /health - Basic health status
GET /health/detailed - Detailed health information
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Import our health check modules
try:
    from checks.base import HealthCheckRunner
    from checks.database_checks import DatabaseHealthCheck
    from checks.external_service_checks import ExternalServiceHealthCheck
    from checks.mcp_tools_checks import MCPToolsHealthCheck
    from checks.system_checks import SystemHealthCheck
except ImportError:
    # Fallback for when running from API directory
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__)))
    from checks.base import HealthCheckRunner
    from checks.database_checks import DatabaseHealthCheck
    from checks.external_service_checks import ExternalServiceHealthCheck
    from checks.mcp_tools_checks import MCPToolsHealthCheck
    from checks.system_checks import SystemHealthCheck

# Suppress noisy loggers for health checks
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('neo4j').setLevel(logging.WARNING)

health_router = APIRouter(tags=["health"])

class HealthStatus(BaseModel):
    """Basic health status response"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    checks_passed: int
    checks_failed: int
    checks_warning: int
    total_time_seconds: float
    message: str

class DetailedHealthCheck(BaseModel):
    """Detailed health check information"""
    name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str
    execution_time: float

class DetailedHealthStatus(BaseModel):
    """Detailed health status response"""
    status: str
    timestamp: datetime
    checks_passed: int
    checks_failed: int
    checks_warning: int
    total_time_seconds: float
    categories: List[Dict[str, Any]]
    checks: List[DetailedHealthCheck]

@health_router.get("/", response_model=HealthStatus)
async def health_check():
    """
    Basic health check endpoint
    Returns overall system health status
    """
    try:
        start_time = datetime.now()
        
        # Run health checks
        runner = HealthCheckRunner()
        runner.add_check(DatabaseHealthCheck())
        runner.add_check(ExternalServiceHealthCheck())
        runner.add_check(MCPToolsHealthCheck())
        runner.add_check(SystemHealthCheck())
        
        results = await runner.run_all_checks(level="critical")
        
        # Calculate totals
        total_passed = sum(r.passed_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        total_time = sum(r.total_time for r in results)
        
        # Determine overall status
        if total_failed > 0:
            status = "unhealthy"
            message = f"Critical issues found: {total_failed} failed checks"
        elif total_warnings > 0:
            status = "degraded"
            message = f"System operational with warnings: {total_warnings} warnings"
        else:
            status = "healthy"
            message = "All systems operational"
        
        return HealthStatus(
            status=status,
            timestamp=start_time,
            checks_passed=total_passed,
            checks_failed=total_failed,
            checks_warning=total_warnings,
            total_time_seconds=total_time,
            message=message
        )
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check system error: {str(e)}")

@health_router.get("/detailed", response_model=DetailedHealthStatus)
async def detailed_health_check():
    """
    Detailed health check endpoint
    Returns comprehensive system health information
    """
    try:
        start_time = datetime.now()
        
        # Run comprehensive health checks
        runner = HealthCheckRunner()
        runner.add_check(DatabaseHealthCheck())
        runner.add_check(ExternalServiceHealthCheck())
        runner.add_check(MCPToolsHealthCheck())
        runner.add_check(SystemHealthCheck())
        
        results = await runner.run_all_checks(level="comprehensive")
        
        # Calculate totals
        total_passed = sum(r.passed_count for r in results)
        total_failed = sum(r.failed_count for r in results)
        total_warnings = sum(r.warning_count for r in results)
        total_time = sum(r.total_time for r in results)
        
        # Determine overall status
        if total_failed > 0:
            status = "unhealthy"
        elif total_warnings > 0:
            status = "degraded"
        else:
            status = "healthy"
        
        # Build category information
        categories = []
        all_checks = []
        
        for result in results:
            category_info = {
                "name": result.category,
                "status": result.overall_status.value,
                "passed": result.passed_count,
                "failed": result.failed_count,
                "warnings": result.warning_count,
                "execution_time": result.total_time
            }
            categories.append(category_info)
            
            # Add individual checks
            for check in result.checks:
                detailed_check = DetailedHealthCheck(
                    name=f"{result.category} - {check.name}",
                    status=check.status.value,
                    message=check.message,
                    execution_time=check.execution_time
                )
                all_checks.append(detailed_check)
        
        return DetailedHealthStatus(
            status=status,
            timestamp=start_time,
            checks_passed=total_passed,
            checks_failed=total_failed,
            checks_warning=total_warnings,
            total_time_seconds=total_time,
            categories=categories,
            checks=all_checks
        )
        
    except Exception as e:
        logging.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check system error: {str(e)}")

@health_router.get("/quick")
async def quick_health_check():
    """
    Quick health check endpoint (minimal checks for load balancers)
    Just verifies the application is running and can connect to primary database
    """
    try:
        from app.database import get_database_url
        from sqlalchemy import create_engine, text
        
        # Quick database connectivity test
        db_url = get_database_url()
        if not db_url:
            raise Exception("Database not configured")
            
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "ok",
            "timestamp": datetime.now(),
            "message": "Service is operational"
        }
        
    except Exception as e:
        logging.error(f"Quick health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Optional: Add a liveness probe for Kubernetes/container orchestration
@health_router.get("/live")
async def liveness_probe():
    """
    Liveness probe endpoint
    Just returns 200 OK if the application is running
    """
    return {"status": "alive", "timestamp": datetime.now()}

# Optional: Add a readiness probe
@health_router.get("/ready")
async def readiness_probe():
    """
    Readiness probe endpoint
    Checks if the application is ready to serve traffic
    """
    try:
        # Quick check of critical services
        from app.database import get_database_url
        
        db_url = get_database_url()
        if not db_url:
            raise HTTPException(status_code=503, detail="Database not configured")
        
        return {"status": "ready", "timestamp": datetime.now()}
        
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service not ready")