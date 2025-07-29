#!/bin/bash

# Jean Memory Health Check Runner
# Convenient wrapper script for common health check scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

print_usage() {
    echo "Jean Memory Health Check Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  pre-deploy     Run critical pre-deployment checks"
    echo "  full           Run comprehensive health checks"
    echo "  quick          Run quick health check"
    echo "  remote         Check remote deployment"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 pre-deploy    # Before pushing to production"
    echo "  $0 full          # Full system verification"
    echo "  $0 remote        # Check production deployment"
}

run_pre_deploy() {
    echo -e "${YELLOW}🚀 Running Pre-Deployment Health Checks...${NC}"
    echo ""
    
    if python health_check.py --level=critical; then
        echo ""
        echo -e "${GREEN}✅ Pre-deployment checks PASSED${NC}"
        echo -e "${GREEN}🎉 Safe to deploy!${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Pre-deployment checks FAILED${NC}"
        echo -e "${RED}🛑 DO NOT DEPLOY until issues are resolved${NC}"
        exit 1
    fi
}

run_full() {
    echo -e "${YELLOW}🔍 Running Comprehensive Health Checks...${NC}"
    echo ""
    
    if python health_check.py --level=comprehensive --verbose; then
        echo ""
        echo -e "${GREEN}✅ All health checks PASSED${NC}"
        exit 0
    else
        echo ""
        echo -e "${YELLOW}⚠️  Some health checks failed or have warnings${NC}"
        exit 1
    fi
}

run_quick() {
    echo -e "${YELLOW}⚡ Running Quick Health Check...${NC}"
    echo ""
    
    if python health_check.py --level=critical; then
        echo ""
        echo -e "${GREEN}✅ Quick health check PASSED${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Quick health check FAILED${NC}"
        exit 1
    fi
}

run_remote() {
    echo -e "${YELLOW}🌐 Checking Remote Deployment...${NC}"
    echo ""
    
    if python health_check.py --level=comprehensive --remote; then
        echo ""
        echo -e "${GREEN}✅ Remote deployment is healthy${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}❌ Remote deployment has issues${NC}"
        exit 1
    fi
}

# Main command processing
case "${1:-help}" in
    "pre-deploy"|"predeploy"|"critical")
        run_pre_deploy
        ;;
    "full"|"comprehensive"|"all")
        run_full
        ;;
    "quick"|"fast")
        run_quick
        ;;
    "remote"|"production"|"prod")
        run_remote
        ;;
    "help"|"--help"|"-h"|"")
        print_usage
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        print_usage
        exit 1
        ;;
esac