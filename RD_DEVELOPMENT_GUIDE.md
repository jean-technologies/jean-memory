# R&D Development Guide

## 🎯 Overview

This guide provides a streamlined R&D environment for developing and refining your unified memory system using real customer data from Supabase while working locally.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Supabase Cloud │    │  Local Neo4j    │    │  Local Qdrant   │
│ (Customer Data) │────▶│ (Graph Memory)  │────▶│ (Vector Store)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Unified Memory  │
                       │    System       │
                       │ (mem0 + Graphiti)│
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ GraphRAG Pipeline│
                       │ (Query & Analysis)│
                       └─────────────────┘
```

## 🚀 Quick Start

### 1. One-Command Setup
```bash
# Auto-setup and run sample pipeline
python rd_quickstart.py --auto

# Interactive mode
python rd_quickstart.py
```

### 2. Manual Setup (if needed)
```bash
# Check environment
python rd_setup.py --check

# Create environment template
python rd_setup.py --create-env

# Start services
python rd_setup.py --start
```

## 📋 R&D Workflow

### Phase 1: Environment Setup
1. **Check Prerequisites**
   ```bash
   python rd_setup.py --check
   ```

2. **Configure Environment**
   - Edit `.env` with your production Supabase credentials
   - Ensure Docker is running
   - Install missing dependencies

3. **Start Services**
   ```bash
   python rd_setup.py --start
   ```

### Phase 2: Data Exploration
1. **Browse Available Users**
   ```bash
   python rd_development_pipeline.py --list-users
   ```

2. **Download Sample Data**
   ```bash
   python rd_development_pipeline.py --user-id USER_ID --sample-size 50
   ```

### Phase 3: Pipeline Development
1. **Test Ingestion**
   ```bash
   python rd_development_pipeline.py --interactive
   # Select option 3: Ingest memories
   ```

2. **Test Retrieval**
   ```bash
   # Select option 4: Test retrieval
   ```

3. **Analyze Results**
   ```bash
   # Select option 5: Analyze results
   ```

### Phase 4: Iteration & Refinement
1. **Modify Pipeline Components**
   - Edit `unified_memory_ingestion.py` for ingestion logic
   - Edit `graphrag_pipeline.py` for retrieval logic
   - Test changes with sample data

2. **Compare Results**
   - Use different user IDs
   - Vary sample sizes
   - Test different query types

## 🔧 Available Scripts

### Core Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `rd_quickstart.py` | One-command setup & execution | `python rd_quickstart.py --auto` |
| `rd_setup.py` | Environment management | `python rd_setup.py --check` |
| `rd_development_pipeline.py` | Full R&D pipeline | `python rd_development_pipeline.py --interactive` |

### Usage Examples

```bash
# Quick start with auto-selected user
python rd_quickstart.py --auto

# Run pipeline for specific user
python rd_quickstart.py --user-id abc123 --sample-size 100

# Full interactive pipeline
python rd_development_pipeline.py --interactive

# Check environment status
python rd_setup.py --check

# Start/stop services
python rd_setup.py --start
python rd_setup.py --stop
```

## 📊 Data Analysis

### Output Files (in `rd_data/` folder)

| File | Content |
|------|---------|
| `user_{id}_memories.json` | Downloaded memories |
| `user_{id}_retrieval_results.json` | Query results |
| `user_{id}_analysis.json` | Performance analysis |

### Key Metrics

- **Ingestion Success Rate**: % of memories successfully processed
- **Retrieval Success Rate**: % of queries that returned results
- **Source Diversity**: Average sources per query
- **Response Quality**: Response length and relevance

### Sample Analysis Output
```json
{
  "user_id": "abc123",
  "memory_analysis": {
    "total_memories": 50,
    "avg_content_length": 145,
    "content_types": {
      "fitness": 20,
      "work": 15,
      "general": 15
    }
  },
  "retrieval_analysis": {
    "success_rate": 0.85,
    "avg_response_length": 234,
    "avg_sources_per_query": 3.2
  },
  "recommendations": [
    "Consider improving graph traversal for better source diversity"
  ]
}
```

## 🔍 Testing Strategies

### 1. User Diversity Testing
```bash
# Test with different user types
python rd_development_pipeline.py --user-id fitness_user --sample-size 30
python rd_development_pipeline.py --user-id work_user --sample-size 30
python rd_development_pipeline.py --user-id general_user --sample-size 30
```

### 2. Sample Size Testing
```bash
# Test scalability
python rd_development_pipeline.py --user-id USER_ID --sample-size 10
python rd_development_pipeline.py --user-id USER_ID --sample-size 50
python rd_development_pipeline.py --user-id USER_ID --sample-size 100
```

### 3. Query Type Testing
Edit test queries in `rd_development_pipeline.py`:
```python
test_queries = [
    # Factual queries
    "What exercises do I do?",
    "Where do I work?",
    
    # Relationship queries  
    "Who do I work with?",
    "What places do I visit?",
    
    # Temporal queries
    "What are my daily routines?",
    "How have my habits changed?",
    
    # Complex queries
    "What are my fitness goals and progress?",
    "How do I balance work and personal life?"
]
```

## 🛠️ Development Tips

### 1. Debugging
- Check logs in `rd_pipeline.log`
- Use `--analyze` flag for detailed analysis
- Monitor Neo4j browser at `http://localhost:7474`
- Check Qdrant dashboard at `http://localhost:6333/dashboard`

### 2. Performance Optimization
- Start with small sample sizes (10-30 memories)
- Use specific user IDs for consistent testing
- Monitor memory usage during ingestion
- Test query performance with different complexity levels

### 3. Data Quality
- Check memory content length distribution
- Analyze temporal patterns in data
- Verify entity extraction quality in Neo4j
- Monitor vector embedding quality in Qdrant

## 🔄 Integration Path

### Phase 1: R&D (Current)
- Local development with real data
- Pipeline refinement and optimization
- Performance analysis and tuning

### Phase 2: MCP Integration
```python
# Update MCP tools to use unified memory system
# In openmemory/api/app/mcp/tools.py

@tool
async def add_memories_unified(content: str, user_id: str):
    """Add memory using unified system"""
    unified_system = UnifiedMemorySystem()
    return await unified_system.add_memory(content, user_id)

@tool  
async def deep_life_query_unified(query: str, user_id: str):
    """Deep query using GraphRAG pipeline"""
    pipeline = GraphRAGPipeline()
    return await pipeline.process_query(query, user_id)
```

### Phase 3: Website Integration
```python
# Update website endpoints
# In openmemory/api/app/routes/memory.py

@router.post("/memories/unified")
async def add_memory_unified(request: MemoryRequest):
    """Add memory using unified system"""
    # Implementation using UnifiedMemorySystem

@router.post("/query/graphrag")  
async def graphrag_query(request: QueryRequest):
    """GraphRAG-powered query"""
    # Implementation using GraphRAGPipeline
```

### Phase 4: Production Deployment
1. **Update render.yaml** (already done)
2. **Set up Neo4j AuraDB** (follow PRODUCTION_DEPLOYMENT_CHECKLIST.md)
3. **Deploy unified system**
4. **Monitor performance**

## 📈 Success Metrics

### Development Phase
- [ ] **Environment Setup**: All services running locally
- [ ] **Data Access**: Successfully downloading customer data
- [ ] **Ingestion**: >90% success rate for memory processing
- [ ] **Retrieval**: >80% success rate for test queries
- [ ] **Performance**: <2s response time for complex queries

### Integration Phase  
- [ ] **MCP Tools**: Updated to use unified system
- [ ] **Website Endpoints**: GraphRAG queries working
- [ ] **User Testing**: Positive feedback on query quality
- [ ] **Performance**: Production-ready response times

### Production Phase
- [ ] **Deployment**: Successful production deployment
- [ ] **Monitoring**: Performance metrics tracking
- [ ] **Scaling**: System handles production load
- [ ] **User Adoption**: Users actively using new features

## 🆘 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Docker services not starting | `docker-compose down && docker-compose up -d` |
| Supabase connection failed | Check SUPABASE_URL and SUPABASE_SERVICE_KEY |
| Neo4j connection timeout | Wait longer for Neo4j startup (30-60s) |
| Memory ingestion errors | Check memory content format and encoding |
| Low retrieval success rate | Verify graph relationships in Neo4j browser |

### Debug Commands
```bash
# Check service status
docker ps
python rd_setup.py --check

# View logs
tail -f rd_pipeline.log
docker-compose logs neo4j_db
docker-compose logs qdrant_db

# Test individual components
python -c "from rd_development_pipeline import RDPipeline; p = RDPipeline(); print(p.list_available_users())"
```

## 📞 Support

- **Environment Issues**: Check `rd_setup.py --check`
- **Pipeline Issues**: Check `rd_pipeline.log`
- **Data Issues**: Verify Supabase access
- **Performance Issues**: Monitor resource usage

---

**Happy R&D Development! 🚀** 