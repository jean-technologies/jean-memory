#!/usr/bin/env python3
"""
Setup script for managing the RAG test user data
Clones memories from a source user to the test user for production testing
"""

import os
import sys
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv("openmemory/.env.local")

class TestUserManager:
    def __init__(self):
        # Test user configuration
        self.test_user_id = "5a4cc4ed-d8f1-4128-af09-18ec96963ecc"
        self.source_user_id = "fa97efb5-410d-4806-b137-8cf13b6cb464"
        
        # Production database connection
        self.database_url = "postgresql://postgres.masapxpxcwvsjpuymbmd:jeanmemorytypefasho@aws-0-us-east-1.pooler.supabase.com:5432/postgres?gssencmode=disable"
        
        print(f"📊 Test User Manager Initialized")
        print(f"   Test User ID: {self.test_user_id}")
        print(f"   Source User ID: {self.source_user_id}")
        print(f"   Database: Supabase Production")
    
    def get_db_connection(self):
        """Get database connection using the production connection string"""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            print("\n💡 Troubleshooting:")
            print("1. Check if the database credentials are correct")
            print("2. Verify network connectivity to Supabase")
            print("3. Ensure the database is accessible from your IP")
            print(f"4. Connection string: {self.database_url}")
            sys.exit(1)
    
    def test_connection(self):
        """Test the database connection"""
        print("🔍 Testing database connection...")
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Database version: {version[:50]}...")
            
            # Test auth.users access
            cursor.execute("SELECT COUNT(*) FROM auth.users LIMIT 1;")
            print("✅ Can access auth.users table")
            
            # Test users table access
            cursor.execute("SELECT COUNT(*) FROM users LIMIT 1;")
            print("✅ Can access users table")
            
            # Test memories table access
            cursor.execute("SELECT COUNT(*) FROM memories LIMIT 1;")
            print("✅ Can access memories table")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get user info from auth.users
            cursor.execute("SELECT id, email, created_at FROM auth.users WHERE id = %s;", (user_id,))
            auth_user = cursor.fetchone()
            
            if not auth_user:
                return {"exists": False, "reason": "not_found_in_auth"}
            
            # Get user info from users table
            cursor.execute("SELECT id, user_id, email FROM users WHERE user_id = %s;", (user_id,))
            app_user = cursor.fetchone()
            
            if not app_user:
                return {
                    "exists": False, 
                    "reason": "not_found_in_users_table",
                    "auth_email": auth_user[1]
                }
            
            # Get memory count
            cursor.execute("""
                SELECT COUNT(*) FROM memories 
                WHERE user_id = %s AND deleted_at IS NULL
            """, (app_user[0],))  # Use the internal user ID
            memory_count = cursor.fetchone()[0]
            
            # Get recent memories
            cursor.execute("""
                SELECT content, created_at FROM memories 
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY created_at DESC LIMIT 3
            """, (app_user[0],))
            recent_memories = cursor.fetchall()
            
            return {
                "exists": True,
                "auth_email": auth_user[1],
                "app_email": app_user[2],
                "created_at": auth_user[2],
                "memory_count": memory_count,
                "internal_user_id": app_user[0],
                "recent_memories": [
                    {"content": mem[0][:100] + "..." if len(mem[0]) > 100 else mem[0], 
                     "created_at": mem[1]}
                    for mem in recent_memories
                ]
            }
            
        except Exception as e:
            print(f"❌ Error getting user stats: {e}")
            return {"exists": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()
    
    def clone_user_memories(self, limit: Optional[int] = None) -> int:
        """Clone memories from source user to test user"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            print(f"🔄 Starting memory cloning process...")
            
            # Get internal user IDs
            cursor.execute("SELECT id FROM users WHERE user_id = %s;", (self.test_user_id,))
            test_internal_id = cursor.fetchone()
            if not test_internal_id:
                print(f"❌ Test user not found in users table")
                return 0
            test_internal_id = test_internal_id[0]
            
            cursor.execute("SELECT id FROM users WHERE user_id = %s;", (self.source_user_id,))
            source_internal_id = cursor.fetchone()
            if not source_internal_id:
                print(f"❌ Source user not found in users table")
                return 0
            source_internal_id = source_internal_id[0]
            
            # Clear existing memories for test user
            print(f"   Clearing existing memories for test user...")
            cursor.execute("DELETE FROM memories WHERE user_id = %s", (test_internal_id,))
            cleared_count = cursor.rowcount
            print(f"   Cleared {cleared_count} existing memories")
            
            # Clone memories from source user
            print(f"   Cloning memories from source user...")
            clone_query = """
                INSERT INTO memories (id, user_id, app_id, content, metadata, created_at, updated_at)
                SELECT 
                    gen_random_uuid() as id,
                    %s as user_id,
                    %s as app_id,
                    content,
                    json_build_object(
                        'cloned_from', %s,
                        'cloned_at', %s,
                        'is_test_data', true,
                        'original_metadata', COALESCE(metadata, '{}')
                    )::json as metadata,
                    created_at,
                    updated_at
                FROM memories
                WHERE user_id = %s AND deleted_at IS NULL
                ORDER BY created_at DESC
            """
            
            if limit:
                clone_query += f" LIMIT {limit}"
            
            cursor.execute(clone_query, (
                test_internal_id,
                self.test_user_id,  # app_id
                self.source_user_id,
                datetime.now().isoformat(),
                source_internal_id
            ))
            
            cloned_count = cursor.rowcount
            conn.commit()
            
            print(f"✅ Successfully cloned {cloned_count} memories")
            return cloned_count
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error cloning memories: {e}")
            import traceback
            traceback.print_exc()
            return 0
        finally:
            cursor.close()
            conn.close()
    
    def clear_test_user_data(self):
        """Clear all data for the test user"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get internal user ID
            cursor.execute("SELECT id FROM users WHERE user_id = %s;", (self.test_user_id,))
            test_internal_id = cursor.fetchone()
            if not test_internal_id:
                print(f"❌ Test user not found in users table")
                return
            test_internal_id = test_internal_id[0]
            
            # Clear memories
            cursor.execute("DELETE FROM memories WHERE user_id = %s", (test_internal_id,))
            memory_count = cursor.rowcount
            
            # Clear documents if they exist
            try:
                cursor.execute("DELETE FROM documents WHERE user_id = %s", (test_internal_id,))
                doc_count = cursor.rowcount
            except:
                doc_count = 0
            
            conn.commit()
            print(f"✅ Cleared {memory_count} memories and {doc_count} documents for test user")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error clearing data: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def verify_setup(self):
        """Verify the test setup is working correctly"""
        print(f"\n📊 Verifying Test Setup")
        print("=" * 50)
        
        # Test connection first
        if not self.test_connection():
            return False
        
        # Check source user
        print(f"\n👤 Source User ({self.source_user_id}):")
        source_stats = self.get_user_stats(self.source_user_id)
        if source_stats["exists"]:
            print(f"   ✅ Auth email: {source_stats['auth_email']}")
            print(f"   ✅ App email: {source_stats['app_email']}")
            print(f"   ✅ Memory count: {source_stats['memory_count']}")
            print(f"   ✅ Account created: {source_stats['created_at']}")
        else:
            print(f"   ❌ Source user issue: {source_stats.get('reason', 'unknown')}")
            if 'auth_email' in source_stats:
                print(f"   📧 Found in auth but not in app: {source_stats['auth_email']}")
            return False
        
        # Check test user
        print(f"\n🧪 Test User ({self.test_user_id}):")
        test_stats = self.get_user_stats(self.test_user_id)
        if test_stats["exists"]:
            print(f"   ✅ Auth email: {test_stats['auth_email']}")
            print(f"   ✅ App email: {test_stats['app_email']}")
            print(f"   ✅ Memory count: {test_stats['memory_count']}")
            print(f"   ✅ Account created: {test_stats['created_at']}")
            
            if test_stats["recent_memories"]:
                print(f"\n   📝 Recent Memories:")
                for i, mem in enumerate(test_stats["recent_memories"], 1):
                    print(f"      {i}. {mem['content']}")
        else:
            print(f"   ❌ Test user issue: {test_stats.get('reason', 'unknown')}")
            if 'auth_email' in test_stats:
                print(f"   📧 Found in auth but not in app: {test_stats['auth_email']}")
            return False
        
        return True

def main():
    print("🚀 Test User Setup for Production Testing")
    print("=" * 50)
    
    manager = TestUserManager()
    
    # Verify both users exist
    if not manager.verify_setup():
        print("\n❌ Setup verification failed. Please check user IDs and database connection.")
        return
    
    print(f"\n📋 Available Actions:")
    print(f"1. Clone memories (with limit)")
    print(f"2. Clone all memories")
    print(f"3. Clear test user data")
    print(f"4. Verify setup only")
    print(f"5. Exit")
    
    while True:
        choice = input(f"\nSelect action (1-5): ").strip()
        
        if choice == "1":
            try:
                limit = int(input("Enter memory limit: "))
                cloned_count = manager.clone_user_memories(limit=limit)
                print(f"\n✅ Cloned {cloned_count} memories with limit {limit}")
                break
            except ValueError:
                print("❌ Please enter a valid number")
                continue
                
        elif choice == "2":
            cloned_count = manager.clone_user_memories()
            print(f"\n✅ Cloned {cloned_count} memories (all)")
            break
            
        elif choice == "3":
            confirm = input("Are you sure you want to clear all test user data? (yes/no): ")
            if confirm.lower() == "yes":
                manager.clear_test_user_data()
                break
            else:
                print("❌ Cancelled")
                continue
                
        elif choice == "4":
            print("\n✅ Setup verification complete")
            break
            
        elif choice == "5":
            print("👋 Goodbye!")
            return
            
        else:
            print("❌ Invalid choice. Please select 1-5.")
            continue
    
    # Final verification
    print(f"\n🔍 Final Verification:")
    manager.verify_setup()
    
    print(f"\n🎉 Setup Complete!")
    print(f"📧 Test user email: rohankatakam@gmail.com")
    print(f"🆔 Test user ID: {manager.test_user_id}")
    print(f"🌐 You can now log in at https://jeanmemory.com")
    print(f"🧪 The unified memory system will be enabled for this test user")

if __name__ == "__main__":
    main() 