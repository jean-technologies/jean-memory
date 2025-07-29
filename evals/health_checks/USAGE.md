# Jean Memory Health Check Usage Guide

## Quick Start

### Pre-Deployment Check (Recommended)
```bash
cd evals/health_checks
python health_check.py --level=critical
```

This runs essential checks that must pass before deploying to production.

### Comprehensive System Check
```bash
python health_check.py --level=comprehensive --verbose
```

This runs all available health checks with detailed output.

### Post-Deployment Monitoring

#### Option 1: Add Health Endpoint to API
Add this to your `openmemory/api/main.py`:

```python
from evals.health_checks.health_endpoint import health_router
app.include_router(health_router, prefix="/health")
```

Then access:
- `GET /health` - Basic health status
- `GET /health/detailed` - Detailed health information  
- `GET /health/quick` - Minimal check for load balancers

#### Option 2: Standalone Health Check
```bash
python health_check.py --level=comprehensive --remote
```

## Health Check Categories

### Critical (Always Run)
- **Database Layer**: PostgreSQL, Qdrant, Neo4j connectivity
- **External Services**: OpenAI, Gemini, Supabase APIs
- **MCP Tools**: jean_memory tool and memory operations
- **System Components**: Authentication, background tasks

### Comprehensive (Full Verification)
- All critical checks
- Document processing tools
- Optional integrations (Stripe, Twilio, PostHog)
- API endpoint validation

## Exit Codes

- `0` - All checks passed ✅
- `1` - Non-critical warnings found ⚠️
- `2` - Critical issues found (block deployment) ❌
- `3` - User interrupted
- `4` - System error during checks
- `5` - Failed to initialize health check system

## Environment Setup

The health check system will automatically try to load environment variables from:
1. `openmemory/api/.env`
2. `openmemory/.env`
3. `.env` (current directory)
4. System environment variables

To skip .env loading:
```bash
python health_check.py --no-env
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Health Checks
  run: |
    cd evals/health_checks
    python health_check.py --level=critical --no-env
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    # ... other env vars
```

### Pre-commit Hook
Add to `.git/hooks/pre-push`:
```bash
#!/bin/bash
cd evals/health_checks
python health_check.py --level=critical
if [ $? -ne 0 ]; then
    echo "❌ Health checks failed. Push blocked."
    exit 1
fi
```

## Troubleshooting

### Common Issues

#### "Import failed" errors
- Ensure you're running from the correct directory
- Check that all dependencies are installed: `pip install -r requirements.txt`

#### Database connection failures
- Verify `DATABASE_URL`, `QDRANT_HOST`, `NEO4J_URI` environment variables
- Ensure databases are running and accessible
- Run database migrations: `alembic upgrade head`

#### MCP tools failures
- This is critical! The jean_memory tool is the heart of the system
- Check mem0 library configuration
- Verify all AI service API keys are valid

#### External service timeouts
- Check internet connectivity
- Verify API keys and quotas
- Some services may be temporarily unavailable (non-critical)

### Verbose Output
Add `--verbose` to see detailed information about all checks:
```bash
python health_check.py --level=comprehensive --verbose
```

### Custom Environment File
```bash
python health_check.py --level=critical
# Will automatically find and load .env files
```

## Monitoring in Production

### Health Endpoint Monitoring
Set up monitoring tools to check:
- `GET /health/quick` every 30 seconds (liveness)
- `GET /health` every 5 minutes (health status)
- `GET /health/detailed` every hour (comprehensive)

### Alerts
Set up alerts for:
- Health endpoint returning 5xx status codes
- Health status changing from "healthy" to "degraded" or "unhealthy"
- Critical health checks failing

### Logging
Health check results are logged with appropriate levels:
- INFO: Successful checks
- WARNING: Non-critical issues
- ERROR: Critical failures

## Development Workflow

### Before Starting Development
```bash
python health_check.py --level=critical
```

### Before Committing Changes
```bash
python health_check.py --level=comprehensive
```

### Before Deploying
```bash
python health_check.py --level=critical
# Must return exit code 0
```

### After Deployment
```bash
curl https://your-domain.com/health
# Should return {"status": "healthy"}
```