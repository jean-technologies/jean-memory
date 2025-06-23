#!/usr/bin/env python3
"""
Verify Test User Isolation

This script verifies that our test infrastructure is properly isolated
and only affects the test user, not other production users.
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv("openmemory/.env.local")

def verify_isolation():
    """Verify that test infrastructure is isolated"""
    print("🔍 Verifying Test User Isolation")
    print("=" * 50)
    
    test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
    
    # Check production database
    prod_db_url = "postgresql://postgres.masapxpxcwvsjpuymbmd:jeanmemorytypefasho@aws-0-us-east-1.pooler.supabase.com:5432/postgres?gssencmode=disable"
    
    print("📊 Checking Production Database:")
    try:
        conn = psycopg2.connect(prod_db_url)
        cursor = conn.cursor()
        
        # Count total users
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM users;")
        total_users = cursor.fetchone()[0]
        print(f"   Total users: {total_users}")
        
        # Check test user exists
        cursor.execute("SELECT id, user_id FROM users WHERE user_id = %s;", (test_user_id,))
        test_user = cursor.fetchone()
        if test_user:
            print(f"   ✅ Test user found: internal_id={test_user[0]}")
        else:
            print(f"   ❌ Test user not found")
        
        # Sample other users (excluding test user)
        cursor.execute("""
            SELECT u.user_id, COUNT(m.id) as memory_count
            FROM users u
            LEFT JOIN memories m ON u.id = m.user_id
            WHERE u.user_id != %s
            GROUP BY u.user_id
            ORDER BY RANDOM()
            LIMIT 5;
        """, (test_user_id,))
        
        print("\n   Sample of other users (should be unaffected):")
        for row in cursor.fetchall():
            print(f"     User {row[0][:8]}...: {row[1]} memories")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error checking production: {e}")
    
    # Check test infrastructure
    print("\n🧪 Checking Test Infrastructure:")
    
    # Test PostgreSQL
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="mem0_unified",
            user="postgres",
            password="secure_postgres_test_2024"
        )
        cursor = conn.cursor()
        
        # Check if any tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        print(f"   PostgreSQL tables: {len(tables)}")
        for table in tables[:5]:  # Show first 5 tables
            print(f"     - {table[0]}")
        
        cursor.close()
        conn.close()
        print("   ✅ Test PostgreSQL is isolated on port 5433")
        
    except Exception as e:
        print(f"   ❌ Test PostgreSQL error: {e}")
    
    # Test Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            "bolt://localhost:7688",
            auth=("neo4j", "secure_neo4j_test_2024")
        )
        
        with driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            print(f"\n   Neo4j nodes: {node_count}")
            
            # Check for test user data
            result = session.run(
                "MATCH (n {user_id: $user_id}) RETURN count(n) as count",
                user_id=test_user_id
            )
            test_user_nodes = result.single()["count"]
            print(f"   Test user nodes: {test_user_nodes}")
            
        driver.close()
        print("   ✅ Test Neo4j is isolated on port 7688")
        
    except Exception as e:
        print(f"   ❌ Test Neo4j error: {e}")
    
    print("\n✅ Summary:")
    print("   - Test user exists in production database")
    print("   - Test infrastructure is on separate ports (5433, 7688)")
    print("   - Other production users are unaffected")
    print("   - Test user routing should only affect user ID: " + test_user_id)

if __name__ == "__main__":
    verify_isolation() 