# SDK Publishing & Documentation Fix Plan

## Current State Assessment

### ✅ What We Have
1. **React SDK**: Published to NPM as `jeanmemory-react` v0.1.3 ✅
2. **Python SDK**: Complete code in `sdk/python/` with `setup.py` - NOT published to PyPI
3. **Node.js SDK**: Complete code in `sdk/node/` - NOT published to NPM
4. **Documentation**: Mintlify docs exist but have incorrect hook references

### ❌ Issues to Fix
1. Python SDK not published to PyPI (`pip install jeanmemory` fails)
2. Node.js SDK not published to NPM (`npm install @jeanmemory/node` fails)
3. Documentation uses `useJeanAgent` instead of `useJean`
4. Missing package.json for Node.js SDK publishing

## Phase 1: Publish Missing SDKs

### 1.1 Python SDK Publishing

**Requirements:**
- PyPI account credentials
- Package name `jeanmemory` available on PyPI
- Testing in isolated environment

**Steps:**
```bash
cd sdk/python
python -m pip install --upgrade pip setuptools wheel twine
python setup.py sdist bdist_wheel
twine check dist/*
twine upload dist/*  # Use --repository-url https://test.pypi.org/legacy/ for testing first
```

**Complexity: EASY** - All code exists, just needs publishing

### 1.2 Node.js SDK Publishing

**Requirements:**
- NPM account with access to `@jeanmemory` scope
- Create package.json for the Node.js SDK
- Handle TypeScript compilation

**Current Gap:** Missing package.json in `sdk/node/`

**Steps:**
1. Create `package.json` for Node.js SDK
2. Set up TypeScript build process
3. Publish to NPM as `@jeanmemory/node`

**Complexity: MODERATE** - Needs build setup

### 1.3 React SDK Status
- ✅ Already published as `jeanmemory-react`
- ✅ Version 0.1.3 available on NPM
- ❌ Documentation references wrong hook name

## Phase 2: Fix Documentation

### 2.1 React Hook Name Fix
**Files to update:**
- `docs-mintlify/quickstart.mdx`
- `docs-mintlify/sdk/react.mdx`

**Change:** `useJeanAgent` → `useJean` everywhere

### 2.2 Verify Package Names
**Current docs claim:**
- `pip install jeanmemory` ✅ (will work after publishing)
- `npm install @jeanmemory/node` ✅ (will work after publishing)  
- `npm install jeanmemory-react` ✅ (already works)

## Implementation Plan

### Step 1: Create Node.js SDK package.json
```json
{
  "name": "@jeanmemory/node",
  "version": "0.1.0",
  "description": "Node.js SDK for Jean Memory",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "prepublish": "npm run build"
  },
  "dependencies": {
    "@ai-sdk/openai": "^0.0.66",
    "ai": "^4.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

### Step 2: Add tsconfig.json for Node.js SDK
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "declaration": true,
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["index.ts"]
}
```

### Step 3: Publishing Commands
```bash
# Python SDK
cd sdk/python
pip install twine wheel
python setup.py sdist bdist_wheel
twine upload dist/*

# Node.js SDK  
cd sdk/node
npm install
npm run build
npm publish --access=public

# React SDK (already published, just verify)
cd sdk/react
npm publish  # should be up to date
```

### Step 4: Update Documentation
```bash
# Fix hook name in all Mintlify docs
find docs-mintlify -name "*.mdx" -exec sed -i '' 's/useJeanAgent/useJean/g' {} \;
```

## Registry Requirements

### PyPI (Python)
- Need PyPI account with 2FA
- Package name `jeanmemory` must be available
- Standard Python packaging (we already have this)

### NPM (Node.js)
- Need NPM account with access to `@jeanmemory` scope
- Organization scope allows `@jeanmemory/node` naming
- TypeScript compilation required

### NPM (React - already done)
- ✅ Published as `jeanmemory-react`
- ✅ Available on NPM registry

## Timeline

**Day 1 (Today):**
1. Create Node.js SDK package.json & tsconfig.json
2. Test Node.js SDK build process
3. Fix React hook name in documentation

**Day 2:**
1. Publish Python SDK to PyPI
2. Publish Node.js SDK to NPM
3. Verify all installation commands work

**Total Effort: 1-2 days**

## Success Criteria

After completion:
- ✅ `pip install jeanmemory` works
- ✅ `npm install @jeanmemory/node` works  
- ✅ `npm install jeanmemory-react` works (already ✅)
- ✅ All documentation examples use correct `useJean` hook
- ✅ All quickstart examples work as documented

## Risk Assessment

**Low Risk:**
- Python publishing (standard process)
- Documentation fixes (simple find/replace)

**Medium Risk:**
- Node.js SDK publishing (needs build setup)
- NPM scope permissions (@jeanmemory organization)

**Mitigation:**
- Test on PyPI test instance first
- Use NPM dry-run before actual publishing
- Keep backups of current working React SDK