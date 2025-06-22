# Security Setup for Unified Memory System

## Required Environment Variables

Before running the unified memory system, you need to set these environment variables:

### 1. Create `.env` file in project root:

```bash
# OpenAI API Keys
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key

# Neo4j Database Password
NEO4J_PASSWORD=your-neo4j-password-here

# Test User ID (for development/testing)
TEST_USER_ID=your-test-user-id-here

# Optional: Qdrant Vector Database (if using remote)
# QDRANT_URL=your-qdrant-url
# QDRANT_API_KEY=your-qdrant-api-key

# Optional: mem0 API (if using hosted service)
# MEM0_API_KEY=your-mem0-api-key
```

### 2. Set Environment Variables

**Option A: Using .env file (recommended)**
```bash
# Copy example and edit
cp .env.example .env
# Edit .env with your actual values
```

**Option B: Export in shell**
```bash
export OPENAI_API_KEY="your-key-here"
export GEMINI_API_KEY="your-key-here"
export NEO4J_PASSWORD="your-password-here"
export TEST_USER_ID="your-user-id-here"
```

### 3. Security Notes

- ✅ **No hardcoded credentials** in source code
- ✅ **Environment variables** for all sensitive data
- ✅ **Default fallback values** for development
- ⚠️ **Never commit** `.env` files to git
- ⚠️ **Use unique passwords** for production

### 4. Local Development Setup

For local development, you can use these defaults:

```bash
# Neo4j (if running locally with default setup)
NEO4J_PASSWORD="neo4j"

# Test User ID (generate a UUID)
TEST_USER_ID="$(python -c 'import uuid; print(str(uuid.uuid4()))')"
```

### 5. Production Considerations

- Use strong, unique passwords
- Rotate API keys regularly  
- Use environment-specific configurations
- Consider using secret management services (AWS Secrets Manager, etc.) 