#!/usr/bin/env python3
"""
Database Schema Explorer

This script explores your Supabase database to understand the structure of
the users and memories tables, then tests data retrieval.
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def explore_database():
    """Explore database schema and test data access"""
    
    # Initialize Supabase client
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return
    
    client = create_client(url, service_key)
    print("✅ Connected to Supabase")
    
    print("\n🔍 Exploring Database Schema")
    print("=" * 50)
    
    # 1. Explore users table
    print("\n📋 Users Table:")
    try:
        # Get sample users (limit to 5 for exploration)
        users_response = client.table('users').select('*').limit(5).execute()
        
        if users_response.data:
            print(f"   ✅ Found {len(users_response.data)} sample users")
            
            # Show schema by examining first user
            sample_user = users_response.data[0]
            print(f"   📊 Users table columns:")
            for key, value in sample_user.items():
                value_type = type(value).__name__
                value_preview = str(value)[:50] if value else "None"
                print(f"      • {key}: {value_type} = {value_preview}")
            
            # Show all user IDs for testing
            print(f"\n   🆔 Available User IDs for testing:")
            for i, user in enumerate(users_response.data, 1):
                user_id = user.get('id') or user.get('user_id') or user.get('uuid')
                email = user.get('email', 'N/A')
                print(f"      {i}. {user_id} ({email})")
        else:
            print("   ⚠️ No users found or access restricted")
            
    except Exception as e:
        print(f"   ❌ Error accessing users table: {e}")
    
    # 2. Explore memories table
    print("\n💭 Memories Table:")
    try:
        # Get sample memories (limit to 3 for exploration)
        memories_response = client.table('memories').select('*').limit(3).execute()
        
        if memories_response.data:
            print(f"   ✅ Found {len(memories_response.data)} sample memories")
            
            # Show schema by examining first memory
            sample_memory = memories_response.data[0]
            print(f"   📊 Memories table columns:")
            for key, value in sample_memory.items():
                value_type = type(value).__name__
                value_preview = str(value)[:50] if value else "None"
                print(f"      • {key}: {value_type} = {value_preview}")
            
            # Show memory distribution by user
            print(f"\n   👥 Memory distribution by user:")
            user_memory_counts = {}
            
            # Get more memories to analyze distribution
            all_memories_response = client.table('memories').select('user_id').limit(100).execute()
            for memory in all_memories_response.data:
                user_id = memory.get('user_id')
                if user_id:
                    user_memory_counts[user_id] = user_memory_counts.get(user_id, 0) + 1
            
            # Show top users by memory count
            sorted_users = sorted(user_memory_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (user_id, count) in enumerate(sorted_users[:5], 1):
                print(f"      {i}. {user_id}: {count} memories")
                
        else:
            print("   ⚠️ No memories found or access restricted")
            
    except Exception as e:
        print(f"   ❌ Error accessing memories table: {e}")
    
    # 3. Test user-specific memory retrieval
    if 'users_response' in locals() and users_response.data:
        test_user_id = users_response.data[0].get('id') or users_response.data[0].get('user_id')
        if test_user_id:
            print(f"\n🧪 Testing Memory Retrieval for User: {test_user_id}")
            try:
                user_memories = client.table('memories').select('*').eq('user_id', test_user_id).limit(5).execute()
                
                if user_memories.data:
                    print(f"   ✅ Found {len(user_memories.data)} memories for this user")
                    
                    # Show sample memory content
                    for i, memory in enumerate(user_memories.data[:2], 1):
                        content = memory.get('content', 'No content')[:100]
                        created_at = memory.get('created_at', 'No date')
                        print(f"   📝 Memory {i}: {content}... (created: {created_at})")
                else:
                    print(f"   ⚠️ No memories found for user {test_user_id}")
                    
            except Exception as e:
                print(f"   ❌ Error retrieving user memories: {e}")
    
    # 4. Generate R&D test commands
    print(f"\n🚀 Ready for R&D Testing!")
    print(f"=" * 50)
    
    if 'sorted_users' in locals() and sorted_users:
        print(f"📋 Recommended test commands:")
        for i, (user_id, count) in enumerate(sorted_users[:3], 1):
            print(f"\n   Test {i} - User with {count} memories:")
            print(f"   python rd_manual_test.py --user-id {user_id}")
            print(f"   python rd_manual_test.py --user-id {user_id} --sample-size {min(count, 50)}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Choose a user ID from above")
    print(f"   2. Run: python rd_manual_test.py --user-id USER_ID")
    print(f"   3. Analyze results in rd_data/ folder")
    print(f"   4. Iterate and refine your algorithms")

if __name__ == "__main__":
    explore_database() 