#!/usr/bin/env python3
"""
User Memory Download Script for Unified Memory Testing
Downloads memories for a specific user from Supabase database.
"""

import json
import os
import sys
import argparse
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_supabase():
    """Connect to Supabase PostgreSQL database"""
    try:
        # Supabase connection string format from the screenshot
        connection_string = "postgresql://postgres:[YOUR-PASSWORD]@db.masapxpxcwvsjpuymbmd.supabase.co:5432/postgres"
        
        # We'll need to get the password from environment or prompt
        password = os.getenv('SUPABASE_DB_PASSWORD')
        if not password:
            print("⚠️  SUPABASE_DB_PASSWORD not found in environment")
            password = input("Enter your Supabase database password: ")
        
        # Replace placeholder with actual password
        connection_string = connection_string.replace('[YOUR-PASSWORD]', password)
        
        conn = psycopg2.connect(connection_string)
        print("✅ Connected to Supabase database")
        return conn
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def download_user_memories(user_id):
    """Download memories for a specific user"""
    conn = connect_to_supabase()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # First, let's see what tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE '%memor%'
            ORDER BY table_name;
        """)
        
        memory_tables = cursor.fetchall()
        print(f"📋 Found memory-related tables: {[t[0] for t in memory_tables]}")
        
        # Check if we have a memories table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'memories'
            );
        """)
        
        has_memories_table = cursor.fetchone()[0]
        
        if not has_memories_table:
            print("❌ No 'memories' table found. Let's check what tables exist:")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            all_tables = cursor.fetchall()
            print(f"📋 Available tables: {[t[0] for t in all_tables]}")
            return []
        
        # Get user info from auth.users if it exists
        try:
            cursor.execute("""
                SELECT email, created_at
                FROM auth.users 
                WHERE id = %s
            """, (user_id,))
            
            user_info = cursor.fetchone()
            if user_info:
                print(f"👤 Found user: {user_info[0]} (created: {user_info[1]})")
            else:
                print(f"👤 User ID: {user_id} (not found in auth.users, but proceeding)")
        except Exception as e:
            print(f"⚠️  Could not query auth.users: {e}")
            print(f"👤 Proceeding with user ID: {user_id}")
        
        # Download memories
        cursor.execute("""
            SELECT id, content, metadata, created_at, updated_at
            FROM memories 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (user_id,))
        
        memories = cursor.fetchall()
        print(f"📚 Found {len(memories)} memories for user")
        
        # Convert to structured format
        raw_memories = []
        for memory in memories:
            memory_id, content, metadata, created_at, updated_at = memory
            
            raw_memory = {
                "id": str(memory_id),
                "content": content,
                "metadata": metadata if metadata else {},
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
                "user_id": user_id
            }
            raw_memories.append(raw_memory)
        
        cursor.close()
        conn.close()
        
        return raw_memories
        
    except Exception as e:
        print(f"❌ Error downloading memories: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return []

def main():
    parser = argparse.ArgumentParser(description='Download user memories from Supabase')
    parser.add_argument('--user-id', required=True, help='User ID to download memories for')
    parser.add_argument('--output', default='user_memories.json', help='Output file name')
    
    args = parser.parse_args()
    
    print("🗃️ User Memory Download Script")
    print("=" * 50)
    print(f"🔗 Downloading memories for user: {args.user_id}")
    
    # Download memories
    raw_memories = download_user_memories(args.user_id)
    
    if not raw_memories:
        print("❌ No memories downloaded")
        return
    
    # Save to JSON file
    output_data = {
        "user_id": args.user_id,
        "download_timestamp": datetime.now().isoformat(),
        "total_memories": len(raw_memories),
        "memories": raw_memories
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(raw_memories)} memories to '{args.output}'")
    print(f"📊 File size: {os.path.getsize(args.output) / 1024:.1f} KB")
    
    # Show sample of first few memories
    if raw_memories:
        print(f"\n📋 Sample memories:")
        for i, memory in enumerate(raw_memories[:3]):
            print(f"  {i+1}. {memory['content'][:60]}...")
            print(f"     Created: {memory['created_at']}")

if __name__ == "__main__":
    main() 