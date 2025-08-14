#!/bin/bash

# Jean Memory SDK Test Runner
# Tests all three SDKs for immediate validation

set -e

echo "🧪 Jean Memory SDK Test Suite"
echo "============================="
echo ""

# Check environment
if [ -z "$JEAN_API_KEY" ]; then
    echo "⚠️  WARNING: JEAN_API_KEY not set - tests will validate structure only"
    echo "   Set JEAN_API_KEY for full end-to-end testing"
    echo ""
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📋 Test Plan:"
echo "  1. Python SDK - Headless backend functionality"
echo "  2. Node.js SDK - Server-side integration"  
echo "  3. React SDK - Frontend components (manual)"
echo ""

# Test Python SDK
echo "🐍 Testing Python SDK..."
echo "========================"
cd python-test
if python3 test_jean_memory.py; then
    echo "✅ Python SDK tests passed"
    PYTHON_SUCCESS=true
else
    echo "❌ Python SDK tests failed"
    PYTHON_SUCCESS=false
fi
echo ""

# Test Node.js SDK  
echo "📦 Testing Node.js SDK..."
echo "=========================="
cd ../node-test
if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install --silent
fi

if npm test; then
    echo "✅ Node.js SDK tests passed"
    NODE_SUCCESS=true
else
    echo "❌ Node.js SDK tests failed" 
    NODE_SUCCESS=false
fi
echo ""

# React SDK setup instructions
echo "⚛️  React SDK Test Instructions..."
echo "==================================="
echo "1. cd react-test"
echo "2. npm install"
echo "3. cp .env.local.example .env.local"
echo "4. Edit .env.local with your API key"
echo "5. npm run dev"
echo "6. Open http://localhost:3000"
echo "7. Test authentication and chat functionality"
echo ""

# Summary
echo "📊 Test Results Summary:"
echo "========================"

if [ "$PYTHON_SUCCESS" = true ]; then
    echo "✅ Python SDK: Ready"
else
    echo "❌ Python SDK: Issues found"
fi

if [ "$NODE_SUCCESS" = true ]; then
    echo "✅ Node.js SDK: Ready"  
else
    echo "❌ Node.js SDK: Issues found"
fi

echo "⚛️  React SDK: Manual testing required"
echo ""

if [ "$PYTHON_SUCCESS" = true ] && [ "$NODE_SUCCESS" = true ]; then
    echo "🚀 SDKs ready for production application development!"
    echo ""
    echo "📈 Recommended next steps:"
    echo "  1. Test React SDK manually"
    echo "  2. Build your first memory-enhanced application"
    echo "  3. Start with a simple chat interface"
    echo "  4. Iterate based on real usage"
else
    echo "⚠️  Fix failing tests before production use"
fi

cd "$SCRIPT_DIR"