# Jean Memory Health Check - Deployment Integration Guide

## Overview

This comprehensive health check system prevents production issues by validating all critical Jean Memory components before and after deployment.

## ✅ What We've Built

### 🔧 Health Check Categories
- **Database Layer**: PostgreSQL, Qdrant, Neo4j connectivity
- **External Services**: OpenAI, Gemini, Supabase APIs
- **MCP Tools**: jean_memory tool (the heart of the system)
- **System Components**: Authentication, background tasks
- **API Endpoints**: Core functionality validation

### 📋 Components Created
1. **CLI Health Check Script** (`health_check.py`) - Pre-deployment validation
2. **Health API Endpoints** (`health_endpoint.py`) - Post-deployment monitoring
3. **Modular Check System** (`checks/`) - Organized, maintainable health checks
4. **Convenience Scripts** (`run_health_check.sh`) - Easy-to-use commands

## 🚀 Quick Integration

### 1. Pre-Deployment Checks
Add to your deployment pipeline:

```bash
# Before deploying
cd evals/health_checks
./run_health_check.sh pre-deploy
```

**This will block deployment if critical issues are found!**

### 2. Post-Deployment Monitoring
Add to your FastAPI application (`openmemory/api/main.py`):

```python
# Add this import
from evals.health_checks.health_endpoint import health_router

# Add this route
app.include_router(health_router, prefix="/health")
```

Then access:
- `GET /health` - Overall system health
- `GET /health/detailed` - Comprehensive diagnostics
- `GET /health/quick` - Load balancer health check

### 3. Development Workflow
```bash
# Before starting work
./run_health_check.sh quick

# Before committing
./run_health_check.sh full

# Before deploying
./run_health_check.sh pre-deploy
```

## 🎯 Critical Checks That Prevent Issues

### The "Claude Tools Not Loading" Issue
✅ **MCP Tools Check** validates:
- jean_memory tool imports correctly
- Smart orchestrator initializes
- Context system works
- Tool execution succeeds

### Database Connection Failures
✅ **Database Layer Check** validates:
- PostgreSQL connection and schema
- Qdrant vector database connectivity
- Neo4j graph database access

### AI Service Outages
✅ **External Services Check** validates:
- OpenAI API key and embedding generation
- Gemini API key and text generation
- Supabase authentication service

### Authentication Issues
✅ **System Components Check** validates:
- JWT token validation
- API key verification system
- User database accessibility

## 📊 Exit Codes & CI/CD Integration

### Exit Codes
- `0` - ✅ All checks passed (safe to deploy)
- `1` - ⚠️ Non-critical warnings
- `2` - ❌ Critical issues (block deployment)
- `3+` - System errors

### GitHub Actions Integration
```yaml
name: Health Check
on: [push, pull_request]
jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r openmemory/api/requirements.txt
      - name: Run health checks
        run: |
          cd evals/health_checks
          python health_check.py --level=critical --no-env
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          # ... other secrets
```

### Render.com Integration
Add to your `render.yaml`:
```yaml
services:
  - type: web
    name: jean-memory-api
    preDeployCommand: |
      cd evals/health_checks && python health_check.py --level=critical
    # ... rest of config
```

## 🔍 Monitoring & Alerting

### Production Monitoring
Set up alerts for:
```bash
# Health endpoint returns error
curl -f https://your-domain.com/health || alert

# Detailed health check
curl https://your-domain.com/health/detailed | jq '.status' | grep -v "healthy" && alert
```

### Log Monitoring
Health checks log with structured data:
- `INFO`: Successful checks
- `WARNING`: Non-critical issues  
- `ERROR`: Critical failures

## 🛠 Customization & Extension

### Adding New Health Checks
1. Create new check class in `checks/`
2. Inherit from `HealthCheck`
3. Implement `run_checks()` method
4. Add to `health_check.py` and `health_endpoint.py`

### Environment-Specific Checks
```python
# In your health check
if os.getenv('ENVIRONMENT') == 'production':
    # Production-specific checks
```

### Custom Timeouts
```python
# For long-running checks
result.add_check("Custom Check", success, "Details", timeout=60)
```

## 📈 Performance Impact

### Pre-Deployment (Critical Level)
- **Runtime**: < 30 seconds
- **Scope**: Essential components only
- **Impact**: Blocks bad deployments

### Post-Deployment (Comprehensive Level)  
- **Runtime**: < 2 minutes
- **Scope**: Full system verification
- **Impact**: Ongoing monitoring

### Quick Health Check
- **Runtime**: < 5 seconds
- **Scope**: Basic connectivity
- **Impact**: Load balancer friendly

## 🚨 Troubleshooting Common Issues

### "Import failed" Errors
```bash
# Ensure correct Python path
cd evals/health_checks
python health_check.py
```

### Database Connection Failures
```bash
# Check environment variables
echo $DATABASE_URL
echo $QDRANT_HOST
echo $NEO4J_URI
```

### MCP Tools Failures (CRITICAL!)
```bash
# This is the heart of the system
cd openmemory/api
python -c "from app.tools.orchestration import jean_memory; print('OK')"
```

## 🎉 Benefits

### Before This System
- 😰 Deploy and hope everything works
- 🐛 Issues discovered by users
- 🔥 Emergency fixes and rollbacks
- ❓ No visibility into system health

### After This System
- ✅ Deploy with confidence
- 🛡️ Issues caught before production
- 📊 Continuous health monitoring
- 🚀 Faster development cycles

## 📞 Next Steps

1. **Integrate into CI/CD** - Add health checks to deployment pipeline
2. **Add Health Endpoint** - Enable post-deployment monitoring
3. **Set Up Alerts** - Monitor health endpoints in production  
4. **Train Team** - Use convenience scripts in daily workflow
5. **Extend Checks** - Add application-specific health validations

The health check system is designed to be your safety net - catching issues before they impact users and giving you confidence in your deployments! 🎯