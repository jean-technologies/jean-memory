# Production Testing Environment Plan: Clone User Approach

**Date**: December 22, 2024  
**Goal**: Set up a safe production testing environment for the multi-layer RAG system using a cloned test user

## 📋 Executive Summary

This plan outlines a minimal, robust approach to test your new multi-layer RAG system directly in production (jeanmemory.com) using a dedicated test user account. By cloning real user data to a test account, you can validate the full end-to-end pipeline in the actual production environment without affecting real users.

## 🏗️ Current System Architecture

### **What You've Built**

1. **Multi-Layer RAG System** (`SYSTEM_STATUS_REPORT.md`)
   - **pgvector** (PostgreSQL) for vector embeddings
   - **Neo4j** for graph relationships
   - **Graphiti** for temporal episode clustering
   - **mem0** as the unified memory layer
   - Successfully tested with 20 memories → 6 episodes

2. **Unified Memory Client** (`unified_memory.py`)
   - Compatibility layer supporting both old (Qdrant) and new systems
   - Feature flag-based routing
   - Multi-layer search capabilities
   - Automatic episode generation

3. **R&D Pipeline** (`rd_development_pipeline.py`)
   - Direct Supabase PostgreSQL access for data download
   - Dataset management system
   - Memory ingestion with episode creation
   - Retrieval testing with RAG responses

4. **Migration Plan** (`MEMORY_SYSTEM_MIGRATION_PLAN.md`)
   - 5-phase migration strategy
   - Infrastructure compatibility layer
   - Safe rollout procedures

### **Current Production Stack**
- **Frontend**: Next.js UI at jeanmemory.com
- **Backend**: FastAPI at api.jeanmemory.com
- **Database**: Supabase PostgreSQL
- **Vector Store**: Qdrant Cloud (current production)
- **Auth**: Supabase Auth
- **Memory Client**: mem0 with Qdrant provider

## 🎯 Testing Strategy: Clone User Approach

### **Why This Approach?**
1. **Real Production Testing**: Test the actual endpoints users interact with
2. **Safe Isolation**: No risk to real user data
3. **Easy Reset**: Can clear and refresh test data anytime
4. **Full Integration**: Tests auth, UI, API, and memory systems together

### **How It Works**
1. Create a dedicated test user account in production
2. Clone memories from a real user to this test account
3. Enable the new RAG system only for this test user
4. Test all features through the actual UI at jeanmemory.com
5. Monitor and analyze results

## 📝 Step-by-Step Implementation Plan

### **Phase 1: Infrastructure Setup** (Day 1)

#### **1.1 Deploy New Infrastructure Components**

First, deploy the new memory infrastructure alongside existing production:

```bash
# 1. SSH into your production server
ssh your-server

# 2. Create docker-compose.prod-testing.yml
cat > docker-compose.prod-testing.yml << 'EOF'
version: '3.8'
services:
  postgres-pgvector:
    image: pgvector/pgvector:pg16
    container_name: mem0_pgvector_test
    environment:
      POSTGRES_DB: mem0_unified
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    volumes:
      - pgvector_test_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # Different port to avoid conflicts
    networks:
      - memory_test_network

  neo4j:
    image: neo4j:5.15.0
    container_name: mem0_neo4j_test
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_server_memory_heap_initial__size: 512m
      NEO4J_server_memory_heap_max__size: 1G
    volumes:
      - neo4j_test_data:/data
    ports:
      - "7475:7474"  # HTTP (different port)
      - "7688:7687"  # Bolt (different port)
    networks:
      - memory_test_network

networks:
  memory_test_network:
    driver: bridge

volumes:
  pgvector_test_data:
  neo4j_test_data:
EOF

# 3. Start the test infrastructure
docker-compose -f docker-compose.prod-testing.yml up -d

# 4. Verify services are running
docker ps | grep -E "mem0_pgvector_test|mem0_neo4j_test"
```

#### **1.2 Update Environment Configuration**

Add test infrastructure configuration to your production `.env`:

```bash
# Add to production .env file
cat >> .env << 'EOF'

# Test Infrastructure (for clone user testing)
TEST_USE_UNIFIED_MEMORY=true
TEST_PG_HOST=localhost
TEST_PG_PORT=5433
TEST_PG_USER=postgres
TEST_PG_PASSWORD=your_secure_password
TEST_PG_DBNAME=mem0_unified

TEST_NEO4J_URI=bolt://localhost:7688
TEST_NEO4J_USER=neo4j
TEST_NEO4J_PASSWORD=your_secure_password

# Test user configuration
TEST_USER_EMAIL=test.rag@jeanmemory.com
TEST_USER_PASSWORD=secure_test_password_2024
UNIFIED_MEMORY_TEST_USER_ID=  # Will be filled after user creation
EOF
```

### **Phase 2: Test User Setup** (Day 1)

#### **2.1 Create Test User Script**

Create `scripts/setup_test_user.py`:

```python
#!/usr/bin/env python3
"""
Setup script for creating and managing the RAG test user
"""

import os
import sys
import json
import asyncio
import psycopg2
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

load_dotenv()

class TestUserManager:
    def __init__(self):
        # Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Direct DB connection
        self.db_conn = psycopg2.connect(
            host=os.getenv("SUPABASE_DB_HOST", "db.masapxpxcwvsjpuymbmd.supabase.co"),
            port=5432,
            database="postgres",
            user="postgres",
            password=os.getenv("SUPABASE_DB_PASSWORD")
        )
        
        self.test_email = os.getenv("TEST_USER_EMAIL", "test.rag@jeanmemory.com")
        self.test_password = os.getenv("TEST_USER_PASSWORD", "secure_test_password_2024")
    
    def create_test_user(self) -> Dict[str, Any]:
        """Create or get the test user account"""
        try:
            # Try to sign in first
            response = self.supabase.auth.sign_in_with_password({
                "email": self.test_email,
                "password": self.test_password
            })
            print(f"✅ Test user already exists: {response.user.id}")
            return {
                "user_id": response.user.id,
                "email": self.test_email,
                "status": "existing"
            }
        except:
            # Create new user
            response = self.supabase.auth.sign_up({
                "email": self.test_email,
                "password": self.test_password,
                "options": {
                    "data": {
                        "name": "RAG Test User",
                        "role": "test_user",
                        "is_test_account": True
                    }
                }
            })
            print(f"✅ Created new test user: {response.user.id}")
            
            # Update .env with the user ID
            self._update_env_file("UNIFIED_MEMORY_TEST_USER_ID", response.user.id)
            
            return {
                "user_id": response.user.id,
                "email": self.test_email,
                "status": "created"
            }
    
    def clone_user_memories(self, source_user_id: str, limit: Optional[int] = None) -> int:
        """Clone memories from source user to test user"""
        cursor = self.db_conn.cursor()
        
        try:
            # Get test user ID from Supabase
            test_user = self.supabase.auth.get_user()
            test_user_id = test_user.user.id
            
            # Clear existing memories for test user
            cursor.execute("""
                DELETE FROM memories 
                WHERE user_id = (SELECT id FROM users WHERE user_id = %s)
            """, (test_user_id,))
            
            # Clone memories from source user
            clone_query = """
                INSERT INTO memories (
                    user_id, content, metadata, created_at, updated_at
                )
                SELECT 
                    (SELECT id FROM users WHERE user_id = %s) as user_id,
                    content,
                    metadata || jsonb_build_object(
                        'cloned_from', %s,
                        'cloned_at', %s,
                        'is_test_data', true
                    ) as metadata,
                    created_at,
                    updated_at
                FROM memories
                WHERE user_id = (SELECT id FROM users WHERE user_id = %s)
                AND deleted_at IS NULL
                ORDER BY created_at DESC
            """
            
            if limit:
                clone_query += f" LIMIT {limit}"
            
            cursor.execute(clone_query, (
                test_user_id,
                source_user_id,
                datetime.now().isoformat(),
                source_user_id
            ))
            
            cloned_count = cursor.rowcount
            self.db_conn.commit()
            
            print(f"✅ Cloned {cloned_count} memories from {source_user_id} to test user")
            return cloned_count
            
        except Exception as e:
            self.db_conn.rollback()
            print(f"❌ Error cloning memories: {e}")
            raise
        finally:
            cursor.close()
    
    def clear_test_user_data(self):
        """Clear all data for the test user"""
        cursor = self.db_conn.cursor()
        
        try:
            test_user = self.supabase.auth.get_user()
            test_user_id = test_user.user.id
            
            # Clear memories
            cursor.execute("""
                DELETE FROM memories 
                WHERE user_id = (SELECT id FROM users WHERE user_id = %s)
            """, (test_user_id,))
            
            # Clear documents
            cursor.execute("""
                DELETE FROM documents 
                WHERE user_id = (SELECT id FROM users WHERE user_id = %s)
            """, (test_user_id,))
            
            self.db_conn.commit()
            print(f"✅ Cleared all data for test user")
            
        except Exception as e:
            self.db_conn.rollback()
            print(f"❌ Error clearing data: {e}")
            raise
        finally:
            cursor.close()
    
    def _update_env_file(self, key: str, value: str):
        """Update .env file with new value"""
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated = True
                    break
            
            if not updated:
                lines.append(f"{key}={value}\n")
            
            with open(env_path, 'w') as f:
                f.writelines(lines)

def main():
    manager = TestUserManager()
    
    # Step 1: Create test user
    print("\n📝 Step 1: Creating test user...")
    user_info = manager.create_test_user()
    
    # Step 2: Select source user
    print("\n📝 Step 2: Select source user to clone...")
    print("Available options:")
    print("1. Use a specific user ID")
    print("2. List top users by memory count")
    
    choice = input("\nEnter choice (1 or 2): ")
    
    if choice == "2":
        # List top users
        cursor = manager.db_conn.cursor()
        cursor.execute("""
            SELECT user_id, COUNT(*) as memory_count 
            FROM memories 
            WHERE deleted_at IS NULL
            GROUP BY user_id 
            HAVING COUNT(*) >= 10
            ORDER BY memory_count DESC 
            LIMIT 10
        """)
        users = cursor.fetchall()
        cursor.close()
        
        print("\nTop users by memory count:")
        for i, (user_id, count) in enumerate(users, 1):
            print(f"{i}. {user_id[:8]}... ({count} memories)")
        
        selection = int(input("\nSelect user number: ")) - 1
        source_user_id = users[selection][0]
    else:
        source_user_id = input("Enter source user ID: ")
    
    # Step 3: Clone memories
    print(f"\n📝 Step 3: Cloning memories from {source_user_id}...")
    memory_limit = input("Enter memory limit (or press Enter for all): ")
    memory_limit = int(memory_limit) if memory_limit else None
    
    cloned_count = manager.clone_user_memories(source_user_id, memory_limit)
    
    print(f"\n✅ Setup complete!")
    print(f"Test user email: {manager.test_email}")
    print(f"Test user ID: {user_info['user_id']}")
    print(f"Memories cloned: {cloned_count}")
    print(f"\nYou can now log in at https://jeanmemory.com with the test credentials")

if __name__ == "__main__":
    main()
```

#### **2.2 Run Test User Setup**

```bash
# Make script executable
chmod +x scripts/setup_test_user.py

# Run the setup
python scripts/setup_test_user.py
```

### **Phase 3: Enable New System for Test User** (Day 2)

#### **3.1 Update UnifiedMemoryClient**

Modify `openmemory/api/app/utils/unified_memory.py` to check for test user:

```python
def should_use_unified_memory(user_id: str) -> bool:
    """Determine if user should use new unified memory system"""
    
    # Always use new system for test user
    test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID")
    if test_user_id and user_id == test_user_id:
        # Use test infrastructure for test user
        os.environ["PG_HOST"] = os.getenv("TEST_PG_HOST", "localhost")
        os.environ["PG_PORT"] = os.getenv("TEST_PG_PORT", "5433")
        os.environ["NEO4J_URI"] = os.getenv("TEST_NEO4J_URI", "bolt://localhost:7688")
        return True
    
    # Check other conditions...
    return False
```

#### **3.2 Deploy Code Changes**

```bash
# 1. Commit changes
git add -A
git commit -m "Enable unified memory for test user"

# 2. Deploy to production
git push origin main

# 3. Restart API service
ssh your-server
cd /path/to/openmemory
docker-compose restart api

# 4. Verify deployment
curl https://api.jeanmemory.com/health
```

### **Phase 4: Initialize Test Data** (Day 2)

#### **4.1 Create Data Migration Script**

Create `scripts/migrate_test_user_data.py`:

```python
#!/usr/bin/env python3
"""
Migrate test user data from Qdrant to new unified memory system
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from openmemory.api.app.utils.unified_memory import UnifiedMemoryClient
from qdrant_client import QdrantClient

load_dotenv()

async def migrate_test_user():
    test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID")
    if not test_user_id:
        print("❌ Test user ID not found in environment")
        return
    
    print(f"🔄 Migrating data for test user: {test_user_id}")
    
    # Initialize clients
    qdrant = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    
    unified_client = UnifiedMemoryClient(use_new_system=True, user_id=test_user_id)
    
    # Fetch memories from Qdrant
    offset = None
    migrated_count = 0
    
    while True:
        results, offset = qdrant.scroll(
            collection_name="openmemory_prod",
            scroll_filter={
                "must": [{"key": "user_id", "match": {"value": test_user_id}}]
            },
            limit=100,
            offset=offset
        )
        
        if not results:
            break
        
        # Migrate each memory
        for point in results:
            memory_text = point.payload.get("data", "")
            metadata = point.payload
            
            await unified_client.add(
                text=memory_text,
                user_id=test_user_id,
                metadata=metadata
            )
            
            migrated_count += 1
            if migrated_count % 10 == 0:
                print(f"   Migrated {migrated_count} memories...")
        
        if not offset:
            break
    
    # Generate episodes
    print(f"🎬 Generating episodes for {migrated_count} memories...")
    await unified_client.generate_user_episodes(test_user_id)
    
    print(f"✅ Migration complete! Migrated {migrated_count} memories")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    test_queries = [
        "What are my daily routines?",
        "What projects am I working on?",
        "Tell me about my fitness activities"
    ]
    
    for query in test_queries:
        results = await unified_client.search(query, test_user_id, limit=5)
        print(f"\nQuery: {query}")
        print(f"Results: {len(results)} memories found")

if __name__ == "__main__":
    asyncio.run(migrate_test_user())
```

#### **4.2 Run Migration**

```bash
# Run the migration
python scripts/migrate_test_user_data.py
```

### **Phase 5: Testing & Monitoring** (Day 3)

#### **5.1 Create Testing Dashboard**

Create `scripts/test_user_monitor.py`:

```python
#!/usr/bin/env python3
"""
Monitor and analyze test user performance
"""

import os
import time
import json
import asyncio
from datetime import datetime
from typing import Dict, List
import psycopg2
from neo4j import AsyncGraphDatabase

class TestUserMonitor:
    def __init__(self):
        self.test_user_id = os.getenv("UNIFIED_MEMORY_TEST_USER_ID")
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=os.getenv("TEST_PG_HOST"),
            port=int(os.getenv("TEST_PG_PORT")),
            database=os.getenv("TEST_PG_DBNAME"),
            user=os.getenv("TEST_PG_USER"),
            password=os.getenv("TEST_PG_PASSWORD")
        )
        
        # Neo4j connection
        self.neo4j_driver = AsyncGraphDatabase.driver(
            os.getenv("TEST_NEO4J_URI"),
            auth=(os.getenv("TEST_NEO4J_USER"), os.getenv("TEST_NEO4J_PASSWORD"))
        )
    
    async def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "test_user_id": self.test_user_id
        }
        
        # PostgreSQL stats
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE user_id = %s
        """, (self.test_user_id,))
        stats["memory_count"] = cursor.fetchone()[0]
        cursor.close()
        
        # Neo4j stats
        async with self.neo4j_driver.session() as session:
            # Count Memory nodes
            result = await session.run("""
                MATCH (m:Memory {user_id: $user_id})
                RETURN count(m) as memory_nodes
            """, user_id=self.test_user_id)
            record = await result.single()
            stats["neo4j_memory_nodes"] = record["memory_nodes"] if record else 0
            
            # Count episodes
            result = await session.run("""
                MATCH (e:Episodic)
                WHERE e.name CONTAINS $user_id
                RETURN count(e) as episode_count
            """, user_id=self.test_user_id)
            record = await result.single()
            stats["episode_count"] = record["episode_count"] if record else 0
            
            # Count relationships
            result = await session.run("""
                MATCH (m:Memory {user_id: $user_id})-[r]->()
                RETURN count(r) as relationship_count
            """, user_id=self.test_user_id)
            record = await result.single()
            stats["relationship_count"] = record["relationship_count"] if record else 0
        
        return stats
    
    async def test_search_performance(self, queries: List[str]) -> Dict:
        """Test search performance"""
        from openmemory.api.app.utils.unified_memory import UnifiedMemoryClient
        
        client = UnifiedMemoryClient(use_new_system=True, user_id=self.test_user_id)
        results = {}
        
        for query in queries:
            start_time = time.time()
            search_results = await client.search_multilayer(
                query=query,
                user_id=self.test_user_id,
                limit=10,
                search_types=["semantic", "graph", "episodic"]
            )
            end_time = time.time()
            
            results[query] = {
                "response_time": end_time - start_time,
                "result_count": len(search_results),
                "sources": {
                    "semantic": len([r for r in search_results if r.get("source") == "semantic"]),
                    "graph": len([r for r in search_results if r.get("source") == "graph"]),
                    "episodic": len([r for r in search_results if r.get("source") == "episodic"])
                }
            }
        
        return results
    
    async def generate_report(self):
        """Generate comprehensive test report"""
        print("📊 Test User Performance Report")
        print("=" * 50)
        
        # System stats
        stats = await self.get_system_stats()
        print(f"\n📈 System Statistics:")
        print(f"  - Memories in pgvector: {stats['memory_count']}")
        print(f"  - Memory nodes in Neo4j: {stats['neo4j_memory_nodes']}")
        print(f"  - Episodes created: {stats['episode_count']}")
        print(f"  - Relationships: {stats['relationship_count']}")
        
        # Search performance
        test_queries = [
            "What did I do yesterday?",
            "Tell me about my work projects",
            "What are my fitness goals?",
            "Who do I work with?",
            "What places do I visit frequently?"
        ]
        
        print(f"\n🔍 Search Performance:")
        perf_results = await self.test_search_performance(test_queries)
        
        for query, metrics in perf_results.items():
            print(f"\n  Query: '{query}'")
            print(f"    - Response time: {metrics['response_time']:.3f}s")
            print(f"    - Total results: {metrics['result_count']}")
            print(f"    - Sources: {metrics['sources']}")
        
        # Save report
        report = {
            "stats": stats,
            "performance": perf_results
        }
        
        with open(f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Report saved to test_report_*.json")

async def main():
    monitor = TestUserMonitor()
    await monitor.generate_report()
    await monitor.neo4j_driver.close()

if __name__ == "__main__":
    asyncio.run(main())
```

#### **5.2 Testing Checklist**

Log into jeanmemory.com with test credentials and verify:

1. **Memory Creation**
   - [ ] Create new memory via UI
   - [ ] Verify it appears in memory list
   - [ ] Check it's stored in pgvector (not Qdrant)

2. **Search Functionality**
   - [ ] Test basic search queries
   - [ ] Verify multi-layer results (semantic + graph + episodic)
   - [ ] Compare response quality vs old system

3. **Deep Life Query**
   - [ ] Ask complex questions
   - [ ] Verify episode-aware responses
   - [ ] Check response time

4. **Generate Narrative**
   - [ ] Generate life narrative
   - [ ] Verify it uses episodic structure
   - [ ] Compare quality vs old system

### **Phase 6: Continuous Testing** (Ongoing)

#### **6.1 Create Reset Script**

Create `scripts/reset_test_user.py`:

```python
#!/usr/bin/env python3
"""
Reset test user for fresh testing
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from scripts.setup_test_user import TestUserManager

def main():
    manager = TestUserManager()
    
    print("🔄 Resetting test user data...")
    
    # Clear existing data
    manager.clear_test_user_data()
    
    # Re-clone from source
    source_user_id = input("Enter source user ID to clone from: ")
    limit = input("Enter memory limit (or press Enter for all): ")
    limit = int(limit) if limit else None
    
    cloned_count = manager.clone_user_memories(source_user_id, limit)
    
    print(f"✅ Reset complete! Cloned {cloned_count} memories")

if __name__ == "__main__":
    main()
```

## 📊 Monitoring & Analysis

### **Key Metrics to Track**

1. **Performance Metrics**
   - Search response time (target: < 500ms)
   - Memory ingestion time
   - Episode generation time

2. **Quality Metrics**
   - Search result relevance
   - Episode coherence
   - Narrative quality

3. **System Health**
   - Memory usage
   - Database connections
   - Error rates

### **Logging Configuration**

Add to your API configuration:

```python
# Enhanced logging for test user
if user_id == os.getenv("UNIFIED_MEMORY_TEST_USER_ID"):
    logger.info(f"TEST_USER_OPERATION: {operation_name}", extra={
        "user_id": user_id,
        "system": "unified",
        "timestamp": datetime.now().isoformat(),
        "metrics": operation_metrics
    })
```

## 🚀 Quick Start Commands

```bash
# 1. Initial setup (run once)
./scripts/setup_test_user.py

# 2. Deploy infrastructure
docker-compose -f docker-compose.prod-testing.yml up -d

# 3. Migrate test user data
python scripts/migrate_test_user_data.py

# 4. Monitor performance
python scripts/test_user_monitor.py

# 5. Reset for new test
python scripts/reset_test_user.py
```

## 🔒 Security Considerations

1. **Test User Isolation**
   - Test user can only access its own data
   - Cannot affect other users
   - Clearly marked as test account

2. **Infrastructure Isolation**
   - Separate ports for test services
   - Different database/collection names
   - Independent from production data

3. **Access Control**
   - Test credentials stored securely
   - Limited to authorized testers
   - Regular password rotation

## 📝 Next Steps

1. **Week 1**: Set up infrastructure and test user
2. **Week 2**: Run comprehensive tests
3. **Week 3**: Analyze results and optimize
4. **Week 4**: Prepare for gradual production rollout

This approach gives you a safe, controlled environment to validate your new multi-layer RAG system in production without any risk to real users. You can iterate quickly, reset as needed, and gather real performance data before the full migration. 