# 🔒 Security Notice: Environment Variables

## **Critical Security Guidelines**

### **Environment File Templates**
All `.env` files in this repository are **TEMPLATES ONLY** with placeholder values:
- `scripts/local-dev/unified-memory/.env.unified-memory` - Contains placeholder API keys
- `env.unified-memory.template` - Template for copying

### **Never Commit Real Credentials**
❌ **DO NOT** commit files containing:
- Real API keys (OpenAI, Gemini, etc.)
- Database passwords or connection strings
- User IDs from production systems
- Any sensitive authentication data

### **Safe Development Workflow**
1. **Copy template files** to create your local versions
2. **Replace placeholders** with your actual credentials
3. **Verify `.gitignore`** excludes your credential files
4. **Use environment variables** in production (Render, Docker, etc.)

### **Production Deployment**
- Set credentials as environment variables in your hosting platform
- Never include credentials in Docker images or config files
- Use secure secret management systems

### **If You Accidentally Commit Secrets**
1. **Immediately rotate** all exposed credentials
2. **Remove from git history** using `git filter-branch` or BFG Repo-Cleaner
3. **Verify** no sensitive data remains in any commits
4. **Update** all systems using the exposed credentials

## **This Repository is Public**
Remember: This is an open-source project. Any committed data is visible to everyone. 