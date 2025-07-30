#!/bin/bash

echo "🧪 Quick OAuth Test for jean-memory-api-dev"
echo "==========================================="

# Test 1: OAuth Discovery
echo -e "\n1️⃣ Testing OAuth Discovery..."
curl -s https://jean-memory-api-dev.onrender.com/.well-known/oauth-authorization-server | jq . || echo "❌ OAuth not deployed yet"

# Test 2: Health check
echo -e "\n2️⃣ Testing Health..."
curl -s https://jean-memory-api-dev.onrender.com/health | jq .

echo -e "\n✅ If you see the OAuth metadata above, it's working!"
echo "🔗 Authorization page: https://jean-memory-api-dev.onrender.com/oauth/authorize?client_id=test&redirect_uri=https://claude.ai/callback&response_type=code&state=test" 