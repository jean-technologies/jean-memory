#!/usr/bin/env python3
"""
Jean Memory Health Check System
Pre-deployment and post-deployment health verification

Usage:
    python health_check.py --level=critical     # Fast pre-deployment checks
    python health_check.py --level=comprehensive # Full system verification
    python health_check.py --remote             # Test against remote deployment
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

# Add this directory and the API directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "../../openmemory/api"))

# Import our health check modules
from checks.base import HealthCheckRunner
from checks.database_checks import DatabaseHealthCheck
from checks.external_service_checks import ExternalServiceHealthCheck
from checks.mcp_tools_checks import MCPToolsHealthCheck
from checks.system_checks import SystemHealthCheck

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during health checks
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress some noisy loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('neo4j').setLevel(logging.WARNING)

async def run_health_checks(level: str = "critical", remote: bool = False, verbose: bool = False):
    """Run health checks based on the specified level"""
    
    print("🏥 Jean Memory Health Check System")
    print("=" * 50)
    print(f"Level: {level.upper()}")
    print(f"Mode: {'Remote' if remote else 'Local'}")
    print(f"Started: {asyncio.get_event_loop().time()}")
    print()
    
    # Initialize the health check runner
    runner = HealthCheckRunner()
    
    # Add critical health checks (always run)
    runner.add_check(DatabaseHealthCheck())
    runner.add_check(ExternalServiceHealthCheck())
    runner.add_check(MCPToolsHealthCheck())
    runner.add_check(SystemHealthCheck())
    
    # Add comprehensive checks if requested
    if level == "comprehensive":
        # Additional checks would go here
        # For now, the existing checks run in comprehensive mode
        pass
    
    # Run all health checks
    try:
        results = await runner.run_all_checks(level)
        exit_code = runner.print_results(results, verbose=verbose)
        
        # Print recommendations based on failures
        await print_recommendations(results)
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n❌ Health check interrupted by user")
        return 3
    except Exception as e:
        print(f"\n❌ Critical error during health check: {e}")
        import traceback
        traceback.print_exc()
        return 4

async def print_recommendations(results):
    """Print actionable recommendations based on health check results"""
    failed_categories = []
    
    for result in results:
        if result.failed_count > 0:
            failed_categories.append(result.category)
    
    if not failed_categories:
        return
    
    print("\n" + "="*80)
    print("🔧 RECOMMENDED ACTIONS")
    print("="*80)
    
    if "Database Layer" in failed_categories:
        print("\n🚨 DATABASE ISSUES:")
        print("   1. Check environment variables: DATABASE_URL, QDRANT_HOST, NEO4J_URI")
        print("   2. Ensure all databases are running and accessible")
        print("   3. Run database migrations: 'alembic upgrade head'")
        print("   4. Verify network connectivity to database services")
    
    if "External Services" in failed_categories:
        print("\n🚨 EXTERNAL SERVICE ISSUES:")
        print("   1. Verify API keys: OPENAI_API_KEY, GEMINI_API_KEY")
        print("   2. Check Supabase configuration: SUPABASE_URL, SUPABASE_ANON_KEY")
        print("   3. Ensure service endpoints are reachable")
        print("   4. Check API quotas and rate limits")
    
    if "MCP Tools" in failed_categories:
        print("\n🚨 MCP TOOLS ISSUES:")
        print("   1. This is CRITICAL - the jean_memory tool is the heart of the system")
        print("   2. Check mem0 library configuration")
        print("   3. Verify all required dependencies are installed")
        print("   4. Test the orchestration system manually")
        print("   5. Check context variable system is working")
    
    print(f"\n⚠️  DO NOT DEPLOY until all critical issues are resolved!")

def load_environment():
    """Load environment variables for health checks"""
    # Try to load from .env file if it exists
    env_files = [
        Path("../../openmemory/api/.env"),
        Path("../../openmemory/.env"),  
        Path(".env")
    ]
    
    for env_file in env_files:
        if env_file.exists():
            print(f"📄 Loading environment from: {env_file}")
            from dotenv import load_dotenv
            load_dotenv(env_file)
            break
    else:
        print("⚠️  No .env file found, using system environment variables")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Jean Memory Health Check System")
    parser.add_argument(
        "--level", 
        choices=["critical", "comprehensive"],
        default="critical",
        help="Level of health checks to run (default: critical)"
    )
    parser.add_argument(
        "--remote",
        action="store_true", 
        help="Run checks against remote deployment"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true",
        help="Show detailed output for all checks"
    )
    parser.add_argument(
        "--no-env",
        action="store_true",
        help="Skip loading .env files"
    )
    
    args = parser.parse_args()
    
    # Load environment variables unless disabled
    if not args.no_env:
        try:
            load_environment()
        except ImportError:
            print("⚠️  python-dotenv not installed, using system environment variables")
    
    # Run health checks
    try:
        exit_code = asyncio.run(run_health_checks(
            level=args.level,
            remote=args.remote,
            verbose=args.verbose
        ))
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"❌ Failed to run health checks: {e}")
        sys.exit(5)

if __name__ == "__main__":
    main()