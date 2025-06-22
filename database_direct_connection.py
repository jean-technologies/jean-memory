#!/usr/bin/env python3
"""
Direct PostgreSQL Database Connection

This script connects directly to your Supabase PostgreSQL database
to explore schema and test data retrieval.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv

load_dotenv()

def connect_to_database():
    """Connect directly to PostgreSQL database"""
    
    # Database connection parameters
    db_config = {
        'host': 'db.masapxpxcwvsjpuymbmd.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'jeanmemorytypefasho'
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        print("✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def explore_schema(conn):
    """Explore the users and memories table schemas"""
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔍 Exploring Database Schema")
    print("=" * 50)
    
    # 1. Get users table schema
    print("\n📋 Users Table Schema:")
    try:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        users_columns = cursor.fetchall()
        if users_columns:
            print("   📊 Column structure:")
            for col in users_columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"      • {col['column_name']}: {col['data_type']} {nullable}{default}")
        else:
            print("   ⚠️ Users table not found")
            
    except Exception as e:
        print(f"   ❌ Error getting users schema: {e}")
    
    # 2. Get memories table schema
    print("\n💭 Memories Table Schema:")
    try:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'memories' AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        memories_columns = cursor.fetchall()
        if memories_columns:
            print("   📊 Column structure:")
            for col in memories_columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"      • {col['column_name']}: {col['data_type']} {nullable}{default}")
        else:
            print("   ⚠️ Memories table not found")
            
    except Exception as e:
        print(f"   ❌ Error getting memories schema: {e}")
    
    cursor.close()
    return users_columns, memories_columns

def explore_data(conn):
    """Explore actual data in the tables"""
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n📊 Exploring Table Data")
    print("=" * 50)
    
    # 1. Get sample users
    print("\n👥 Sample Users:")
    try:
        cursor.execute("SELECT * FROM users LIMIT 5;")
        users = cursor.fetchall()
        
        if users:
            print(f"   ✅ Found {len(users)} sample users")
            for i, user in enumerate(users, 1):
                user_id = user.get('id') or user.get('user_id') or user.get('uuid')
                email = user.get('email', 'N/A')
                created_at = user.get('created_at', 'N/A')
                print(f"      {i}. ID: {user_id}")
                print(f"         Email: {email}")
                print(f"         Created: {created_at}")
                print()
        else:
            print("   ⚠️ No users found")
            
    except Exception as e:
        print(f"   ❌ Error getting users: {e}")
    
    # 2. Get sample memories
    print("\n💭 Sample Memories:")
    try:
        cursor.execute("SELECT * FROM memories LIMIT 3;")
        memories = cursor.fetchall()
        
        if memories:
            print(f"   ✅ Found {len(memories)} sample memories")
            for i, memory in enumerate(memories, 1):
                memory_id = memory.get('id') or memory.get('memory_id')
                user_id = memory.get('user_id')
                content = memory.get('content', 'No content')[:100]
                created_at = memory.get('created_at', 'N/A')
                
                print(f"      {i}. Memory ID: {memory_id}")
                print(f"         User ID: {user_id}")
                print(f"         Content: {content}...")
                print(f"         Created: {created_at}")
                print()
        else:
            print("   ⚠️ No memories found")
            
    except Exception as e:
        print(f"   ❌ Error getting memories: {e}")
    
    # 3. Get memory counts by user
    print("\n📈 Memory Distribution:")
    try:
        cursor.execute("""
            SELECT user_id, COUNT(*) as memory_count 
            FROM memories 
            GROUP BY user_id 
            ORDER BY memory_count DESC 
            LIMIT 10;
        """)
        
        user_counts = cursor.fetchall()
        if user_counts:
            print("   📊 Top users by memory count:")
            for i, row in enumerate(user_counts, 1):
                print(f"      {i}. User {row['user_id']}: {row['memory_count']} memories")
        else:
            print("   ⚠️ No memory distribution data")
            
    except Exception as e:
        print(f"   ❌ Error getting memory distribution: {e}")
    
    cursor.close()
    return users, memories, user_counts

def test_user_memory_retrieval(conn, user_id):
    """Test retrieving all memories for a specific user"""
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n🧪 Testing Memory Retrieval for User: {user_id}")
    print("=" * 50)
    
    try:
        # Get all memories for the user
        cursor.execute("""
            SELECT m.*, u.email 
            FROM memories m 
            LEFT JOIN users u ON m.user_id = u.id 
            WHERE m.user_id = %s 
            ORDER BY m.created_at DESC;
        """, (user_id,))
        
        user_memories = cursor.fetchall()
        
        if user_memories:
            print(f"   ✅ Found {len(user_memories)} memories for user {user_id}")
            
            # Show user info
            if user_memories[0].get('email'):
                print(f"   👤 User email: {user_memories[0]['email']}")
            
            # Show memory samples
            print(f"\n   📝 Sample memories:")
            for i, memory in enumerate(user_memories[:3], 1):
                content = memory.get('content', 'No content')[:150]
                created_at = memory.get('created_at', 'N/A')
                memory_id = memory.get('id')
                
                print(f"      {i}. [{memory_id}] {content}...")
                print(f"         Created: {created_at}")
                print()
            
            # Memory statistics
            total_chars = sum(len(str(m.get('content', ''))) for m in user_memories)
            avg_length = total_chars / len(user_memories) if user_memories else 0
            
            print(f"   📊 Memory Statistics:")
            print(f"      • Total memories: {len(user_memories)}")
            print(f"      • Total characters: {total_chars:,}")
            print(f"      • Average length: {avg_length:.0f} characters")
            
            return user_memories
        else:
            print(f"   ⚠️ No memories found for user {user_id}")
            return []
            
    except Exception as e:
        print(f"   ❌ Error retrieving user memories: {e}")
        return []
    finally:
        cursor.close()

def generate_rd_queries(conn):
    """Generate the exact queries we'll use in R&D pipeline"""
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n🔧 R&D Pipeline Queries")
    print("=" * 50)
    
    # Get a good test user
    try:
        cursor.execute("""
            SELECT user_id, COUNT(*) as memory_count 
            FROM memories 
            GROUP BY user_id 
            HAVING COUNT(*) >= 5
            ORDER BY memory_count DESC 
            LIMIT 5;
        """)
        
        test_users = cursor.fetchall()
        
        if test_users:
            print("   🎯 Recommended test users:")
            for i, user in enumerate(test_users, 1):
                print(f"      {i}. User ID: {user['user_id']} ({user['memory_count']} memories)")
            
            # Generate exact queries for R&D
            best_user = test_users[0]['user_id']
            
            print(f"\n   📋 Exact queries for R&D pipeline:")
            print(f"   ```sql")
            print(f"   -- Get user info")
            print(f"   SELECT * FROM users WHERE id = '{best_user}';")
            print(f"   ")
            print(f"   -- Get all memories for user")
            print(f"   SELECT * FROM memories WHERE user_id = '{best_user}' ORDER BY created_at DESC;")
            print(f"   ")
            print(f"   -- Get memory count")
            print(f"   SELECT COUNT(*) FROM memories WHERE user_id = '{best_user}';")
            print(f"   ```")
            
            print(f"\n   🚀 Ready to test R&D pipeline with user: {best_user}")
            return best_user
        else:
            print("   ⚠️ No users with sufficient memories found")
            return None
            
    except Exception as e:
        print(f"   ❌ Error generating R&D queries: {e}")
        return None
    finally:
        cursor.close()

def main():
    """Main exploration function"""
    
    print("🔍 Direct PostgreSQL Database Explorer")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        # Explore schema
        users_schema, memories_schema = explore_schema(conn)
        
        # Explore data
        users, memories, user_counts = explore_data(conn)
        
        # Generate R&D pipeline info
        best_user = generate_rd_queries(conn)
        
        # Test with best user if found
        if best_user and 'user_counts' in locals() and user_counts:
            test_user_memory_retrieval(conn, best_user)
        
        print(f"\n🎉 Database exploration complete!")
        print(f"   💡 Next step: Update R&D scripts with PostgreSQL connection")
        print(f"   🚀 Then run: python rd_manual_test.py --user-id {best_user}")
        
    finally:
        conn.close()
        print(f"\n✅ Database connection closed")

if __name__ == "__main__":
    main() 