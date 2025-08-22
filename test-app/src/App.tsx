import React, { useState } from 'react';
import { JeanProvider, useJean } from '@jeanmemory/react';
import './App.css';

// Your Public Jean Memory API Key
// IMPORTANT: In a real app, use environment variables for this.
const JEAN_MEMORY_API_KEY = process.env.REACT_APP_JEAN_MEMORY_API_KEY || "YOUR_PUBLIC_API_KEY_HERE";

interface Result {
  mode: string;
  data: any;
  latency: number;
}

const SpeedTestUI: React.FC = () => {
  const { getContext } = useJean();
  const [query, setQuery] = useState<string>("What have I been working on recently?");
  const [results, setResults] = useState<Result[]>([]);
  const [isLoading, setIsLoading] = useState<string | null>(null);

  const handleTest = async (mode: 'fast' | 'balanced' | 'autonomous' | 'comprehensive') => {
    setIsLoading(mode);
    const startTime = Date.now();
    try {
      const context = await getContext(query, { mode });
      const endTime = Date.now();
      const latency = (endTime - startTime) / 1000;
      
      setResults(prevResults => [{ mode, data: context, latency }, ...prevResults]);
    } catch (error) {
      const endTime = Date.now();
      const latency = (endTime - startTime) / 1000;
      console.error(`Error testing ${mode} mode:`, error);
      const errorData = error instanceof Error ? error.message : "An unknown error occurred.";
      setResults(prevResults => [{ mode, data: { error: errorData }, latency }, ...prevResults]);
    } finally {
      setIsLoading(null);
    }
  };

  return (
    <div className="container">
      <h1>Jean Memory Speed Test</h1>
      <p>
        Enter a query and test the latency and response of each speed mode. 
        This demonstrates how to use the <code>@jeanmemory/react</code> SDK with a PKCE JWT flow managed by the provider.
      </p>
      
      <div className="input-group">
        <label htmlFor="query-input">Your Query:</label>
        <input
          id="query-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., What are my current goals?"
        />
      </div>

      <div className="button-group">
        <button onClick={() => handleTest('fast')} disabled={!!isLoading}>
          {isLoading === 'fast' ? 'Testing...' : 'Test Fast (≈1s)'}
        </button>
        <button onClick={() => handleTest('balanced')} disabled={!!isLoading}>
          {isLoading === 'balanced' ? 'Testing...' : 'Test Balanced (≈5s)'}
        </button>
        <button onClick={() => handleTest('autonomous')} disabled={!!isLoading}>
          {isLoading === 'autonomous' ? 'Testing...' : 'Test Autonomous (≈12s)'}
        </button>
        <button onClick={() => handleTest('comprehensive')} disabled={!!isLoading}>
          {isLoading === 'comprehensive' ? 'Testing...' : 'Test Comprehensive (≈30s)'}
        </button>
      </div>

      <div className="results-container">
        {results.map((result, index) => (
          <div key={index} className="result-card">
            <div className="result-header">
              <span className={`mode-badge mode-${result.mode}`}>{result.mode.toUpperCase()}</span>
              <span className="latency">{result.latency.toFixed(2)}s</span>
            </div>
            <pre className="result-body">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
};

const App: React.FC = () => {
  if (!JEAN_MEMORY_API_KEY || JEAN_MEMORY_API_KEY === "YOUR_PUBLIC_API_KEY_HERE") {
    return (
      <div className="container">
        <h1>Configuration Needed</h1>
        <p>Please provide your Jean Memory public API key.</p>
        <p>Create a <code>.env</code> file in the <code>test-app</code> directory with the following content:</p>
        <pre><code>REACT_APP_JEAN_MEMORY_API_KEY="your-public-api-key"</code></pre>
      </div>
    );
  }
  
  return (
    <JeanProvider apiKey={JEAN_MEMORY_API_KEY}>
      <SpeedTestUI />
    </JeanProvider>
  );
};

export default App;
