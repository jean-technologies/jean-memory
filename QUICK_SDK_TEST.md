# Quick SDK Test (5 Minutes)

**Purpose:** Rapid test of all three Jean Memory SDKs

## 🚀 One-Command Tests

### Node.js SDK Test
```bash
mkdir /tmp/test-node && cd /tmp/test-node
npm init -y && npm install @jeanmemory/node
echo "const { JeanMemoryClient } = require('@jeanmemory/node'); console.log('✅ Works:', new JeanMemoryClient({apiKey:'test'}))" > test.js
node test.js
```

### Python SDK Test  
```bash
mkdir /tmp/test-python && cd /tmp/test-python
python3 -m venv venv && source venv/bin/activate
pip install jeanmemory
python3 -c "from jean_memory import JeanMemoryClient; print('✅ Works:', JeanMemoryClient('test'))"
```

### React SDK Test
```bash
npx create-next-app@latest /tmp/test-react --typescript --no-tailwind --no-eslint --app --no-src-dir
cd /tmp/test-react && npm install @jeanmemory/react
echo "import { JeanProvider } from '@jeanmemory/react'; export default function Page() { return <JeanProvider apiKey='test'><div>✅ Works</div></JeanProvider>; }" > app/page.tsx
npm run build
```

## 📋 Expected Results

| SDK | Expected | If Broken |
|-----|----------|-----------|
| Node.js | `✅ Works: JeanMemoryClient {}` | Import/constructor error |
| Python | `✅ Works: <jean_memory.client.JeanMemoryClient object>` | Import error |
| React | Build succeeds | Build/import error |

## 🔍 What to Report

If any test fails, report:
1. **Error message** (exact text)
2. **What was imported** vs what was expected
3. **Package version** installed

**Time limit:** If any test takes >2 minutes, report as "timeout"