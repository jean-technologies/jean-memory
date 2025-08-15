# 🚀 Jean Memory SDK Unified Deployment System

This deployment system ensures all 3 SDKs (React, Node.js, Python) maintain consistent versioning and can be deployed together or separately.

## ✨ Features

- **Unified Versioning**: All SDKs use the same version number
- **Atomic Deployments**: Build and publish all SDKs together
- **Dry Run Mode**: Test deployments without making changes
- **Selective Deployment**: Deploy only specific SDKs
- **Automatic Version Bumping**: Semantic versioning (major.minor.patch)
- **Error Handling**: Fails fast if any SDK build/publish fails

## 🎯 Quick Start

### Deploy All SDKs (Patch Version Bump)
```bash
cd /path/to/jean-memory
python3 scripts/deploy_all_sdks.py
```

### Deploy with Specific Version
```bash
python3 scripts/deploy_all_sdks.py --version 1.3.0
```

### Deploy with Version Bump Type
```bash
# Patch: 1.2.4 → 1.2.5
python3 scripts/deploy_all_sdks.py --bump patch

# Minor: 1.2.4 → 1.3.0  
python3 scripts/deploy_all_sdks.py --bump minor

# Major: 1.2.4 → 2.0.0
python3 scripts/deploy_all_sdks.py --bump major
```

### Dry Run (Test Without Publishing)
```bash
python3 scripts/deploy_all_sdks.py --dry-run
```

### Deploy Only Specific SDKs
```bash
# Deploy only React and Node.js
python3 scripts/deploy_all_sdks.py --sdks react node

# Deploy only Python
python3 scripts/deploy_all_sdks.py --sdks python
```

### Skip Build Step (If Already Built)
```bash
python3 scripts/deploy_all_sdks.py --skip-build
```

## 📦 What It Does

1. **Version Analysis**: Checks current versions across all SDKs
2. **Version Update**: Updates package.json, setup.py, and __init__.py files
3. **Build Process**: Runs TypeScript compilation and Python builds
4. **Publishing**: Publishes to npm (React/Node.js) and PyPI (Python)
5. **Verification**: Confirms successful deployment

## 🔧 Configuration

The script automatically detects SDK locations:
- React SDK: `sdk/react/`
- Node.js SDK: `sdk/node/`  
- Python SDK: `sdk/python/`

## 📋 Prerequisites

### For All SDKs:
- Valid API credentials for npm and PyPI
- Build tools installed (Node.js, Python, TypeScript)

### For npm Publishing:
```bash
npm login
```

### For PyPI Publishing:
```bash
pip install twine
python3 -m twine configure
```

## 🛡️ Safety Features

- **Dry Run Mode**: Always test first
- **Version Validation**: Ensures semantic versioning
- **Build Verification**: Won't publish if builds fail
- **Atomic Operations**: All SDKs succeed or fail together
- **Rollback Ready**: Git integration for easy rollbacks

## 📊 Example Output

```
[00:04:23] 🚀 🎯 JEAN MEMORY SDK UNIFIED DEPLOYMENT

[00:04:23] ℹ️  Current versions:
  📦 react: 1.2.1
  📦 node: 1.2.4
  📦 python: 1.2.4

[00:04:23] 🚀 Target version: 1.2.5

[00:04:23] 🚀 📝 Updating versions...
[00:04:23] ✅ Updated react version to 1.2.5
[00:04:23] ✅ Updated node version to 1.2.5
[00:04:23] ✅ Updated python version to 1.2.5

[00:04:23] 🚀 🔨 Building SDKs...
[00:04:23] ✅ Built react SDK successfully
[00:04:24] ✅ Built node SDK successfully
[00:04:25] ✅ Built python SDK successfully

[00:04:25] 🚀 📤 Publishing SDKs...
[00:04:25] ✅ Published react SDK successfully
[00:04:25] ✅ Published node SDK successfully
[00:04:25] ✅ Published python SDK successfully

[00:04:25] ✅ 🎉 All SDKs deployed successfully!
[00:04:25] ℹ️  All SDKs are now at version 1.2.5
```

## 🚨 Common Issues & Solutions

### Build Failures
```bash
# Check individual SDK builds
cd sdk/react && npm run build
cd sdk/node && npm run build  
cd sdk/python && python3 setup.py build
```

### Publishing Failures
```bash
# Check authentication
npm whoami
python3 -m twine check dist/*
```

### Version Conflicts
```bash
# Start fresh with dry run
python3 scripts/deploy_all_sdks.py --dry-run --version 1.3.0
```

## 🎯 Best Practices

1. **Always dry run first**: `--dry-run` to test
2. **Use semantic versioning**: Meaningful version bumps
3. **Test builds locally**: Verify functionality before publishing
4. **Coordinate team**: Ensure no conflicts with other developers
5. **Document releases**: Update changelogs and release notes

## 🔄 Integration with CI/CD

```yaml
# GitHub Actions example
- name: Deploy SDKs
  run: |
    python3 scripts/deploy_all_sdks.py --bump patch
  env:
    NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
    PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
```

## 📈 Monitoring

After deployment, verify releases:
- **npm**: https://www.npmjs.com/package/@jeanmemory/react
- **npm**: https://www.npmjs.com/package/@jeanmemory/node
- **PyPI**: https://pypi.org/project/jeanmemory/

---

**Built with ❤️ by the Jean Memory team**