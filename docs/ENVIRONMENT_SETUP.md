# Environment Variables Setup - Dev vs Production

## 🚨 Critical Variables for OAuth

### Development Server (jean-memory-api-dev)
```bash
# Environment detection
ENVIRONMENT=development

# OAuth configuration
JWT_SECRET_KEY=049727cc7f797a0bb8ac4016c25dcbfda7f7cf9113282c651d8492d00138f06e86ac9d37599ed81dad5cff59f2f98069908066d7a1dea70cef51922a14532ad4

# API URL (auto-detects to: https://jean-memory-api-dev.onrender.com)
# API_BASE_URL=https://jean-memory-api-dev.onrender.com  # Optional override
```

### Production Server (jean-memory-api-virginia)
```bash
# Environment detection
ENVIRONMENT=production

# OAuth configuration  
JWT_SECRET_KEY=049727cc7f797a0bb8ac4016c25dcbfda7f7cf9113282c651d8492d00138f06e86ac9d37599ed81dad5cff59f2f98069908066d7a1dea70cef51922a14532ad4

# API URL (auto-detects to: https://jean-memory-api-virginia.onrender.com)
# API_BASE_URL=https://jean-memory-api-virginia.onrender.com  # Optional override
```

## 🔧 Existing Variables (Keep These!)

Both servers should already have these core variables:

```bash
# Database
DATABASE_URL=postgresql://...

# Supabase
SUPABASE_URL=https://...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_KEY=...

# AI Services
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GEMINI_API_KEY=...

# Vector Database
QDRANT_HOST=...
QDRANT_API_KEY=...
QDRANT_URL=...

# Other services (if used)
STRIPE_SECRET_KEY=...
TWILIO_ACCOUNT_SID=...
POSTHOG_API_KEY=...
```

## ⚠️ Potential Conflicts Check

Files that might be affected by environment changes:
- ✅ `app/oauth/server.py` - Updated to use config.API_BASE_URL  
- ❌ `app/routers/claude_simple.py` - DELETED (no issue)
- ✅ `app/settings.py` - Added API_BASE_URL auto-detection

## 🧪 Validation Script

Test the environment configuration:
```python
from app.settings import Config
config = Config()
print(f"Environment: {config.ENVIRONMENT}")
print(f"API Base URL: {config.API_BASE_URL}")
print(f"Is Production: {config.IS_PRODUCTION}")
```

## 🚀 Deployment Steps

1. **Set ENVIRONMENT variable** on both servers
2. **Set JWT_SECRET_KEY** on both servers (same value)
3. **Keep all existing variables** unchanged
4. **Deploy** - API_BASE_URL will auto-detect correctly
5. **Test** OAuth discovery endpoints

No other code changes needed - environment detection is automatic!
