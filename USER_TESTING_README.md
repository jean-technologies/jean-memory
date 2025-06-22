# User-Specific Unified Memory Testing

This directory contains scripts for testing the unified memory system (mem0 + Graphiti + GraphRAG) with real user data from your Supabase database.

## 🚀 Quick Start

The simplest way to test with a user:

```bash
# Test with 50 memories (default)
python quick_user_test.py <USER_ID>

# Test with 30 memories and interactive mode
python quick_user_test.py <USER_ID> --size 30 --interactive

# Test with 100 memories
python quick_user_test.py <USER_ID> --size 100
```

## 📋 Prerequisites

### 1. Environment Variables

Create a `.env` file with:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key
NEO4J_PASSWORD=your-neo4j-password
SUPABASE_DB_PASSWORD=your-supabase-password

# Optional (for enhanced preprocessing)
GEMINI_API_KEY=your-gemini-api-key

# Optional (if using remote services)
SUPABASE_DB_HOST=db.masapxpxcwvsjpuymbmd.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
```

### 2. Running Services

Make sure these services are running locally:

- **Neo4j**: `bolt://localhost:7687`
- **Qdrant**: `http://localhost:6333`

### 3. Python Dependencies

```bash
pip install psycopg2-binary neo4j qdrant-client openai google-generativeai python-dotenv
```

## 🛠️ Available Scripts

### `quick_user_test.py` (Recommended)
Simple wrapper with environment checks and sensible defaults.

```bash
python quick_user_test.py <USER_ID> [options]

Options:
  --size N          Number of memories to test (default: 50)
  --interactive     Enter interactive query mode after testing
  --skip-checks     Skip environment/service checks
```

### `test_user_unified_memory.py` (Advanced)
Full-featured testing pipeline with detailed control.

```bash
python test_user_unified_memory.py --user-id <USER_ID> [options]

Options:
  --sample-size N       Number of memories (default: 50)
  --interactive         Interactive mode
  --save-results FILE   Save results to JSON file
```

## 📊 What the Test Does

### Stage 1: Download User Memories
- Connects to your Supabase database
- Downloads the latest N memories for the specified user
- Saves raw memories to `user_{USER_ID}_raw_memories.json`

### Stage 2: Preprocess Memories (Optional)
- Uses Gemini to enhance temporal context and confidence scores
- Improves memory categorization
- Falls back to raw memories if preprocessing fails

### Stage 3: Initialize Unified System
- Sets up mem0 with Neo4j graph storage and Qdrant vector storage
- Initializes Graphiti for temporal episode creation
- Verifies all connections

### Stage 4: Ingest Memories
- Adds memories to mem0 (automatic entity extraction + vector storage)
- Creates temporal episodes with Graphiti
- Groups related memories by temporal context

### Stage 5: Test Queries
- Runs predefined test queries:
  - "What activities do I do?"
  - "Tell me about my recent memories"
  - "What happened this week?"
  - "Who are the people I interact with?"
  - "What are my interests?"

### Stage 6: Interactive Mode (Optional)
- Allows you to query the ingested memories interactively
- Shows results from both mem0 and Graphiti
- Type 'exit' to quit

## 📈 Sample Output

```
🚀 Quick User Memory Test
👤 User ID: abc123def456
📏 Sample size: 30
🎮 Interactive: True
============================================================

📥 STAGE 1: DOWNLOADING USER MEMORIES
============================================================
✅ Connected to Supabase database
👤 Found user: user@example.com (created: 2024-01-15)
📚 Found 30 memories for user
💾 Saved 30 raw memories to user_abc123de_raw_memories.json

🤖 STAGE 2: PREPROCESSING MEMORIES
============================================================
🤖 Preprocessing 30 memories with Gemini...
✅ Enhanced 30 memories
📊 Confidence distribution: {'high': 12, 'medium': 16, 'low': 2}

🧠 STAGE 3: INITIALIZING UNIFIED SYSTEM
============================================================
  🔧 Initializing mem0...
  ✅ mem0 ready
  🔧 Initializing Graphiti...
  ✅ Graphiti ready
🚀 Unified memory system initialized successfully

📝 STAGE 4: INGESTING MEMORIES
============================================================
  📝 Ingesting memory 1/30: I went to the gym this morning...
    ✅ mem0 ID: mem_abc123
  📝 Ingesting memory 2/30: Had lunch with Sarah at the cafe...
    ✅ mem0 ID: mem_def456
...
🎬 Creating temporal episodes with Graphiti...
✅ Created 8 temporal episodes
📊 Ingestion Summary:
  ✅ Successful: 30
  ❌ Failed: 0
  🎬 Episodes: 8

🔍 STAGE 5: TESTING QUERIES
============================================================

❓ Query 1: What activities do I do?
  📊 mem0: 8 results
  📊 Graphiti: 3 results
    1. I went to the gym this morning and did deadlifts...
    2. Had a productive work session on the AI project...

❓ Query 2: Tell me about my recent memories
  📊 mem0: 12 results
  📊 Graphiti: 5 results
...

🎮 STAGE 6: INTERACTIVE MODE
============================================================

🚀 Interactive Query Mode
==================================================
👤 User: abc123def456
📚 Memories ingested: 30
Type 'exit' to quit

❓ Your query: What did I eat yesterday?
🔍 Searching for: What did I eat yesterday?

📊 Results:
  mem0: 4 results
  Graphiti: 2 results

🧠 Top mem0 Results:
  1. Had lunch with Sarah at the cafe and ordered the salmon...
  2. Made a homemade protein smoothie for breakfast...
  3. Cooked ground turkey breakfast sandwiches...

--------------------------------------------------
❓ Your query: exit
👋 Goodbye!

🎉 TEST COMPLETED SUCCESSFULLY
============================================================
👤 User: abc123def456
📚 Memories processed: 30
✅ Successful ingestions: 30
🎬 Temporal episodes: 8
🔍 Test queries: 5

💾 Test results saved to: test_results_abc123de_20241222_143052.json
🎉 Test completed successfully!
```

## 🔧 Troubleshooting

### Database Connection Issues
```bash
# Check your Supabase connection
psql "postgresql://postgres:YOUR_PASSWORD@db.masapxpxcwvsjpuymbmd.supabase.co:5432/postgres" -c "SELECT version();"
```

### Service Check Issues
```bash
# Check Neo4j
curl http://localhost:7474/

# Check Qdrant
curl http://localhost:6333/collections
```

### Memory Issues
If you get memory errors with large datasets, reduce the sample size:
```bash
python quick_user_test.py <USER_ID> --size 20
```

## 📁 Output Files

The test creates several files:

- `user_{USER_ID}_raw_memories.json` - Raw memories from database
- `test_results_{USER_ID}_{timestamp}.json` - Complete test results
- Logs are printed to console

## 🎯 Recommended Testing Flow

1. **Start Small**: Test with `--size 20` first
2. **Check Results**: Review the generated JSON files
3. **Scale Up**: Increase to `--size 50` or more
4. **Interactive**: Use `--interactive` to explore queries
5. **Production**: Test with larger datasets (100+)

## 🔍 Performance Benchmarks

Expected performance for different sample sizes:

- **20 memories**: ~2-3 minutes
- **50 memories**: ~5-7 minutes  
- **100 memories**: ~10-15 minutes

Times include downloading, preprocessing, ingestion, and testing.

## 🚀 Next Steps

After successful testing:

1. **Analyze Results**: Review query performance and accuracy
2. **Tune Parameters**: Adjust confidence thresholds, sample sizes
3. **Scale Testing**: Test with multiple users
4. **Production Deploy**: Move to production environment

## 💡 Tips

- **Use Interactive Mode**: Great for exploring what the system learned
- **Check Entity Extraction**: Look for extracted relationships in Neo4j browser
- **Monitor Resources**: Watch memory usage with large datasets
- **Save Results**: Use `--save-results` for detailed analysis 