#!/bin/bash

echo "🧪 Testing Cloudflare Worker for ChatGPT SSE Support"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

USER_ID="2822dc63-74a4-4ba1-b406-166352591123"
BACKEND_URL="https://jean-memory-api-virginia.onrender.com"

echo "1. Testing direct backend (should fail for POST to SSE):"
echo "---------------------------------------------------------"

echo -n "  GET  /mcp/chatgpt/sse/$USER_ID: "
if curl -s -f -N "$BACKEND_URL/mcp/chatgpt/sse/$USER_ID" 2>/dev/null | head -1 | grep -q "event: endpoint"; then
    echo -e "${GREEN}✓ Works${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
fi

echo -n "  POST /mcp/chatgpt/sse/$USER_ID: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/mcp/chatgpt/sse/$USER_ID" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
if [ "$STATUS" = "405" ]; then
    echo -e "${RED}✗ Returns 405 (Expected - This is why we need the Worker!)${NC}"
else
    echo -e "${RED}✗ Unexpected status: $STATUS${NC}"
fi

echo -n "  POST /mcp/chatgpt/messages/$USER_ID: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BACKEND_URL/mcp/chatgpt/messages/$USER_ID" \
    -H "Content-Type: application/json" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}')
if [ "$STATUS" = "400" ] || [ "$STATUS" = "204" ] || [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Accepts POST (Status: $STATUS)${NC}"
else
    echo -e "${RED}✗ Failed with status: $STATUS${NC}"
fi

echo ""
echo "2. Summary:"
echo "-----------"
echo "  ❌ ChatGPT cannot use the backend directly because:"
echo "     - ChatGPT POSTs to the SSE endpoint"
echo "     - Backend returns 405 Method Not Allowed for POST to SSE"
echo ""
echo "  ✅ Solution: Deploy the Cloudflare Worker"
echo "     - Accepts both GET and POST to SSE"
echo "     - Handles protocol conversion"
echo "     - Maintains session state with Durable Objects"
echo ""
echo "3. To deploy the worker:"
echo "------------------------"
echo "  npm run deploy"
echo ""
echo "4. After deployment, test with:"
echo "--------------------------------"
echo "  curl -X POST https://your-worker.workers.dev/mcp/chatgpt/sse/$USER_ID"
echo ""