#!/bin/bash

# Unified Memory System - Local Development Stop Script
# This script stops the Neo4j and Qdrant services for unified memory development

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🛑 Stopping Unified Memory System services..."

cd "$SCRIPT_DIR"

# Stop Docker services
docker-compose -f docker-compose.unified-memory.yml down

echo "✅ All services stopped!"
echo ""
echo "💡 To remove data volumes (reset all data):"
echo "   docker-compose -f docker-compose.unified-memory.yml down -v"
echo ""
echo "🚀 To start services again: ./start-unified-memory.sh" 