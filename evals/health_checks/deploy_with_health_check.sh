#!/bin/bash

# Jean Memory Deployment with Post-Deploy Health Check
# This script can be integrated into your Render.com or other deployment pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
HEALTH_CHECK_URL="${DEPLOY_URL:-http://localhost:8000}"
MAX_WAIT_TIME=300  # 5 minutes max wait
CHECK_INTERVAL=10  # Check every 10 seconds

echo -e "${BLUE}🚀 Jean Memory Deployment with Health Check${NC}"
echo "=================================="
echo "Target URL: $HEALTH_CHECK_URL"
echo "Max wait time: ${MAX_WAIT_TIME}s"
echo ""

# Step 1: Wait for deployment to be ready
echo -e "${YELLOW}⏳ Waiting for deployment to be ready...${NC}"
wait_count=0
while [ $wait_count -lt $MAX_WAIT_TIME ]; do
    if curl -f -s "$HEALTH_CHECK_URL/" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Deployment is responding${NC}"
        break
    fi
    
    echo "   Waiting... (${wait_count}s/${MAX_WAIT_TIME}s)"
    sleep $CHECK_INTERVAL
    wait_count=$((wait_count + CHECK_INTERVAL))
done

if [ $wait_count -ge $MAX_WAIT_TIME ]; then
    echo -e "${RED}❌ Deployment did not become ready within ${MAX_WAIT_TIME}s${NC}"
    exit 1
fi

# Step 2: Run post-deployment health check
echo ""
echo -e "${YELLOW}🏥 Running post-deployment health check...${NC}"

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if python3 "$SCRIPT_DIR/post_deploy_check.py" --url="$HEALTH_CHECK_URL"; then
    echo ""
    echo -e "${GREEN}🎉 Deployment successful and healthy!${NC}"
    echo -e "${GREEN}✨ System is ready for traffic${NC}"
    
    # Optional: Send success notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"✅ Jean Memory deployment successful and healthy!"}' \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}🚨 Deployment health check FAILED${NC}"
    echo -e "${RED}⚠️  System may have issues - investigate immediately${NC}"
    
    # Optional: Send failure notification
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚨 Jean Memory deployment health check FAILED - investigate immediately!"}' \
            "$SLACK_WEBHOOK_URL" > /dev/null 2>&1
    fi
    
    exit 1
fi