# Production Testing Deployment Guide

This guide explains how to safely deploy and test the new unified memory system in production using environment variables.

## 🛡️ Security Approach

- **No sensitive data in code**: All test user IDs and configuration are set via environment variables
- **Explicit enablement**: Test routing only works when explicitly enabled
- **Single user isolation**: Only affects the designated test user
- **Easy rollback**: Simply disable environment variables to revert

## 📋 Environment Variables to Set in Render

### Required Variables

Set these in your Render dashboard under "Environment":

```bash
# Enable test user routing (MUST be set to "true" to activate)
ENABLE_UNIFIED_MEMORY_TEST_USER=true

# Test user ID (set to your actual test user ID from Supabase)
UNIFIED_MEMORY_TEST_USER_ID=5a4cc4ed-d8f1-4128-af09-18ec96963ecc
```

### Test Infrastructure Variables

If using hosted test infrastructure (recommended for production testing):

```bash
# Test PostgreSQL (for pgvector)
TEST_PG_HOST=your-test-postgres-host.com
TEST_PG_PORT=5432
TEST_PG_USER=postgres
TEST_PG_PASSWORD=your-secure-test-password
TEST_PG_DBNAME=mem0_unified_test

# Test Neo4j (for graph relationships)
TEST_NEO4J_URI=bolt://your-test-neo4j-host.com:7687
TEST_NEO4J_USER=neo4j
TEST_NEO4J_PASSWORD=your-secure-neo4j-password
```

### Optional Variables (for future use)

```bash
# Gradual rollout percentage (0-100)
UNIFIED_MEMORY_ROLLOUT_PERCENTAGE=0

# Additional test users (comma-separated)
UNIFIED_MEMORY_USER_ALLOWLIST=user-id-1,user-id-2

# Force all users to new system (development only)
FORCE_UNIFIED_MEMORY=false
```

## 🚀 Deployment Steps

### Step 1: Set Environment Variables

1. Go to your Render dashboard
2. Navigate to your service settings
3. Go to "Environment" tab
4. Add the required environment variables:
   - `ENABLE_UNIFIED_MEMORY_TEST_USER=true`
   - `UNIFIED_MEMORY_TEST_USER_ID=5a4cc4ed-d8f1-4128-af09-18ec96963ecc`

### Step 2: Deploy Code

1. Commit and push your changes to the main branch
2. Render will automatically deploy the new code
3. The system will now route the test user to the new pipeline

### Step 3: Test in Production

1. Log in to https://jeanmemory.com with test credentials:
   - Email: `rohankatakam@gmail.com`
   - Password: `Secure_test_password_2024`

2. Verify the routing is working by checking logs for:
   ```
   🧪 Routing test user to NEW unified memory system (production test)
   ```

3. Test functionality:
   - Add new memories
   - Search existing memories
   - Verify performance

### Step 4: Monitor

1. Check application logs for any errors
2. Monitor database connections to test infrastructure
3. Verify other users are unaffected (should see no routing logs for them)

## 🔍 Verification

### Check Routing Logic

Test the routing with different scenarios:

```bash
# Test user - should route to NEW system
User ID: 5a4cc4ed-d8f1-4128-af09-18ec96963ecc
Expected: Routes to unified memory system

# Any other user - should route to OLD system  
User ID: any-other-user-id
Expected: Routes to existing Qdrant system
```

### Check Environment Variables

Verify variables are set correctly:

```bash
# In your application logs, you should see:
✅ ENABLE_UNIFIED_MEMORY_TEST_USER: true
✅ UNIFIED_MEMORY_TEST_USER_ID: [configured]
```

## 🚨 Safety Features

### Automatic Safeguards

1. **Double verification**: Both `ENABLE_UNIFIED_MEMORY_TEST_USER=true` AND `UNIFIED_MEMORY_TEST_USER_ID` must be set
2. **Explicit user matching**: Only the exact user ID specified will be routed
3. **Default fallback**: All other users automatically use the old system
4. **No code exposure**: No sensitive data is committed to the repository

### Emergency Rollback

To immediately disable test routing:

1. In Render dashboard, set: `ENABLE_UNIFIED_MEMORY_TEST_USER=false`
2. Or delete the environment variable entirely
3. Redeploy (or wait for automatic deployment)

## 📊 Testing Checklist

### Before Deployment
- [ ] Environment variables configured in Render
- [ ] Test infrastructure is running and accessible
- [ ] Code changes reviewed and tested locally

### After Deployment
- [ ] Test user routes to new system (check logs)
- [ ] Other users route to old system (check logs)
- [ ] Test user can add memories
- [ ] Test user can search memories
- [ ] No errors in application logs
- [ ] Database connections are working

### Ongoing Monitoring
- [ ] Regular checks of test user functionality
- [ ] Monitor for any performance issues
- [ ] Verify no impact on other users
- [ ] Check test infrastructure health

## 🎯 Success Criteria

The production test is successful when:

1. ✅ Test user successfully uses new unified memory system
2. ✅ All other users continue using existing system normally
3. ✅ No performance degradation for existing users
4. ✅ New system performs as expected under production load
5. ✅ No data leakage or cross-user contamination

## 📞 Troubleshooting

### Test User Not Routing to New System

Check:
1. `ENABLE_UNIFIED_MEMORY_TEST_USER` is set to `"true"`
2. `UNIFIED_MEMORY_TEST_USER_ID` matches exactly
3. User is logging in with correct credentials
4. Check application logs for routing messages

### Other Users Affected

This should not happen, but if it does:
1. Immediately set `ENABLE_UNIFIED_MEMORY_TEST_USER=false`
2. Check environment variable configuration
3. Review logs to identify the issue

### Infrastructure Connection Issues

Check:
1. Test database credentials are correct
2. Network connectivity to test infrastructure
3. Database/Neo4j services are running
4. Firewall/security group settings

## 🔄 Future Rollout

Once testing is successful, you can gradually roll out to more users:

1. **Targeted rollout**: Add user IDs to `UNIFIED_MEMORY_USER_ALLOWLIST`
2. **Percentage rollout**: Set `UNIFIED_MEMORY_ROLLOUT_PERCENTAGE` to a small value (e.g., 5)
3. **Full rollout**: Gradually increase percentage or switch all users

This approach ensures a safe, controlled migration to the new unified memory system. 