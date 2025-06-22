# Unified Memory System - Deployment Guide

This guide provides step-by-step instructions for safely deploying the unified memory system from local development to production.

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development Setup](#local-development-setup)
3. [Testing Phase](#testing-phase)
4. [Production Deployment](#production-deployment)
5. [Rollback Plan](#rollback-plan)
6. [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🔍 Pre-Deployment Checklist

### Environment Isolation
- [ ] Verified on feature branch (`feature/unified-memory-*`)
- [ ] All changes isolated with feature flags
- [ ] No direct modifications to production code paths
- [ ] Environment check script passes: `python scripts/local-dev/unified-memory/check_environment.py`

### Code Review
- [ ] All unified memory code in separate modules
- [ ] Feature flags properly implemented (`USE_UNIFIED_MEMORY`)
- [ ] No hardcoded credentials or endpoints
- [ ] Error handling and fallbacks in place

### Testing
- [ ] Unit tests for unified memory components
- [ ] Integration tests with test data
- [ ] Migration script tested with dry run
- [ ] Performance benchmarks documented

---

## 🚀 Local Development Setup

### 1. Initial Setup

```bash
# Clone and checkout feature branch
git checkout feature/unified-memory-local-dev

# Navigate to unified memory directory
cd scripts/local-dev/unified-memory

# Copy environment template
cp env.unified-memory.template .env.unified-memory

# Edit and add your API keys
nano .env.unified-memory
```

### 2. Start Services

```bash
# Start Neo4j and Qdrant containers
./start-unified-memory.sh

# Verify services are running
docker ps | grep unified

# Check service health
curl http://localhost:7474  # Neo4j
curl http://localhost:6333/dashboard  # Qdrant
```

### 3. Install Dependencies

```bash
# Install unified memory dependencies
pip install -r scripts/local-dev/unified-memory/requirements-unified-memory.txt

# Verify installation
python -c "import graphiti_core; import neo4j; print('✅ Dependencies installed')"
```

### 4. Enable Unified Memory

```bash
# Add to your main .env file
echo "USE_UNIFIED_MEMORY=true" >> .env
echo "ENVIRONMENT=development" >> .env
echo "IS_LOCAL_UNIFIED_MEMORY=true" >> .env

# Restart API server
cd openmemory/api
uvicorn app.main:app --reload
```

---

## 🧪 Testing Phase

### 1. Data Export and Preprocessing

```bash
# Export production memories (read-only operation)
python download_raw_memories.py

# Preprocess with Gemini (enhances temporal data)
python preprocess_memories_gemini.py \
  --input memories.json \
  --output preprocessed_memories.json

# Verify preprocessing
python test_unified_memory_preprocessed.py
```

### 2. Migration Testing

```bash
# Dry run first (no data changes)
python scripts/local-dev/unified-memory/migrate_to_unified.py \
  --input preprocessed_memories.json \
  --user-id test_user_unified \
  --batch-size 10

# If dry run succeeds, execute migration
python scripts/local-dev/unified-memory/migrate_to_unified.py \
  --input preprocessed_memories.json \
  --user-id test_user_unified \
  --batch-size 10 \
  --execute
```

### 3. API Testing

```bash
# Test unified search endpoint
curl -X POST http://localhost:8000/api/v1/mcp/unified_search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "test query", "limit": 10}'

# Test unified add memory
curl -X POST http://localhost:8000/api/v1/mcp/unified_add_memory \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "Test memory with timestamp",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

### 4. UI Testing

1. Open the UI at http://localhost:3000
2. Test the enhanced Create Memory dialog with date picker
3. Verify memories are being stored in both systems
4. Test search functionality

---

## 🚢 Production Deployment

### Phase 1: Infrastructure Setup

```bash
# 1. Deploy Neo4j (managed service recommended)
# Example: Neo4j Aura, AWS Neptune, or self-hosted

# 2. Verify Qdrant Cloud is configured
# Your existing Qdrant Cloud instance can be used

# 3. Update production environment variables
ENVIRONMENT=production
USE_UNIFIED_MEMORY=false  # Keep disabled initially
NEO4J_URI=neo4j+s://your-neo4j-instance.io
NEO4J_PASSWORD=your-secure-password
```

### Phase 2: Code Deployment

```bash
# 1. Merge feature branch (with unified memory DISABLED)
git checkout main
git merge feature/unified-memory-local-dev

# 2. Deploy to production
# Your standard deployment process

# 3. Verify standard functionality still works
# All existing endpoints should function normally
```

### Phase 3: Gradual Rollout

```yaml
# Option 1: Feature flag by percentage
feature_flags:
  unified_memory:
    enabled: true
    rollout_percentage: 5  # Start with 5% of users

# Option 2: Feature flag by user list
feature_flags:
  unified_memory:
    enabled: true
    allowed_users:
      - "user_id_1"
      - "user_id_2"
```

### Phase 4: Full Migration

```bash
# 1. Run production migration script
python migrate_production_to_unified.py \
  --source production \
  --batch-size 100 \
  --parallel-workers 4

# 2. Monitor migration progress
tail -f unified_migration.log

# 3. Verify data integrity
python verify_migration_integrity.py
```

---

## 🔄 Rollback Plan

### Immediate Rollback (< 5 minutes)

```bash
# 1. Disable unified memory feature flag
UPDATE feature_flags SET enabled = false WHERE name = 'unified_memory';

# 2. Restart API servers
# Your standard restart process

# 3. Verify standard endpoints working
curl https://api.your-domain.com/health
```

### Data Rollback (if needed)

```bash
# 1. Stop unified memory writes
UPDATE feature_flags SET enabled = false WHERE name = 'unified_memory';

# 2. Export unified memory data (backup)
python export_unified_memories.py --output unified_backup.json

# 3. Restore to standard Mem0 if needed
python restore_standard_memories.py --input unified_backup.json
```

---

## 📊 Monitoring & Maintenance

### Key Metrics to Monitor

1. **Performance Metrics**
   - API response times (unified vs standard endpoints)
   - Database query performance
   - Memory usage

2. **Data Metrics**
   - Number of memories in each system
   - Search result quality scores
   - Entity extraction accuracy

3. **Error Metrics**
   - Failed memory additions
   - Search timeouts
   - Database connection errors

### Monitoring Commands

```bash
# Check Neo4j status
cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "MATCH (n) RETURN count(n) as node_count"

# Check Qdrant status
curl http://localhost:6333/collections/unified_memory_dev

# View API logs
tail -f /var/log/openmemory/api.log | grep unified

# Check migration status
cat migration_state.json | jq .
```

### Regular Maintenance

```bash
# Weekly: Backup unified memory data
python backup_unified_memory.py

# Monthly: Optimize Neo4j indices
cypher-shell -u neo4j -p $NEO4J_PASSWORD \
  "CALL db.indexes() YIELD name, state RETURN name, state"

# Quarterly: Review and clean up old data
python cleanup_old_memories.py --days 365
```

---

## 🎯 Success Criteria

### Technical Success
- [ ] All tests passing
- [ ] Performance within 10% of standard system
- [ ] Zero data loss during migration
- [ ] Rollback tested and verified

### Business Success
- [ ] Improved search relevance (measure with A/B tests)
- [ ] Enhanced temporal query capabilities
- [ ] Positive user feedback on new features

---

## 📚 Additional Resources

- [Unified Memory Architecture](ARCHITECTURE_UPDATE.md)
- [Migration Plan](MIGRATION_AND_ENHANCEMENT_PLAN.md)
- [API Documentation](docs/api/unified-memory.md)
- [Troubleshooting Guide](docs/troubleshooting/unified-memory.md)

---

## ⚠️ Important Notes

1. **Never enable unified memory in production without testing**
2. **Always run migrations with dry-run first**
3. **Keep feature flags as your safety net**
4. **Monitor closely during initial rollout**
5. **Have rollback plan ready at all times**

For questions or issues, contact the development team or create an issue in the repository. 