# Jean Memory Development Server Setup Guide

**Version**: 1.0  
**Date**: January 2025  
**Purpose**: Complete guide for setting up a cloud-based development environment that mirrors production

## Executive Summary

This document outlines the comprehensive setup for creating a true development environment that mirrors your production Jean Memory infrastructure on Render. The development server will be connected to the `dev` branch instead of `main`, allowing for safe testing of all features including MCP, Supabase auth, Neo4j, and Qdrant integration before merging to production.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Migration Strategy](#database-migration-strategy)
3. [Service Configuration](#service-configuration)
4. [Environment Variables](#environment-variables)
5. [Deployment Process](#deployment-process)
6. [Testing Strategy](#testing-strategy)
7. [Cost Analysis](#cost-analysis)
8. [Maintenance & Monitoring](#maintenance--monitoring)

---

## Architecture Overview

### Current Production Architecture

```
Production (main branch):
├── jean-memory-ui-virginia (Frontend)
├── jean-memory-api-virginia (Backend API)
├── jean-memory-api (Legacy Backend - Oregon)
└── narrative-backfill-weekly (Cron Job)

Connected to:
├── PostgreSQL (Supabase)
├── Qdrant Cloud (test_cluster)
├── Neo4j Aura (Instance01)
└── External APIs (OpenAI, Gemini, Stripe, Twilio, etc.)
```

### Proposed Development Architecture

```
Development (dev branch):
├── jean-memory-ui-dev (Frontend)
├── jean-memory-api-dev (Backend API)
└── narrative-backfill-dev (Cron Job)

Connected to:
├── PostgreSQL Dev (Supabase - New Project)
├── Qdrant Cloud (dev_cluster - New Cluster)
├── Neo4j Aura (dev_instance - New Instance)
└── Same External APIs (with dev-specific keys where needed)
```

---

## Database Migration Strategy

### 1. PostgreSQL (Supabase)

**Option A: New Supabase Project (Recommended)**
- Create new Supabase project: `jean-memory-dev`
- Copy production database schema using `pg_dump`
- Optionally copy subset of production data for testing

**Steps:**
1. Create new Supabase project
2. Export production schema: `pg_dump --schema-only`
3. Import schema to dev database
4. Run Alembic migrations to ensure compatibility
5. Optionally import sanitized user data

**Option B: Separate Database in Same Project**
- Use same Supabase project with different database name
- Less isolation but simpler setup

### 2. Qdrant Vector Database

**Create New Development Cluster:**
- Cluster Name: `dev_cluster`
- Same specs as production (1 NODE, 8GiB disk, 2GiB RAM)
- Region: AWS us-east-1 (same as production)
- New API key for isolation

**Data Migration:**
- Export existing collections from production cluster
- Import into dev cluster (optional - can start fresh)
- Collections will be recreated as users interact with dev environment

### 3. Neo4j Graph Database

**Create New Development Instance:**
- Instance Name: `jean-memory-dev`
- Type: AuraDB Free (same as production)
- New connection URI and credentials

**Data Migration:**
- Export production graph using Cypher queries
- Import into dev instance (optional)
- Graphiti will rebuild graph structure as memories are processed

---

## Service Configuration

### Development Services

#### 1. jean-memory-api-dev

```yaml
- type: web
  name: jean-memory-api-dev
  runtime: python
  repo: https://github.com/jonathan-politzki/your-memory
  branch: dev  # KEY CHANGE: Deploy from dev branch
  plan: starter
  region: virginia
  rootDir: openmemory/api
  buildCommand: pip install -r requirements.txt
  startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
  preDeployCommand: alembic upgrade head
  healthCheckPath: /health
  autoDeployTrigger: commit
```

#### 2. jean-memory-ui-dev

```yaml
- type: web
  name: jean-memory-ui-dev
  runtime: node
  repo: https://github.com/jonathan-politzki/your-memory
  branch: dev  # KEY CHANGE: Deploy from dev branch
  plan: starter
  region: virginia
  rootDir: openmemory/ui
  buildCommand: pnpm install && pnpm build
  startCommand: pnpm start
  autoDeployTrigger: commit
```

#### 3. narrative-backfill-dev

```yaml
- type: cron
  name: narrative-backfill-dev
  runtime: python
  repo: https://github.com/jonathan-politzki/your-memory
  branch: dev  # KEY CHANGE: Deploy from dev branch
  plan: starter
  region: virginia
  rootDir: .
  buildCommand: pip install -r openmemory/api/requirements.txt && pip install psycopg2-binary python-dotenv
  startCommand: python scripts/utils/standalone_backfill.py
  schedule: "0 3 * * 0"  # Sunday at 3 AM UTC (1 hour after prod)
```

---

## Environment Variables

### Backend API Development Variables

**Database Configuration:**
```yaml
- key: DATABASE_URL
  value: "postgresql://[dev-supabase-connection-string]"
- key: SUPABASE_URL
  value: "https://[dev-project-id].supabase.co"
- key: SUPABASE_SERVICE_KEY
  value: "[dev-service-key]"
- key: SUPABASE_ANON_KEY
  value: "[dev-anon-key]"
```

**Vector & Graph Databases:**
```yaml
- key: QDRANT_HOST
  value: "https://[dev-cluster-id].us-east-1-0.aws.cloud.qdrant.io"
- key: QDRANT_API_KEY
  value: "[dev-cluster-api-key]"
- key: NEO4J_URI
  value: "neo4j+s://[dev-instance-id].databases.neo4j.io"
- key: NEO4J_USER
  value: "neo4j"
- key: NEO4J_PASSWORD
  value: "[dev-instance-password]"
```

**Environment Identification:**
```yaml
- key: ENVIRONMENT
  value: "development"  # Changed from "production"
- key: LOG_level
  value: "DEBUG"  # More verbose logging for development
```

**External APIs (Same as Production):**
- OpenAI API Key (same)
- Gemini API Key (same)
- Stripe Keys (use test keys)
- Twilio Keys (use test account or same)
- PostHog (same or separate project)

### Frontend Development Variables

```yaml
- key: NEXT_PUBLIC_API_URL
  value: "https://jean-memory-api-dev.onrender.com"
- key: ENVIRONMENT
  value: "development"
- key: NODE_ENV
  value: "development"
- key: NEXT_PUBLIC_SUPABASE_URL
  value: "https://[dev-project-id].supabase.co"
- key: NEXT_PUBLIC_SUPABASE_ANON_KEY
  value: "[dev-anon-key]"
```

---

## Deployment Process

### Phase 1: Database Setup

1. **Create Supabase Development Project**
   ```bash
   # Install Supabase CLI
   npm install -g supabase
   
   # Create new project via dashboard or CLI
   supabase projects create jean-memory-dev
   ```

2. **Create Qdrant Development Cluster**
   - Log into Qdrant Cloud dashboard
   - Create new cluster: `dev_cluster`
   - Same configuration as production
   - Note new API key and endpoint

3. **Create Neo4j Development Instance**
   - Log into Neo4j Aura
   - Create new AuraDB Free instance
   - Name: `jean-memory-dev`
   - Note connection details

### Phase 2: Data Migration (Optional)

1. **PostgreSQL Schema Migration**
   ```bash
   # Export production schema
   pg_dump --schema-only $PROD_DATABASE_URL > schema.sql
   
   # Import to development
   psql $DEV_DATABASE_URL < schema.sql
   
   # Run Alembic to ensure current state
   alembic upgrade head
   ```

2. **Qdrant Collections (Optional)**
   ```python
   # Export from production cluster
   from qdrant_client import QdrantClient
   
   prod_client = QdrantClient(url=PROD_QDRANT_HOST, api_key=PROD_QDRANT_KEY)
   dev_client = QdrantClient(url=DEV_QDRANT_HOST, api_key=DEV_QDRANT_KEY)
   
   # Copy collections (implement as needed)
   ```

3. **Neo4j Graph (Optional)**
   ```cypher
   // Export from production
   CALL apoc.export.cypher.all("graph-export.cypher", {})
   
   // Import to development (run exported script)
   ```

### Phase 3: Service Deployment

1. **Create Development Render Configuration**
   - Copy `render.yaml` to `render-dev.yaml`
   - Update service names and branch references
   - Update environment variables

2. **Deploy Services**
   - Create services manually in Render dashboard
   - Or use Render Blueprint with `render-dev.yaml`
   - Verify deployments and health checks

### Phase 4: Testing & Verification

1. **API Health Check**
   ```bash
   curl https://jean-memory-api-dev.onrender.com/health
   ```

2. **Database Connectivity**
   - Test PostgreSQL connection
   - Test Qdrant vector operations
   - Test Neo4j graph queries

3. **Frontend Integration**
   - Test authentication flow
   - Test memory creation/retrieval
   - Test MCP functionality

---

## Testing Strategy

### 1. Development Workflow

```
Local Development → Dev Branch → Development Server → Main Branch → Production
```

1. Develop features locally
2. Push to `dev` branch
3. Automatic deployment to development server
4. Test all functionality in cloud environment
5. Merge `dev` to `main` when ready
6. Automatic deployment to production

### 2. Testing Checklist

**Authentication & Security:**
- [ ] Supabase authentication works
- [ ] API key authentication works
- [ ] User isolation maintains

**Core Functionality:**
- [ ] Memory creation and retrieval
- [ ] Vector search via Qdrant
- [ ] Graph queries via Neo4j
- [ ] MCP protocol integration
- [ ] Background job processing

**Integrations:**
- [ ] SMS via Twilio
- [ ] Email via Resend
- [ ] Stripe webhooks (test mode)
- [ ] External integrations (Twitter, Substack)

**AI Features:**
- [ ] OpenAI embeddings
- [ ] Gemini analysis
- [ ] Smart triage system
- [ ] Context orchestration

### 3. Load Testing

- Use development server for performance testing
- Test with realistic data volumes
- Verify scalability assumptions

---

## Cost Analysis

### Monthly Cost Estimate

**Render Services:**
- jean-memory-api-dev: $7/month (Starter plan)
- jean-memory-ui-dev: $7/month (Starter plan)
- narrative-backfill-dev: $7/month (Starter plan)
- **Subtotal: $21/month**

**Database Services:**
- Supabase Dev Project: $0 (Free tier)
- Qdrant Dev Cluster: ~$20-30/month (1 node, 2GB RAM)
- Neo4j Dev Instance: $0 (AuraDB Free)
- **Subtotal: $20-30/month**

**Total Monthly Cost: $41-51/month**

**Additional Considerations:**
- Same API costs (OpenAI, Gemini) for development usage
- Stripe test mode (no charges)
- Twilio dev/test usage

---

## Maintenance & Monitoring

### 1. Monitoring Setup

**Health Checks:**
- Render built-in health monitoring
- Custom health endpoints
- Database connection monitoring

**Logging:**
- Set LOG_LEVEL=DEBUG for development
- Monitor application logs via Render dashboard
- Set up alerts for critical failures

### 2. Backup Strategy

**Database Backups:**
- Supabase automatic backups (dev project)
- Manual exports before major changes
- Point-in-time recovery available

**Code Backups:**
- Git repository serves as primary backup
- Regular branch synchronization

### 3. Update Process

1. **Weekly Maintenance:**
   - Sync dev branch with main
   - Update dependencies
   - Review and clean test data

2. **Monthly Review:**
   - Cost analysis
   - Performance metrics
   - Security updates

---

## Implementation Timeline

### Week 1: Infrastructure Setup
- Day 1-2: Create database instances
- Day 3-4: Configure Render services
- Day 5: Initial deployment and testing

### Week 2: Data Migration & Testing
- Day 1-2: Migrate database schemas
- Day 3-4: Comprehensive testing
- Day 5: Documentation and team training

### Week 3: Integration & Optimization
- Day 1-2: Integration testing
- Day 3-4: Performance optimization
- Day 5: Final validation

---

## Risk Mitigation

### 1. Data Safety
- Development databases are isolated from production
- Regular backups before major changes
- No PII in development environment (where possible)

### 2. Cost Control
- Monitor usage via Render dashboard
- Set up billing alerts
- Use free tiers where available

### 3. Security
- Separate API keys for development
- Test mode for payment processing
- Limited access to development environment

---

## Conclusion

This development server setup provides a true cloud-based development environment that mirrors production without the complexity of local development. The key benefits include:

1. **True Parity**: Identical architecture to production
2. **Safe Testing**: Isolated environment for experimental changes
3. **Team Collaboration**: Shared development environment
4. **CI/CD Ready**: Automatic deployments from dev branch
5. **Cost Effective**: Reasonable monthly cost for high-fidelity testing

The setup ensures that all features including MCP, authentication, and database integrations work exactly as they would in production, eliminating the common "works on my machine" problem.

---

## Next Steps

1. Create database instances (Supabase, Qdrant, Neo4j)
2. Update GitHub repository with dev branch protection
3. Create Render services with development configuration
4. Migrate essential data for testing
5. Establish development workflow and team processes

This development server will provide the confidence needed to deploy changes to production while maintaining the stability and reliability your users expect.