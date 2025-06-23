#!/usr/bin/env python3
"""
Simple Test of Unified Memory Routing

This script tests if the routing logic works correctly for the test user.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv("openmemory/.env.local")

# Import the routing function
from openmemory.api.app.utils.unified_memory import should_use_unified_memory

def test_routing():
    """Test the routing logic"""
    print("🧪 Testing Unified Memory Routing")
    print("=" * 40)
    
    # Test user ID
    test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
    
    # Random user ID
    random_user_id = "12345678-1234-1234-1234-123456789012"
    
    print(f"Test User ({test_user_id[:8]}...): {should_use_unified_memory(test_user_id)}")
    print(f"Random User ({random_user_id[:8]}...): {should_use_unified_memory(random_user_id)}")
    
    # Check environment variables
    print(f"\nEnvironment Variables:")
    print(f"UNIFIED_MEMORY_TEST_USER_ID: {os.getenv('UNIFIED_MEMORY_TEST_USER_ID', 'Not set')}")
    print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not set'}")
    print(f"TEST_PG_HOST: {os.getenv('TEST_PG_HOST', 'Not set')}")
    print(f"TEST_NEO4J_URI: {os.getenv('TEST_NEO4J_URI', 'Not set')}")
    
    # Test infrastructure connectivity
    print(f"\n🔌 Testing Infrastructure Connectivity")
    
    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("TEST_PG_HOST", "localhost"),
            port=int(os.getenv("TEST_PG_PORT", "5433")),
            database=os.getenv("TEST_PG_DBNAME", "mem0_unified"),
            user=os.getenv("TEST_PG_USER", "postgres"),
            password=os.getenv("TEST_PG_PASSWORD", "secure_postgres_test_2024")
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL: Connected ({version[:50]}...)")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
    
    # Test Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv("TEST_NEO4J_URI", "bolt://localhost:7688"),
            auth=(
                os.getenv("TEST_NEO4J_USER", "neo4j"),
                os.getenv("TEST_NEO4J_PASSWORD", "secure_neo4j_test_2024")
            )
        )
        
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            record = result.single()
            print(f"✅ Neo4j: Connected ({record['name']} {record['version']})")
        driver.close()
    except Exception as e:
        print(f"❌ Neo4j: {e}")

if __name__ == "__main__":
    test_routing() 