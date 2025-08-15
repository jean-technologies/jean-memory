const { JeanMemoryClient } = require('@jeanmemory/node');

try {
  const client = new JeanMemoryClient({ apiKey: 'jean_sk_test_key' });
  console.log('Node.js SDK works!');
} catch (e) {
  console.error('Node.js SDK failed:', e);
}
