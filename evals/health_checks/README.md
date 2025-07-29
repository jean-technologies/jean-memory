# Jean Memory Health Check System

## Overview

This health check system ensures all critical components of Jean Memory are functioning properly. It's designed to catch regressions and failures early, preventing production issues.

## Architecture

### Pre-Deployment Health Checks
- **Purpose**: Fast, essential checks that must pass before deployment
- **Location**: `health_check.py` - CLI script  
- **Runtime**: < 30 seconds
- **Scope**: Critical path components only

### Post-Deployment Monitoring  
- **Purpose**: Comprehensive health monitoring after deployment
- **Location**: `/health` API endpoint
- **Runtime**: < 2 minutes
- **Scope**: Full system verification

## Health Check Categories

### 1. Database Layer
- **PostgreSQL**: Connection, basic queries, schema validation
- **Qdrant**: Vector database connectivity, collection existence
- **Neo4j**: Graph database connectivity, basic queries

### 2. External AI Services
- **OpenAI**: API key validation, embedding generation test
- **Gemini**: API key validation, simple generation test

### 3. Authentication Systems
- **Supabase**: JWT validation, user creation test
- **API Keys**: Key validation, rate limiting checks

### 4. External Integrations
- **Stripe**: API connectivity (if configured)
- **Twilio**: SMS service connectivity (if configured)
- **PostHog**: Analytics connectivity (if configured)

### 5. Core Application Services
- **mem0**: Library initialization, basic operations
- **Graphiti**: Neo4j graph management layer
- **MCP Server**: Protocol implementation

### 6. API Endpoints
- **Core MCP**: `/mcp` endpoint functionality
- **Memory Operations**: CRUD operations
- **Authentication**: Token validation

### 7. MCP Tools
- **jean_memory**: Core orchestration tool
- **Memory Tools**: add_memories, search_memory, list_memories
- **Document Tools**: Processing capabilities

### 8. Background Services
- **Document Processing**: Background job execution
- **Integration Sync**: Background sync capabilities

## Usage

### Pre-Deployment Check
```bash
cd evals/health_checks
python health_check.py --level=critical
```

### Post-Deployment Monitoring
```bash
# Via API endpoint
curl https://your-domain.com/health

# Or via script
python health_check.py --level=comprehensive --remote
```

## Configuration

Health checks are configured via environment variables and can be customized for different deployment environments (staging, production).

## Exit Codes

- **0**: All checks passed
- **1**: Non-critical issues found
- **2**: Critical issues found (deployment should be blocked)