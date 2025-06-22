# Production Deployment Checklist

## 🎯 Overview

This checklist ensures your unified memory system is properly configured for production with Neo4j AuraDB integration.

## ✅ Pre-Deployment Setup

### 1. Neo4j AuraDB Setup

- [ ] **Create Neo4j AuraDB Instance**
  - Go to [Neo4j AuraDB](https://neo4j.com/cloud/aura/)
  - Create a new **AuraDB Free** instance
  - Choose your preferred region (recommend same as Render - Virginia)
  - Save the connection details securely

- [ ] **Record Connection Details**
  ```
  NEO4J_URI: neo4j+s://your-instance.databases.neo4j.io
  NEO4J_USER: neo4j
  NEO4J_PASSWORD: [generated-password]
  ```

- [ ] **Test Local Connection to AuraDB**
  ```bash
  python test_infrastructure_setup.py --prod
  ```

### 2. Render Environment Variables

- [ ] **Add Neo4j Variables to Render**
  In your Render dashboard, add these environment variables:
  
  ```
  NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=your-generated-password
  USE_UNIFIED_MEMORY=true
  UNIFIED_QDRANT_COLLECTION_NAME=unified_memory_prod
  ```

- [ ] **Verify Existing Variables**
  Ensure these are already set:
  ```
  OPENAI_API_KEY=your-openai-key
  QDRANT_HOST=your-cluster.region.gcp.cloud.qdrant.io
  QDRANT_API_KEY=your-qdrant-api-key
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_SERVICE_KEY=your-supabase-service-key
  ```

### 3. Code Deployment

- [ ] **Commit Updated render.yaml**
  ```bash
  git add render.yaml
  git commit -m "Add Neo4j AuraDB configuration for production"
  git push origin main
  ```

- [ ] **Verify Render Auto-Deploy**
  - Check Render dashboard for successful deployment
  - Monitor deployment logs for any errors

## 🚀 Post-Deployment Verification

### 1. Service Health Checks

- [ ] **API Health Check**
  ```bash
  curl https://jean-memory-api-virginia.onrender.com/health
  ```

- [ ] **Neo4j Connection Test**
  Check Render logs for Neo4j connection messages

- [ ] **Unified Memory System Test**
  Use the API docs to test memory operations:
  ```
  https://jean-memory-api-virginia.onrender.com/docs
  ```

### 2. Database Verification

- [ ] **Neo4j Browser Access**
  - Open [Neo4j Browser](https://browser.neo4j.io/)
  - Connect using your AuraDB credentials
  - Run: `MATCH (n) RETURN count(n)` to verify connection

- [ ] **Qdrant Collections**
  - Verify `unified_memory_prod` collection exists
  - Check vector count and dimensions

- [ ] **Supabase Tables**
  - Verify user authentication works
  - Check memory tables are accessible

### 3. End-to-End Testing

- [ ] **Memory Operations**
  - Add a test memory via API
  - Search for memories
  - Verify both vector and graph storage

- [ ] **GraphRAG Pipeline**
  - Test complex queries that use both mem0 and Graphiti
  - Verify relationship discovery works

## 🔧 Troubleshooting Guide

### Common Issues

#### Neo4j Connection Errors
```bash
# Check environment variables are set
curl -H "Authorization: Bearer YOUR_RENDER_TOKEN" \
  https://api.render.com/v1/services/YOUR_SERVICE_ID/env-vars

# Test connection manually
python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('neo4j+s://your-instance.databases.neo4j.io', 
                             auth=('neo4j', 'your-password'))
with driver.session() as session:
    result = session.run('RETURN 1')
    print('Connected!', result.single()[0])
driver.close()
"
```

#### Qdrant Collection Issues
```bash
# Check if production collection exists
curl -X GET "https://your-cluster.region.gcp.cloud.qdrant.io:6333/collections" \
  -H "api-key: your-api-key"

# Create collection if missing
curl -X PUT "https://your-cluster.region.gcp.cloud.qdrant.io:6333/collections/unified_memory_prod" \
  -H "api-key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 1536, "distance": "Cosine"}}'
```

#### Memory System Integration
```bash
# Test unified memory system
python -c "
import os
os.environ['ENVIRONMENT'] = 'production'
from openmemory.api.app.utils.unified_memory import UnifiedMemorySystem
system = UnifiedMemorySystem()
print('Unified memory system initialized successfully')
"
```

### Performance Monitoring

- [ ] **Set up monitoring** for:
  - API response times
  - Neo4j query performance
  - Qdrant search latency
  - Memory usage and storage

- [ ] **Configure alerts** for:
  - Service downtime
  - High error rates
  - Database connection failures

## 📊 Success Metrics

### Deployment Success Indicators

- [ ] **All services responding** (API, Neo4j, Qdrant, Supabase)
- [ ] **Memory operations working** (add, search, update, delete)
- [ ] **Graph relationships created** (entities and episodes)
- [ ] **Vector search functional** (semantic similarity)
- [ ] **No error logs** in production

### Performance Benchmarks

- [ ] **API response time** < 500ms for simple queries
- [ ] **GraphRAG queries** < 2s for complex searches
- [ ] **Memory ingestion** < 1s per memory
- [ ] **Vector search** < 200ms for similarity queries

## 🔐 Security Verification

- [ ] **No hardcoded credentials** in deployed code
- [ ] **Environment variables** properly set with `sync: false`
- [ ] **API keys** not exposed to frontend
- [ ] **Database connections** using SSL/TLS
- [ ] **Neo4j password** not in frontend environment

## 📈 Next Steps After Deployment

1. **Monitor performance** for 24-48 hours
2. **Test with real user data** (small batch first)
3. **Set up backup strategies** for Neo4j and Qdrant
4. **Document any production-specific configurations**
5. **Plan for scaling** if needed

## 🆘 Rollback Plan

If deployment fails:

1. **Revert render.yaml** to previous version
2. **Remove Neo4j environment variables** temporarily
3. **Disable unified memory features** with `USE_UNIFIED_MEMORY=false`
4. **Monitor for stability** before re-attempting

---

## 📞 Support Resources

- **Neo4j AuraDB Support**: [Neo4j Support](https://neo4j.com/support/)
- **Render Support**: [Render Documentation](https://render.com/docs)
- **Qdrant Support**: [Qdrant Documentation](https://qdrant.tech/documentation/)

**Estimated Deployment Time**: 30-45 minutes
**Required Downtime**: ~5 minutes during deployment 