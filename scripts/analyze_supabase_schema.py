#!/usr/bin/env python3
"""
Analyze Supabase database schema for users and memories tables
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv("openmemory/.env.local")

def analyze_schema():
    """Analyze the database schema"""
    
    # Production database URL with SSL
    database_url = "postgresql://postgres.masapxpxcwvsjpuymbmd:jeanmemorytypefasho@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🔍 Analyzing Supabase Database Schema")
        print("=" * 50)
        
        # Check if we can connect
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to: {version}")
        
        # Analyze users table
        print(f"\n👥 USERS TABLE SCHEMA:")
        print("-" * 30)
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        
        users_columns = cursor.fetchall()
        if users_columns:
            for col in users_columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  {col[0]:<20} {col[1]:<15} {nullable}{default}")
        else:
            print("  ❌ Users table not found")
        
        # Check auth.users table (Supabase auth)
        print(f"\n🔐 AUTH.USERS TABLE SCHEMA:")
        print("-" * 30)
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'auth' AND table_name = 'users'
            ORDER BY ordinal_position
            LIMIT 10;
        """)
        
        auth_users_columns = cursor.fetchall()
        if auth_users_columns:
            for col in auth_users_columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"  {col[0]:<20} {col[1]:<15} {nullable}")
        
        # Analyze memories table
        print(f"\n🧠 MEMORIES TABLE SCHEMA:")
        print("-" * 30)
        
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'memories'
            ORDER BY ordinal_position;
        """)
        
        memories_columns = cursor.fetchall()
        if memories_columns:
            for col in memories_columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                default = f" DEFAULT {col[3]}" if col[3] else ""
                print(f"  {col[0]:<20} {col[1]:<15} {nullable}{default}")
        else:
            print("  ❌ Memories table not found")
        
        # Check sample data
        print(f"\n📊 SAMPLE DATA:")
        print("-" * 30)
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM auth.users;")
        user_count = cursor.fetchone()[0]
        print(f"Total users in auth.users: {user_count}")
        
        if users_columns:
            cursor.execute("SELECT COUNT(*) FROM users;")
            app_user_count = cursor.fetchone()[0]
            print(f"Total users in users table: {app_user_count}")
        
        # Count memories
        if memories_columns:
            cursor.execute("SELECT COUNT(*) FROM memories WHERE deleted_at IS NULL;")
            memory_count = cursor.fetchone()[0]
            print(f"Total active memories: {memory_count}")
        
        # Check specific users
        print(f"\n🔍 CHECKING SPECIFIC USERS:")
        print("-" * 30)
        
        test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
        source_user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
        
        # Check test user in auth.users
        cursor.execute("SELECT id, email, created_at FROM auth.users WHERE id = %s;", (test_user_id,))
        test_user = cursor.fetchone()
        if test_user:
            print(f"✅ Test user found in auth.users: {test_user[1]} (created: {test_user[2]})")
        else:
            print(f"❌ Test user not found in auth.users")
        
        # Check source user in auth.users
        cursor.execute("SELECT id, email, created_at FROM auth.users WHERE id = %s;", (source_user_id,))
        source_user = cursor.fetchone()
        if source_user:
            print(f"✅ Source user found in auth.users: {source_user[1]} (created: {source_user[2]})")
        else:
            print(f"❌ Source user not found in auth.users")
        
        # Check if users exist in app users table
        if users_columns:
            cursor.execute("SELECT id, user_id, email FROM users WHERE user_id = %s;", (test_user_id,))
            test_app_user = cursor.fetchone()
            if test_app_user:
                print(f"✅ Test user found in users table: {test_app_user[2]}")
            else:
                print(f"❌ Test user not found in users table")
            
            cursor.execute("SELECT id, user_id, email FROM users WHERE user_id = %s;", (source_user_id,))
            source_app_user = cursor.fetchone()
            if source_app_user:
                print(f"✅ Source user found in users table: {source_app_user[2]}")
            else:
                print(f"❌ Source user not found in users table")
        
        # Check memories for both users
        if memories_columns:
            cursor.execute("""
                SELECT COUNT(*) FROM memories m
                JOIN users u ON m.user_id = u.id
                WHERE u.user_id = %s AND m.deleted_at IS NULL;
            """, (test_user_id,))
            test_memories = cursor.fetchone()[0]
            print(f"Test user memories: {test_memories}")
            
            cursor.execute("""
                SELECT COUNT(*) FROM memories m
                JOIN users u ON m.user_id = u.id
                WHERE u.user_id = %s AND m.deleted_at IS NULL;
            """, (source_user_id,))
            source_memories = cursor.fetchone()[0]
            print(f"Source user memories: {source_memories}")
        
        # Show relationship between auth.users and users table
        print(f"\n🔗 TABLE RELATIONSHIPS:")
        print("-" * 30)
        
        if users_columns:
            cursor.execute("""
                SELECT 
                    au.id as auth_id,
                    au.email as auth_email,
                    u.id as app_id,
                    u.user_id as app_user_id,
                    u.email as app_email
                FROM auth.users au
                LEFT JOIN users u ON au.id = u.user_id
                WHERE au.id IN (%s, %s);
            """, (test_user_id, source_user_id))
            
            relationships = cursor.fetchall()
            for rel in relationships:
                print(f"Auth User: {rel[0][:8]}... ({rel[1]})")
                if rel[2]:
                    print(f"  -> App User: {rel[2]} (user_id: {rel[3][:8]}..., email: {rel[4]})")
                else:
                    print(f"  -> No corresponding app user record")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Schema analysis complete!")
        
    except Exception as e:
        print(f"❌ Error analyzing schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_schema() 