#!/bin/bash

# Unified Memory System - Local Development Startup Script
# This script starts the Neo4j and Qdrant services for unified memory development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "🚀 Starting Unified Memory System for Local Development"
echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Project root: $PROJECT_ROOT"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env.unified-memory" ]; then
    echo "⚠️  Environment file not found. Creating from template..."
    
    # Create .env file from template
    cat > "$SCRIPT_DIR/.env.unified-memory" << EOF
# Unified Memory System - Local Development Configuration
# IMPORTANT: Replace 'your_openai_api_key_here' with your actual OpenAI API key

# OpenAI API Key (required for embeddings and LLM processing)
OPENAI_API_KEY=your_openai_api_key_here

# Neo4j Connection Parameters (for both Graphiti and Mem0)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=fasho93fasho

# Qdrant Connection Parameters (for Mem0's vector store)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Mem0 Specific Graph Store (uses same Neo4j instance)
MEM0_GRAPH_STORE_URL=bolt://localhost:7687
MEM0_GRAPH_STORE_USERNAME=neo4j
MEM0_GRAPH_STORE_PASSWORD=fasho93fasho

# Local Development Flags
USE_UNIFIED_MEMORY=true
IS_LOCAL_UNIFIED_MEMORY=true
EOF

    echo "📄 Created .env.unified-memory file"
    echo "⚠️  IMPORTANT: Please edit $SCRIPT_DIR/.env.unified-memory and add your OpenAI API key"
    echo "   Replace 'your_openai_api_key_here' with your actual OpenAI API key"
    echo ""
    read -p "Press Enter after you've updated the API key..."
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" "$SCRIPT_DIR/.env.unified-memory"; then
    echo "❌ OpenAI API key not configured. Please edit $SCRIPT_DIR/.env.unified-memory"
    echo "   Replace 'your_openai_api_key_here' with your actual OpenAI API key"
    exit 1
fi

echo "🐳 Starting Docker services..."

# Start Docker services
cd "$SCRIPT_DIR"
docker-compose -f docker-compose.unified-memory.yml up -d

echo "⏳ Waiting for services to be ready..."

# Wait for Neo4j to be ready
echo "🔄 Waiting for Neo4j to be ready..."
timeout=60
counter=0
while ! docker exec neo4j_unified_memory cypher-shell -u neo4j -p fasho93fasho "RETURN 1" > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Neo4j failed to start within $timeout seconds"
        docker-compose -f docker-compose.unified-memory.yml logs neo4j_unified
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo "   Neo4j not ready yet... ($counter/$timeout seconds)"
done

# Wait for Qdrant to be ready
echo "🔄 Waiting for Qdrant to be ready..."
timeout=30
counter=0
while ! curl -s http://localhost:6333/health > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Qdrant failed to start within $timeout seconds"
        docker-compose -f docker-compose.unified-memory.yml logs qdrant_unified
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo "   Qdrant not ready yet... ($counter/$timeout seconds)"
done

echo "✅ All services are ready!"
echo ""
echo "📊 Service Status:"
echo "   🗄️  Neo4j:  http://localhost:7474 (Browser UI)"
echo "   🔍 Qdrant: http://localhost:6333/dashboard (Web UI)"
echo ""
echo "🔧 To use unified memory in your API:"
echo "   1. Set USE_UNIFIED_MEMORY=true in your main .env file"
echo "   2. Install additional dependencies:"
echo "      pip install -r $SCRIPT_DIR/requirements-unified-memory.txt"
echo "   3. Restart your API server"
echo ""
echo "🧪 Test endpoints available:"
echo "   POST /api/v1/mcp/unified_search"
echo "   POST /api/v1/mcp/unified_add_memory"
echo ""
echo "🛑 To stop services: ./stop-unified-memory.sh" 