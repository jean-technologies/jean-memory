# 🚀 Render Environment Setup - Ready to Deploy

## ✅ What to Set on Each Server

### jean-memory-api-dev.onrender.com
```bash
ENVIRONMENT=development
JWT_SECRET_KEY=049727cc7f797a0bb8ac4016c25dcbfda7f7cf9113282c651d8492d00138f06e86ac9d37599ed81dad5cff59f2f98069908066d7a1dea70cef51922a14532ad4
```

### jean-memory-api-virginia.onrender.com  
```bash
ENVIRONMENT=production
JWT_SECRET_KEY=049727cc7f797a0bb8ac4016c25dcbfda7f7cf9113282c651d8492d00138f06e86ac9d37599ed81dad5cff59f2f98069908066d7a1dea70cef51922a14532ad4
```

## 🔧 How URLs Will Work

- **Dev**: `https://jean-memory-api-dev.onrender.com/mcp` (OAuth URL)
- **Production**: `https://jean-memory-api-virginia.onrender.com/mcp` (OAuth URL)

## ⚠️ What NOT to Touch

**Keep all existing environment variables unchanged:**
- DATABASE_URL
- SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY  
- OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
- QDRANT_HOST, QDRANT_API_KEY, QDRANT_URL
- STRIPE_SECRET_KEY, TWILIO_*, POSTHOG_*
- All other existing variables

## 🧪 Validation Results

✅ Development environment detection works
✅ Production environment detection works  
✅ URL auto-detection works correctly
✅ Override capability works if needed
✅ No conflicts with existing variables

## 📋 Deployment Steps

1. **Go to Render Dashboard**
2. **jean-memory-api-dev**: Add `ENVIRONMENT=development` and `JWT_SECRET_KEY`
3. **jean-memory-api-virginia**: Add `ENVIRONMENT=production` and `JWT_SECRET_KEY`  
4. **Deploy both services**
5. **Test OAuth discovery endpoints**

## 🎯 Testing URLs

After deployment, these should work:

- Dev: `https://jean-memory-api-dev.onrender.com/.well-known/oauth-authorization-server`
- Prod: `https://jean-memory-api-virginia.onrender.com/.well-known/oauth-authorization-server`

Both should return proper OAuth discovery metadata with correct URLs.

## 🚨 Rollback Plan

If anything breaks:
1. Remove `ENVIRONMENT` variable (defaults to development)
2. Add `API_BASE_URL` explicitly if needed
3. System will fall back to working state

**Ready to deploy! No code changes needed - just environment variables.**
