# Jean Memory Database Schema Documentation

## Overview

Jean Memory uses a multi-database architecture to provide efficient storage, retrieval, and analysis of user memories:

1. **PostgreSQL**: Primary relational database for metadata and user data
2. **Qdrant**: Vector database for semantic search capabilities
3. **Neo4j**: Graph database for relationship mapping and knowledge graphs

## PostgreSQL Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR UNIQUE NOT NULL,  -- Supabase user ID
    name VARCHAR,
    email VARCHAR UNIQUE,
    firstname VARCHAR(100),
    lastname VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    
    -- Subscription fields
    subscription_tier ENUM('FREE', 'PRO', 'ENTERPRISE') DEFAULT 'FREE',
    stripe_customer_id VARCHAR,
    stripe_subscription_id VARCHAR,
    subscription_status VARCHAR,
    subscription_current_period_end TIMESTAMP,
    
    -- SMS fields
    phone_number VARCHAR(20) UNIQUE,
    phone_verified BOOLEAN DEFAULT FALSE,
    phone_verification_attempts INTEGER DEFAULT 0,
    phone_verified_at TIMESTAMP,
    sms_enabled BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone_number);
```

### Apps Table
```sql
CREATE TABLE apps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id) NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Sync tracking
    last_synced_at TIMESTAMP,
    sync_status VARCHAR DEFAULT 'idle',  -- idle, syncing, failed
    sync_error TEXT,
    total_memories_created INTEGER DEFAULT 0,
    total_memories_accessed INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uq_user_app_name UNIQUE(owner_id, name)
);

CREATE INDEX idx_apps_owner ON apps(owner_id);
CREATE INDEX idx_apps_active ON apps(is_active);
```

### Memories Table
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    app_id UUID REFERENCES apps(id) NOT NULL,
    content TEXT NOT NULL,
    vector TEXT,  -- Legacy vector storage
    metadata JSONB DEFAULT '{}',
    state ENUM('active', 'paused', 'archived', 'deleted') DEFAULT 'active',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_memory_user_state ON memories(user_id, state);
CREATE INDEX idx_memory_app_state ON memories(app_id, state);
CREATE INDEX idx_memory_user_app ON memories(user_id, app_id);
```

### Categories Table
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR UNIQUE NOT NULL,
    description VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_category_name ON categories(name);
```

### Memory Categories (Junction Table)
```sql
CREATE TABLE memory_categories (
    memory_id UUID REFERENCES memories(id),
    category_id UUID REFERENCES categories(id),
    PRIMARY KEY (memory_id, category_id)
);

CREATE INDEX idx_memory_category ON memory_categories(memory_id, category_id);
```

### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    app_id UUID REFERENCES apps(id) NOT NULL,
    title VARCHAR NOT NULL,
    source_url VARCHAR,
    document_type VARCHAR NOT NULL,  -- 'substack', 'obsidian', 'medium', etc
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_user ON documents(user_id);
CREATE INDEX idx_documents_app ON documents(app_id);
CREATE INDEX idx_documents_type ON documents(document_type);
```

### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding FLOAT[],  -- Vector embedding
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_document_index ON document_chunks(document_id, chunk_index);
-- Full-text search index
CREATE INDEX idx_chunks_content_fts ON document_chunks USING gin(to_tsvector('english', content));
```

### User Narratives Table
```sql
CREATE TABLE user_narratives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) UNIQUE NOT NULL,
    narrative_content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_narrative_user_generated ON user_narratives(user_id, generated_at);
```

### SMS Conversations Table
```sql
CREATE TABLE sms_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    role ENUM('USER', 'ASSISTANT') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sms_conversation_user_created ON sms_conversations(user_id, created_at);
```

### API Keys Table
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR UNIQUE NOT NULL,  -- SHA-256 hash
    user_id UUID REFERENCES users(id) NOT NULL,
    name VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_apikey_user_id ON api_keys(user_id);
CREATE INDEX idx_apikey_active ON api_keys(is_active);
```

### Memory Access Logs Table
```sql
CREATE TABLE memory_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memories(id) NOT NULL,
    app_id UUID REFERENCES apps(id) NOT NULL,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_type VARCHAR NOT NULL,  -- 'read', 'search', 'update'
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_access_memory_time ON memory_access_logs(memory_id, accessed_at);
CREATE INDEX idx_access_app_time ON memory_access_logs(app_id, accessed_at);
```

## Qdrant Vector Database Schema

### Main Collection
```json
{
  "collection_name": "jean_memory_main",
  "vectors": {
    "size": 1536,  // OpenAI text-embedding-3-small
    "distance": "Cosine"
  },
  "payload_schema": {
    "user_id": "keyword",
    "app_id": "keyword",
    "memory_id": "keyword",
    "content": "text",
    "created_at": "datetime",
    "categories": "keyword[]",
    "metadata": "json"
  }
}
```

### Unified Collection (Phase 2)
```json
{
  "collection_name": "jean_memory_unified",
  "vectors": {
    "size": 1536,
    "distance": "Cosine"
  },
  "payload_schema": {
    "user_id": "keyword",
    "content_type": "keyword",  // 'memory', 'document_chunk'
    "source_id": "keyword",
    "content": "text",
    "metadata": "json"
  }
}
```

## Neo4j Graph Database Schema

### Node Types

#### User Node
```cypher
(:User {
  id: "user_uuid",
  name: "User Name",
  email: "user@example.com",
  created_at: datetime()
})
```

#### Memory Node
```cypher
(:Memory {
  id: "memory_uuid",
  content: "Memory content",
  created_at: datetime(),
  categories: ["category1", "category2"]
})
```

#### Entity Node
```cypher
(:Entity {
  id: "entity_uuid",
  name: "Entity Name",
  type: "person|place|organization|concept",
  metadata: {}
})
```

#### Document Node
```cypher
(:Document {
  id: "document_uuid",
  title: "Document Title",
  source: "substack",
  url: "https://...",
  created_at: datetime()
})
```

### Relationship Types

#### User Relationships
```cypher
(user:User)-[:HAS_MEMORY]->(memory:Memory)
(user:User)-[:OWNS_DOCUMENT]->(document:Document)
```

#### Memory Relationships
```cypher
(memory:Memory)-[:MENTIONS]->(entity:Entity)
(memory:Memory)-[:RELATES_TO]->(memory2:Memory)
(memory:Memory)-[:DERIVED_FROM]->(document:Document)
```

#### Entity Relationships
```cypher
(entity:Entity)-[:CONNECTED_TO {strength: 0.8}]->(entity2:Entity)
(entity:Entity)-[:PART_OF]->(entity2:Entity)
```

### Indexes
```cypher
CREATE INDEX user_id_index FOR (u:User) ON (u.id);
CREATE INDEX memory_id_index FOR (m:Memory) ON (m.id);
CREATE INDEX entity_name_index FOR (e:Entity) ON (e.name);
CREATE FULLTEXT INDEX memory_content FOR (m:Memory) ON (m.content);
```

## Data Relationships

### Cross-Database References

1. **PostgreSQL → Qdrant**
   - Memory ID links records
   - User ID for filtering
   - App ID for source tracking

2. **PostgreSQL → Neo4j**
   - User ID for node creation
   - Memory ID for relationships
   - Entity extraction from content

3. **Qdrant ↔ Neo4j**
   - Semantic search results enriched with graph context
   - Graph traversal guided by vector similarity

### Data Flow Example

```
1. User creates memory
   → PostgreSQL: Store metadata
   → Background job triggered
   
2. Background processing
   → Generate embedding (OpenAI)
   → Qdrant: Store vector + payload
   → Extract entities (NLP)
   → Neo4j: Create nodes/relationships
   
3. User searches memory
   → Embed query
   → Qdrant: Vector search
   → Neo4j: Enrich with relationships
   → PostgreSQL: Get full metadata
   → Return combined results
```

## Migration Management

### Alembic Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Key Migrations
1. `0b53c747049a_initial_migration.py` - Base schema
2. `0d81e543af1a_add_user_narratives_table.py` - Narrative support
3. `6a4b2e8f5c91_add_sms_fields_to_users.py` - SMS integration
4. `f8c6e2d514fc_add_document_table.py` - Document storage
5. `2834f44d4d7d_add_document_chunks_table.py` - Chunking support

## Performance Considerations

### PostgreSQL Optimizations
1. **Indexes**: Strategic indexes on foreign keys and search fields
2. **Partitioning**: Consider partitioning memories table by created_at
3. **Connection Pooling**: SQLAlchemy pool_size=10, max_overflow=20
4. **Query Optimization**: Use explain analyze for slow queries

### Qdrant Optimizations
1. **Collection Sharding**: Automatic based on data size
2. **HNSW Parameters**: m=16, ef_construct=128 for accuracy/speed balance
3. **Payload Indexing**: Index frequently filtered fields
4. **Batch Operations**: Insert/update in batches of 100-1000

### Neo4j Optimizations
1. **Node Labels**: Use specific labels for faster traversal
2. **Relationship Indexes**: Index frequently traversed relationships
3. **Query Tuning**: Use PROFILE to optimize Cypher queries
4. **Connection Pool**: Min=5, Max=50 connections

## Backup and Recovery

### PostgreSQL Backup
```bash
# Full backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

### Qdrant Backup
```bash
# Snapshot collection
curl -X POST "$QDRANT_HOST/collections/jean_memory_main/snapshots"

# Download snapshot
curl -O "$QDRANT_HOST/collections/jean_memory_main/snapshots/{snapshot_name}"
```

### Neo4j Backup
```bash
# Online backup
neo4j-admin backup --backup-dir=/backup --name=jean-memory

# Restore
neo4j-admin restore --from=/backup/jean-memory --database=neo4j
```