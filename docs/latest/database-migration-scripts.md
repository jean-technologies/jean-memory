# Database Migration Scripts for Development Environment

This document contains the scripts and procedures needed to migrate your production data to the development environment.

## Prerequisites

1. Production database access credentials
2. Development database instances created (Supabase, Qdrant, Neo4j)
3. Required CLI tools installed

## PostgreSQL Migration (Supabase)

### Schema-Only Migration (Recommended)

```bash
#!/bin/bash
# schema-migration.sh

# Set environment variables
PROD_DATABASE_URL="postgresql://postgres:[password]@db.[prod-project-id].supabase.co:5432/postgres"
DEV_DATABASE_URL="postgresql://postgres:[password]@db.[dev-project-id].supabase.co:5432/postgres"

echo "Starting schema migration from production to development..."

# Export schema only (no data)
echo "Exporting production schema..."
pg_dump --schema-only --no-owner --no-privileges $PROD_DATABASE_URL > schema.sql

# Import schema to development database
echo "Importing schema to development database..."
psql $DEV_DATABASE_URL < schema.sql

# Run Alembic to ensure migrations are up to date
echo "Running Alembic migrations..."
cd openmemory/api
alembic upgrade head

echo "Schema migration completed!"
```

### Data Migration (Optional - Use Carefully)

```bash
#!/bin/bash
# data-migration.sh

# WARNING: This will copy production data to development
# Only use sanitized/anonymized data for development

echo "Starting data migration (use with caution)..."

# Export specific tables with data
pg_dump --data-only --table=users --table=apps $PROD_DATABASE_URL > users_apps_data.sql

# Sanitize sensitive data (replace with dummy data)
sed -i 's/user@email\.com/dev-user@example.com/g' users_apps_data.sql
sed -i 's/[0-9]\{10,\}/1234567890/g' users_apps_data.sql  # Replace phone numbers

# Import sanitized data
psql $DEV_DATABASE_URL < users_apps_data.sql

echo "Data migration completed!"
```

## Qdrant Vector Database Migration

### Python Script for Collection Migration

```python
#!/usr/bin/env python3
# qdrant-migration.py

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Production Qdrant
PROD_QDRANT_HOST = "https://d696cac3-e12a-48f5-b529-5890e56e872e.us-east-1-0.aws.cloud.qdrant.io:6333"
PROD_QDRANT_KEY = os.getenv("PROD_QDRANT_API_KEY")

# Development Qdrant (replace with your dev cluster details)
DEV_QDRANT_HOST = "https://[dev-cluster-id].us-east-1-0.aws.cloud.qdrant.io:6333"
DEV_QDRANT_KEY = os.getenv("DEV_QDRANT_API_KEY")

def migrate_qdrant_collections():
    """Migrate Qdrant collections from production to development"""
    
    prod_client = QdrantClient(url=PROD_QDRANT_HOST, api_key=PROD_QDRANT_KEY)
    dev_client = QdrantClient(url=DEV_QDRANT_HOST, api_key=DEV_QDRANT_KEY)
    
    try:
        # Get all collections from production
        prod_collections = prod_client.get_collections()
        logger.info(f"Found {len(prod_collections.collections)} collections in production")
        
        for collection in prod_collections.collections:
            collection_name = collection.name
            logger.info(f"Processing collection: {collection_name}")
            
            # Get collection info
            collection_info = prod_client.get_collection(collection_name)
            
            # Create collection in development with same configuration
            dev_client.create_collection(
                collection_name=f"dev_{collection_name}",  # Prefix with 'dev_'
                vectors_config=VectorParams(
                    size=collection_info.config.params.vectors.size,
                    distance=collection_info.config.params.vectors.distance
                )
            )
            
            # Optional: Copy a subset of vectors (e.g., first 100 for testing)
            # This is optional and may not be needed for development
            # Uncomment if you want to copy some sample data
            """
            points, _ = prod_client.scroll(
                collection_name=collection_name,
                limit=100,  # Copy only first 100 points
                with_payload=True,
                with_vectors=True
            )
            
            if points:
                dev_client.upsert(
                    collection_name=f"dev_{collection_name}",
                    points=points
                )
                logger.info(f"Copied {len(points)} points to dev_{collection_name}")
            """
            
            logger.info(f"Created dev_{collection_name} collection")
            
    except Exception as e:
        logger.error(f"Error during Qdrant migration: {e}")
        raise

if __name__ == "__main__":
    migrate_qdrant_collections()
    print("Qdrant migration completed!")
```

## Neo4j Graph Database Migration

### Cypher Script for Graph Export/Import

```bash
#!/bin/bash
# neo4j-migration.sh

# Production Neo4j connection
PROD_NEO4J_URI="neo4j+s://12d02666.databases.neo4j.io"
PROD_NEO4J_USER="neo4j"
PROD_NEO4J_PASSWORD="[production-password]"

# Development Neo4j connection
DEV_NEO4J_URI="neo4j+s://[dev-instance-id].databases.neo4j.io"
DEV_NEO4J_USER="neo4j"
DEV_NEO4J_PASSWORD="[development-password]"

echo "Starting Neo4j graph migration..."

# Export graph from production (requires APOC plugin)
cypher-shell -a $PROD_NEO4J_URI -u $PROD_NEO4J_USER -p $PROD_NEO4J_PASSWORD \
  "CALL apoc.export.cypher.all('graph-export.cypher', {
    format: 'cypher-shell',
    useOptimizations: {type: 'UNWIND_BATCH', unwindBatchSize: 20}
  })"

# Download the exported file (if using Neo4j Aura, you'll need to access it through the browser)
echo "Please download graph-export.cypher from your production Neo4j browser"
echo "Then run the import script on development instance"

# Import to development (run this after downloading the export file)
# cypher-shell -a $DEV_NEO4J_URI -u $DEV_NEO4J_USER -p $DEV_NEO4J_PASSWORD < graph-export.cypher

echo "Neo4j migration preparation completed!"
```

### Alternative: Minimal Graph Setup

```cypher
// minimal-graph-setup.cypher
// Run this in development Neo4j if you don't want to copy production data

// Create indexes for better performance
CREATE INDEX user_id_index FOR (n:User) ON (n.user_id);
CREATE INDEX memory_id_index FOR (n:Memory) ON (n.memory_id);
CREATE INDEX entity_name_index FOR (n:Entity) ON (n.name);

// Create sample nodes for testing
CREATE (u:User {user_id: "dev-test-user-123", name: "Development Test User"});
CREATE (m:Memory {memory_id: "dev-memory-1", content: "Test memory for development"});
CREATE (e:Entity {name: "Test Entity", type: "Person"});

// Create sample relationships
MATCH (u:User {user_id: "dev-test-user-123"}), (m:Memory {memory_id: "dev-memory-1"})
CREATE (u)-[:HAS_MEMORY]->(m);

MATCH (m:Memory {memory_id: "dev-memory-1"}), (e:Entity {name: "Test Entity"})
CREATE (m)-[:MENTIONS]->(e);
```

## Complete Migration Script

```bash
#!/bin/bash
# complete-migration.sh

set -e  # Exit on any error

echo "Starting complete database migration for Jean Memory development environment..."

# Check required environment variables
required_vars=("PROD_DATABASE_URL" "DEV_DATABASE_URL" "PROD_QDRANT_API_KEY" "DEV_QDRANT_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

echo "✓ Environment variables validated"

# 1. PostgreSQL Schema Migration
echo "🗄️  Migrating PostgreSQL schema..."
pg_dump --schema-only --no-owner --no-privileges $PROD_DATABASE_URL > schema.sql
psql $DEV_DATABASE_URL < schema.sql
echo "✓ PostgreSQL schema migrated"

# 2. Run Alembic migrations
echo "🔄 Running Alembic migrations..."
cd openmemory/api
alembic upgrade head
cd ../..
echo "✓ Alembic migrations completed"

# 3. Qdrant Collection Migration
echo "🔍 Creating Qdrant development collections..."
python3 qdrant-migration.py
echo "✓ Qdrant collections created"

# 4. Neo4j Setup (minimal)
echo "🕸️  Setting up Neo4j development instance..."
cypher-shell -a $DEV_NEO4J_URI -u $DEV_NEO4J_USER -p $DEV_NEO4J_PASSWORD < minimal-graph-setup.cypher
echo "✓ Neo4j development setup completed"

# 5. Verify connections
echo "🔍 Verifying database connections..."

# Test PostgreSQL
psql $DEV_DATABASE_URL -c "SELECT COUNT(*) FROM users;" > /dev/null
echo "✓ PostgreSQL connection verified"

# Test Qdrant
python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='$DEV_QDRANT_HOST', api_key='$DEV_QDRANT_API_KEY')
print('✓ Qdrant connection verified')
print(f'Collections: {[c.name for c in client.get_collections().collections]}')
"

echo "🎉 Database migration completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update environment variables in Render dashboard"
echo "2. Deploy development services using render-dev.yaml"
echo "3. Test the development environment"
echo "4. Set up development workflow with dev branch"
```

## Environment Variables Template

Create a `.env.dev` file for local testing:

```bash
# .env.dev - Development environment variables

# Database URLs
DATABASE_URL=postgresql://postgres:[password]@db.[dev-project-id].supabase.co:5432/postgres
SUPABASE_URL=https://[dev-project-id].supabase.co
SUPABASE_SERVICE_KEY=[dev-service-key]
SUPABASE_ANON_KEY=[dev-anon-key]

# Qdrant Development
QDRANT_HOST=https://[dev-cluster-id].us-east-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=[dev-api-key]
QDRANT_PORT=6333

# Neo4j Development
NEO4J_URI=neo4j+s://[dev-instance-id].databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=[dev-password]

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# API Keys (same as production unless test versions available)
OPENAI_API_KEY=[same-as-prod]
GEMINI_API_KEY=[same-as-prod]
ANTHROPIC_API_KEY=[same-as-prod]

# Stripe (TEST KEYS)
STRIPE_SECRET_KEY=sk_test_[test-key]
STRIPE_WEBHOOK_SECRET=whsec_test_[test-webhook-secret]

# Collection Names (prefixed for development)
MAIN_QDRANT_COLLECTION_NAME=dev_main_collection
UNIFIED_QDRANT_COLLECTION_NAME=dev_unified_collection
```

## Safety Checklist

Before running migration scripts:

- [ ] Development database instances are created and accessible
- [ ] All environment variables are set correctly
- [ ] Production database credentials are read-only (if possible)
- [ ] Backup development databases before migration (in case of errors)
- [ ] Test scripts in a safe environment first
- [ ] Ensure no PII/sensitive data is copied to development
- [ ] Verify all connections work before proceeding
- [ ] Have rollback plan ready

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify database URLs and credentials
   - Check firewall/network settings
   - Ensure databases are running

2. **Permission Denied**
   - Verify user has necessary permissions
   - Check database user roles
   - Ensure service keys are correct

3. **Schema Conflicts**
   - Clear development database before import
   - Check for naming conflicts
   - Verify Alembic migration state

4. **Memory/Performance Issues**
   - Use smaller batch sizes for large migrations
   - Run migrations during off-peak hours
   - Monitor database resource usage

### Support Commands

```bash
# Check PostgreSQL connection
psql $DEV_DATABASE_URL -c "SELECT version();"

# List Qdrant collections
python3 -c "from qdrant_client import QdrantClient; print(QdrantClient(url='$DEV_QDRANT_HOST', api_key='$DEV_QDRANT_API_KEY').get_collections())"

# Test Neo4j connection
cypher-shell -a $DEV_NEO4J_URI -u $DEV_NEO4J_USER -p $DEV_NEO4J_PASSWORD "RETURN 'Connection successful' as status;"
```