#!/usr/bin/env python3
"""
Infrastructure Setup Verification Script

Tests both local development and production infrastructure configurations:
- Local: Supabase CLI, Docker Qdrant, Docker Neo4j
- Production: Supabase Cloud, Qdrant Cloud, Neo4j AuraDB

Usage:
    python test_infrastructure_setup.py --local     # Test local development setup
    python test_infrastructure_setup.py --prod      # Test production setup
    python test_infrastructure_setup.py --both      # Test both environments
"""

import os
import sys
import asyncio
import argparse
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection(environment: str = "local") -> Dict[str, Any]:
    """Test Supabase connection (local or cloud)"""
    print(f"\n🔍 Testing Supabase ({environment})...")
    
    try:
        from supabase import create_client, Client
        
        if environment == "local":
            # Local Supabase CLI
            url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "http://127.0.0.1:54321")
            key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
        else:
            # Production Supabase Cloud
            url = os.getenv("SUPABASE_URL", "")
            key = os.getenv("SUPABASE_ANON_KEY", "")
        
        if not url or not key:
            return {
                "status": "error",
                "message": f"Missing Supabase credentials for {environment}",
                "details": {"url": bool(url), "key": bool(key)}
            }
        
        supabase: Client = create_client(url, key)
        
        # Test connection with a simple query
        response = supabase.table("memories").select("count", count="exact").limit(0).execute()
        
        return {
            "status": "success",
            "message": f"Supabase {environment} connection successful",
            "details": {
                "url": url,
                "authenticated": True,
                "database": "accessible"
            }
        }
        
    except ImportError:
        return {
            "status": "error",
            "message": "Supabase client not installed. Run: pip install supabase",
            "details": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Supabase {environment} connection failed: {str(e)}",
            "details": {"url": url if 'url' in locals() else None}
        }

def test_qdrant_connection(environment: str = "local") -> Dict[str, Any]:
    """Test Qdrant connection (local or cloud)"""
    print(f"\n🔍 Testing Qdrant ({environment})...")
    
    try:
        from qdrant_client import QdrantClient
        
        if environment == "local":
            # Local Docker Qdrant
            host = os.getenv("QDRANT_HOST", "localhost")
            port = int(os.getenv("QDRANT_PORT", "6333"))
            api_key = None  # Local doesn't need API key
        else:
            # Production Qdrant Cloud
            host = os.getenv("QDRANT_HOST", "")
            port = int(os.getenv("QDRANT_PORT", "6333"))
            api_key = os.getenv("QDRANT_API_KEY", "")
            
            if not host or not api_key:
                return {
                    "status": "error",
                    "message": f"Missing Qdrant credentials for {environment}",
                    "details": {"host": bool(host), "api_key": bool(api_key)}
                }
        
        # Create client
        if api_key:
            client = QdrantClient(host=host, port=port, api_key=api_key)
        else:
            client = QdrantClient(host=host, port=port)
        
        # Test connection
        collections = client.get_collections()
        
        return {
            "status": "success",
            "message": f"Qdrant {environment} connection successful",
            "details": {
                "host": host,
                "port": port,
                "collections": len(collections.collections) if collections else 0,
                "authenticated": bool(api_key)
            }
        }
        
    except ImportError:
        return {
            "status": "error",
            "message": "Qdrant client not installed. Run: pip install qdrant-client",
            "details": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Qdrant {environment} connection failed: {str(e)}",
            "details": {"host": host if 'host' in locals() else None}
        }

def test_neo4j_connection(environment: str = "local") -> Dict[str, Any]:
    """Test Neo4j connection (local or cloud)"""
    print(f"\n🔍 Testing Neo4j ({environment})...")
    
    try:
        from neo4j import GraphDatabase
        
        if environment == "local":
            # Local Docker Neo4j
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "fasho93fasho")
        else:
            # Production Neo4j AuraDB
            uri = os.getenv("NEO4J_URI", "")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "")
            
            if not uri or not password:
                return {
                    "status": "error",
                    "message": f"Missing Neo4j credentials for {environment}",
                    "details": {"uri": bool(uri), "user": bool(user), "password": bool(password)}
                }
        
        # Create driver and test connection
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            result = session.run("RETURN 'Neo4j connected!' AS message")
            message = result.single()["message"]
            
            # Get some basic stats
            stats_result = session.run("""
                MATCH (n) 
                RETURN labels(n) as labels, count(n) as count 
                ORDER BY count DESC 
                LIMIT 5
            """)
            stats = [{"labels": record["labels"], "count": record["count"]} 
                    for record in stats_result]
        
        driver.close()
        
        return {
            "status": "success",
            "message": f"Neo4j {environment} connection successful",
            "details": {
                "uri": uri,
                "user": user,
                "response": message,
                "node_stats": stats
            }
        }
        
    except ImportError:
        return {
            "status": "error",
            "message": "Neo4j driver not installed. Run: pip install neo4j",
            "details": {}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Neo4j {environment} connection failed: {str(e)}",
            "details": {"uri": uri if 'uri' in locals() else None}
        }

def test_unified_memory_system(environment: str = "local") -> Dict[str, Any]:
    """Test unified memory system integration"""
    print(f"\n🔍 Testing Unified Memory System ({environment})...")
    
    try:
        # Test mem0 import
        from mem0 import Memory
        
        # Test Graphiti import
        from graphiti_core import Graphiti
        
        return {
            "status": "success",
            "message": f"Unified memory system dependencies available",
            "details": {
                "mem0": "✅ Available",
                "graphiti": "✅ Available",
                "environment": environment
            }
        }
        
    except ImportError as e:
        missing_package = str(e).split("'")[1] if "'" in str(e) else "unknown"
        return {
            "status": "error",
            "message": f"Missing unified memory dependencies: {missing_package}",
            "details": {
                "missing_package": missing_package,
                "install_command": f"pip install mem0ai graphiti-core"
            }
        }

def print_results(results: Dict[str, Dict[str, Any]], environment: str):
    """Print formatted test results"""
    print(f"\n{'='*60}")
    print(f"🏗️  INFRASTRUCTURE TEST RESULTS ({environment.upper()})")
    print(f"{'='*60}")
    
    for service, result in results.items():
        status = result["status"]
        message = result["message"]
        
        if status == "success":
            print(f"✅ {service.upper()}: {message}")
        else:
            print(f"❌ {service.upper()}: {message}")
        
        # Print details if available
        if result.get("details"):
            for key, value in result["details"].items():
                print(f"   • {key}: {value}")
    
    # Summary
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    total_count = len(results)
    
    print(f"\n📊 SUMMARY: {success_count}/{total_count} services working")
    
    if success_count == total_count:
        print(f"🎉 All {environment} infrastructure services are working correctly!")
    else:
        print(f"⚠️  {total_count - success_count} service(s) need attention")

def main():
    parser = argparse.ArgumentParser(description="Test infrastructure setup")
    parser.add_argument("--local", action="store_true", help="Test local development setup")
    parser.add_argument("--prod", action="store_true", help="Test production setup")
    parser.add_argument("--both", action="store_true", help="Test both environments")
    
    args = parser.parse_args()
    
    if not any([args.local, args.prod, args.both]):
        print("Please specify --local, --prod, or --both")
        sys.exit(1)
    
    environments = []
    if args.local or args.both:
        environments.append("local")
    if args.prod or args.both:
        environments.append("production")
    
    for env in environments:
        print(f"\n🚀 Testing {env} environment...")
        
        results = {
            "supabase": test_supabase_connection(env),
            "qdrant": test_qdrant_connection(env),
            "neo4j": test_neo4j_connection(env),
            "unified_memory": test_unified_memory_system(env)
        }
        
        print_results(results, env)

if __name__ == "__main__":
    main() 