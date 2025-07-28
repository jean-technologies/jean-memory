# Render.com Integration for Post-Deploy Health Checks

## Quick Integration

### Option 1: Update your `render.yaml`
```yaml
services:
  - type: web
    name: jean-memory-api-virginia
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    # Remove pre-deploy health checks to speed up deployment
    # preDeployCommand: alembic upgrade head  # Keep DB migrations only
    
    # Add post-deploy command that runs AFTER deployment is live
    postDeployCommand: |
      cd evals/health_checks && 
      python post_deploy_check.py --url=$RENDER_EXTERNAL_URL --quiet
    
    envVars:
      - key: RENDER_EXTERNAL_URL
        sync: false
```

### Option 2: Use the deploy script
Update your `render.yaml`:
```yaml
services:
  - type: web
    name: jean-memory-api-virginia
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    
    # Run our custom deploy script after deployment
    postDeployCommand: |
      DEPLOY_URL=$RENDER_EXTERNAL_URL ./evals/health_checks/deploy_with_health_check.sh
```

## What This Does

### ⚡ Fast Deployment
- No pre-deployment checks blocking the deploy
- Only essential DB migrations run before deployment
- Gets your code live ASAP

### 🏥 Post-Deploy Verification
**After deployment is live, automatically checks:**
- ✅ API is responding
- ✅ MCP endpoint works and jean_memory tool is available
- ✅ Database connectivity 
- ✅ Jean Memory tool executes successfully

### 🚨 Immediate Alerts
- If health checks fail, you get immediate notification
- Can integrate with Slack/Discord webhooks
- Logs are captured in Render dashboard

## Example Output

**Successful deployment:**
```
🏥 Post-Deployment Health Check
🌐 Target: https://your-app.onrender.com
⏰ Started: 14:32:15

✅ API Health: OK
✅ MCP Endpoint: OK  
✅ Database: OK
✅ Jean Memory Tool: OK

🎉 All post-deployment checks PASSED
✨ System is healthy and ready for traffic!
```

**Failed deployment:**
```
🏥 Post-Deployment Health Check
🌐 Target: https://your-app.onrender.com
⏰ Started: 14:32:15

✅ API Health: OK
❌ MCP Endpoint: FAILED
✅ Database: OK
❌ Jean Memory Tool: FAILED

🚨 Some post-deployment checks FAILED
⚠️  System may have issues - investigate immediately
```

## Benefits

### For You
- **Faster deployments** - No waiting for health checks
- **Immediate feedback** - Know within 30 seconds if deployment worked
- **Better reliability** - Catch issues right after deployment

### For Users  
- **Less downtime** - Deployment happens faster
- **Better experience** - Issues caught before users notice

## Advanced Options

### Add Slack Notifications
Set `SLACK_WEBHOOK_URL` environment variable in Render:
```yaml
envVars:
  - key: SLACK_WEBHOOK_URL
    value: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### Custom Health Check URL
If you have a custom domain:
```bash
DEPLOY_URL=https://your-custom-domain.com ./deploy_with_health_check.sh
```

### Skip Post-Deploy Checks (Emergency)
If you need to deploy without health checks:
```yaml
# Temporarily comment out postDeployCommand
# postDeployCommand: |
#   cd evals/health_checks && python post_deploy_check.py --url=$RENDER_EXTERNAL_URL
```

This gives you the best of both worlds - fast deployments with immediate health verification! 🚀