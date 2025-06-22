#!/usr/bin/env python3
"""
Quick User Memory Test Script

Simple wrapper for testing the unified memory system with a specific user.
Handles environment setup and provides sensible defaults.

Usage:
    python quick_user_test.py <USER_ID>
    python quick_user_test.py <USER_ID> --size 30 --interactive
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

def setup_environment():
    """Set up environment variables with sensible defaults"""
    
    # Check for .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Found .env file")
        from dotenv import load_dotenv
        load_dotenv()
    else:
        print("⚠️  No .env file found, using environment variables")
    
    # Check required environment variables
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for embeddings and LLM',
        'GEMINI_API_KEY': 'Gemini API key for preprocessing (optional)',
        'NEO4J_PASSWORD': 'Neo4j database password',
        'SUPABASE_DB_PASSWORD': 'Supabase database password'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  {var}: {description}")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print("\nPlease set these in your .env file or environment.")
        return False
    
    print("✅ All required environment variables found")
    return True

def check_services():
    """Check if required services are running"""
    
    services_ok = True
    
    # Check Neo4j
    try:
        from neo4j import GraphDatabase
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        driver = GraphDatabase.driver(
            neo4j_uri, 
            auth=(neo4j_user, neo4j_password)
        )
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        print("✅ Neo4j is running")
    except Exception as e:
        print(f"❌ Neo4j not available: {e}")
        services_ok = False
    
    # Check Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333", timeout=5)
        if response.status_code == 200:
            print("✅ Qdrant is running")
        else:
            print("❌ Qdrant not responding")
            services_ok = False
    except Exception as e:
        print(f"❌ Qdrant not available: {e}")
        services_ok = False
    
    return services_ok

async def run_user_test(user_id: str, sample_size: int = 50, interactive: bool = False):
    """Run the user test with the unified memory system"""
    
    print(f"🚀 Quick User Memory Test")
    print(f"👤 User ID: {user_id}")
    print(f"📏 Sample size: {sample_size}")
    print(f"🎮 Interactive: {interactive}")
    print("=" * 60)
    
    # Import and run the main tester
    try:
        from test_user_unified_memory import UserMemoryTester
        
        tester = UserMemoryTester(user_id, sample_size)
        results = await tester.run_complete_test(interactive=interactive)
        
        # Save results with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results_{user_id[:8]}_{timestamp}.json"
        
        import json
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Test results saved to: {results_file}")
        
        if results.get('success'):
            print("🎉 Test completed successfully!")
        else:
            print(f"❌ Test failed: {results.get('error', 'Unknown error')}")
        
        return results
        
    except ImportError as e:
        print(f"❌ Could not import test module: {e}")
        print("Make sure test_user_unified_memory.py is in the same directory")
        return None
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Quick test of unified memory system for a specific user',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python quick_user_test.py abc123def456
  python quick_user_test.py abc123def456 --size 30
  python quick_user_test.py abc123def456 --size 100 --interactive
  
Environment Variables Required:
  OPENAI_API_KEY       - OpenAI API key
  GEMINI_API_KEY       - Gemini API key (optional)
  NEO4J_PASSWORD       - Neo4j password
  SUPABASE_DB_PASSWORD - Supabase database password"""
    )
    
    parser.add_argument(
        'user_id',
        help='User ID to test with'
    )
    parser.add_argument(
        '--size', 
        type=int, 
        default=50,
        help='Number of memories to test with (default: 50)'
    )
    parser.add_argument(
        '--interactive', 
        action='store_true',
        help='Enter interactive query mode after testing'
    )
    parser.add_argument(
        '--skip-checks', 
        action='store_true',
        help='Skip environment and service checks'
    )
    
    args = parser.parse_args()
    
    # Pre-flight checks
    if not args.skip_checks:
        print("🔍 Running pre-flight checks...")
        
        if not setup_environment():
            sys.exit(1)
        
        if not check_services():
            print("\n❌ Some services are not available.")
            print("Make sure Neo4j and Qdrant are running locally.")
            
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                sys.exit(1)
        
        print("\n✅ Pre-flight checks passed!")
        print("-" * 60)
    
    # Run the test
    try:
        results = asyncio.run(run_user_test(
            args.user_id, 
            args.size, 
            args.interactive
        ))
        
        if results and results.get('success'):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 