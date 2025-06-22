#!/usr/bin/env python3
"""
Sample Memory Download Script for Testing
Downloads a sample of n memories from Supabase for testing the unified memory pipeline.
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
        # Supabase connection string format
        connection_string = "postgresql://postgres:[YOUR-PASSWORD]@db.masapxpxcwvsjpuymbmd.supabase.co:5432/postgres"
        
        # Get password from environment or prompt
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

def download_sample_memories(user_id, sample_size, strategy="diverse"):
    """
    Download a sample of memories for testing
    
    Args:
        user_id: User ID to download memories for
        sample_size: Number of memories to download
        strategy: Sampling strategy ('diverse', 'recent', 'random', 'oldest')
    """
    conn = connect_to_supabase()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Get user info
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
        
        # First, get total count
        cursor.execute("""
            SELECT COUNT(*) 
            FROM memories 
            WHERE user_id = %s
        """, (user_id,))
        
        total_memories = cursor.fetchone()[0]
        print(f"📚 Total memories for user: {total_memories}")
        
        if total_memories == 0:
            print("❌ No memories found for this user")
            return []
        
        # Adjust sample size if needed
        actual_sample_size = min(sample_size, total_memories)
        if actual_sample_size < sample_size:
            print(f"⚠️  Requested {sample_size} memories, but only {total_memories} available")
        
        print(f"📊 Sampling strategy: {strategy}")
        print(f"📊 Sample size: {actual_sample_size}/{total_memories} ({actual_sample_size/total_memories*100:.1f}%)")
        
        # Build query based on strategy
        if strategy == "diverse":
            # Get a diverse sample across time periods
            query = """
                WITH time_buckets AS (
                    SELECT 
                        id, content, metadata, created_at, updated_at,
                        ntile(10) OVER (ORDER BY created_at) as time_bucket
                    FROM memories 
                    WHERE user_id = %s
                ),
                sampled AS (
                    SELECT *, 
                           ROW_NUMBER() OVER (PARTITION BY time_bucket ORDER BY RANDOM()) as rn
                    FROM time_buckets
                )
                SELECT id, content, metadata, created_at, updated_at
                FROM sampled 
                WHERE rn <= GREATEST(1, %s / 10)
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (user_id, actual_sample_size, actual_sample_size))
            
        elif strategy == "recent":
            # Get most recent memories
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                LIMIT %s
            """, (user_id, actual_sample_size))
            
        elif strategy == "oldest":
            # Get oldest memories
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = %s 
                ORDER BY created_at ASC
                LIMIT %s
            """, (user_id, actual_sample_size))
            
        elif strategy == "random":
            # Get random sample
            cursor.execute("""
                SELECT id, content, metadata, created_at, updated_at
                FROM memories 
                WHERE user_id = %s 
                ORDER BY RANDOM()
                LIMIT %s
            """, (user_id, actual_sample_size))
            
        else:
            raise ValueError(f"Unknown sampling strategy: {strategy}")
        
        memories = cursor.fetchall()
        print(f"📚 Downloaded {len(memories)} sample memories")
        
        # Convert to structured format
        sample_memories = []
        for memory in memories:
            memory_id, content, metadata, created_at, updated_at = memory
            
            sample_memory = {
                "id": str(memory_id),
                "content": content,
                "metadata": metadata if metadata else {},
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None,
                "user_id": user_id
            }
            sample_memories.append(sample_memory)
        
        cursor.close()
        conn.close()
        
        return sample_memories
        
    except Exception as e:
        print(f"❌ Error downloading sample memories: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.close()
        return []

def analyze_sample_characteristics(memories):
    """Analyze the characteristics of the sample"""
    if not memories:
        return
    
    print(f"\n📊 Sample Analysis:")
    print("-" * 40)
    
    # Content length analysis
    content_lengths = [len(m['content']) for m in memories]
    avg_length = sum(content_lengths) / len(content_lengths)
    min_length = min(content_lengths)
    max_length = max(content_lengths)
    
    print(f"📝 Content Length:")
    print(f"   - Average: {avg_length:.1f} characters")
    print(f"   - Range: {min_length} - {max_length} characters")
    
    # Time range analysis
    dates = [datetime.fromisoformat(m['created_at'].replace('Z', '+00:00')) for m in memories if m['created_at']]
    if dates:
        dates.sort()
        time_span = dates[-1] - dates[0]
        print(f"📅 Time Range:")
        print(f"   - Oldest: {dates[0].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Newest: {dates[-1].strftime('%Y-%m-%d %H:%M')}")
        print(f"   - Span: {time_span.days} days")
    
    # Sample content preview
    print(f"\n📋 Sample Content Preview:")
    for i, memory in enumerate(memories[:5]):
        print(f"   {i+1}. {memory['content'][:60]}...")
        print(f"      Created: {memory['created_at']}")

def main():
    parser = argparse.ArgumentParser(description='Download sample memories for testing')
    parser.add_argument('--user-id', required=True, help='User ID to download memories for')
    parser.add_argument('--sample-size', type=int, default=50, help='Number of memories to sample (default: 50)')
    parser.add_argument('--strategy', choices=['diverse', 'recent', 'random', 'oldest'], 
                       default='diverse', help='Sampling strategy (default: diverse)')
    parser.add_argument('--output', default='sample_memories.json', help='Output file name')
    parser.add_argument('--analyze', action='store_true', help='Show sample analysis')
    
    args = parser.parse_args()
    
    print("🧪 Sample Memory Download Script")
    print("=" * 50)
    print(f"🔗 User ID: {args.user_id}")
    print(f"📊 Sample size: {args.sample_size}")
    print(f"🎯 Strategy: {args.strategy}")
    
    # Download sample memories
    sample_memories = download_sample_memories(args.user_id, args.sample_size, args.strategy)
    
    if not sample_memories:
        print("❌ No sample memories downloaded")
        return
    
    # Analyze sample if requested
    if args.analyze:
        analyze_sample_characteristics(sample_memories)
    
    # Save to JSON file
    output_data = {
        "user_id": args.user_id,
        "sample_strategy": args.strategy,
        "requested_sample_size": args.sample_size,
        "actual_sample_size": len(sample_memories),
        "download_timestamp": datetime.now().isoformat(),
        "memories": sample_memories
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved {len(sample_memories)} sample memories to '{args.output}'")
    print(f"📊 File size: {os.path.getsize(args.output) / 1024:.1f} KB")
    
    # Recommendations
    print(f"\n💡 Testing Recommendations:")
    if len(sample_memories) < 20:
        print("   🧪 Small sample - good for quick validation")
    elif len(sample_memories) < 100:
        print("   ⚖️ Medium sample - good for batch testing and quality assessment")
    else:
        print("   🏋️ Large sample - good for performance and scale testing")
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. Run batch preprocessing: python preprocess_memories_gemini_batch.py --input {args.output}")
    print(f"   2. Test unified memory ingestion")
    print(f"   3. Validate search functionality")
    print(f"   4. If satisfied, run full migration")

if __name__ == "__main__":
    main() 