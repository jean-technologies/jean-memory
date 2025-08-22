import React, { useState, useEffect } from 'react';
import { JeanProvider, useJean } from '@jeanmemory/react';
import './App.css';

// Your Public Jean Memory API Key
const JEAN_MEMORY_API_KEY = process.env.REACT_APP_JEAN_MEMORY_API_KEY || "YOUR_PUBLIC_API_KEY_HERE";

interface TestResult {
  mode: string;
  query: string;
  response: any;
  latency: number;
  timestamp: Date;
  status: 'success' | 'error';
  hasContent: boolean;
  isEmpty: boolean;
  errorMessage?: string;
}

interface ModeConfig {
  name: 'fast' | 'balanced' | 'autonomous' | 'comprehensive';
  expectedLatency: string;
  description: string;
  color: string;
}

const modes: ModeConfig[] = [
  { name: 'fast', expectedLatency: '1-2s', description: 'Direct memory search', color: '#10b981' },
  { name: 'balanced', expectedLatency: '3-5s', description: 'AI synthesis with Gemini', color: '#3b82f6' },
  { name: 'autonomous', expectedLatency: '8-15s', description: 'Intelligent orchestration', color: '#8b5cf6' },
  { name: 'comprehensive', expectedLatency: '20-30s', description: 'Deep analysis', color: '#ef4444' }
];

const SpeedTestUI: React.FC = () => {
  const { getContext, user, isAuthenticated } = useJean();
  const [query, setQuery] = useState<string>("What have I been working on recently?");
  const [results, setResults] = useState<TestResult[]>([]);
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [testingSuite, setTestingSuite] = useState(false);

  // Analyze result to check if it's empty or has error
  const analyzeResponse = (response: any): { hasContent: boolean; isEmpty: boolean; errorMessage?: string } => {
    if (!response) {
      return { hasContent: false, isEmpty: true };
    }

    // Check for error in response
    if (typeof response === 'object') {
      if (response.error || response.status === 'error') {
        return { 
          hasContent: false, 
          isEmpty: true, 
          errorMessage: response.error || response.message || 'Unknown error' 
        };
      }
      
      // Check for content in various formats
      if (response.content) {
        const content = Array.isArray(response.content) ? response.content[0]?.text : response.content;
        if (content && content.includes('error')) {
          return { hasContent: false, isEmpty: true, errorMessage: content };
        }
        return { hasContent: Boolean(content), isEmpty: !content };
      }
      
      if (response.result) {
        return { hasContent: true, isEmpty: false };
      }
    }

    // For string responses
    if (typeof response === 'string') {
      if (response.includes('error') || response.includes('Error')) {
        return { hasContent: false, isEmpty: true, errorMessage: response };
      }
      return { hasContent: response.length > 0, isEmpty: response.trim().length === 0 };
    }

    return { hasContent: false, isEmpty: true };
  };

  const testMode = async (mode: ModeConfig['name']) => {
    setIsLoading(mode);
    const startTime = Date.now();
    
    try {
      const response = await getContext(query, { mode });
      const latency = (Date.now() - startTime) / 1000;
      const analysis = analyzeResponse(response);
      
      const result: TestResult = {
        mode,
        query,
        response,
        latency,
        timestamp: new Date(),
        status: analysis.errorMessage ? 'error' : 'success',
        hasContent: analysis.hasContent,
        isEmpty: analysis.isEmpty,
        errorMessage: analysis.errorMessage
      };
      
      setResults(prev => [result, ...prev]);
      return result;
    } catch (error) {
      const latency = (Date.now() - startTime) / 1000;
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      
      const result: TestResult = {
        mode,
        query,
        response: { error: errorMessage },
        latency,
        timestamp: new Date(),
        status: 'error',
        hasContent: false,
        isEmpty: true,
        errorMessage
      };
      
      setResults(prev => [result, ...prev]);
      return result;
    } finally {
      setIsLoading(null);
    }
  };

  const runFullTestSuite = async () => {
    setTestingSuite(true);
    setResults([]);
    
    for (const mode of modes) {
      await testMode(mode.name);
      // Small delay between tests
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    setTestingSuite(false);
  };

  const clearResults = () => {
    setResults([]);
  };

  // Format response for display
  const formatResponse = (response: any): string => {
    if (typeof response === 'string') return response;
    if (typeof response === 'object') {
      // Handle content array format
      if (response.content && Array.isArray(response.content)) {
        return response.content[0]?.text || JSON.stringify(response, null, 2);
      }
      return JSON.stringify(response, null, 2);
    }
    return String(response);
  };

  // Calculate statistics
  const getStats = () => {
    const modeStats: Record<string, { count: number; avgLatency: number; successRate: number }> = {};
    
    modes.forEach(mode => {
      const modeResults = results.filter(r => r.mode === mode.name);
      if (modeResults.length > 0) {
        const successful = modeResults.filter(r => r.status === 'success' && r.hasContent);
        const totalLatency = modeResults.reduce((sum, r) => sum + r.latency, 0);
        
        modeStats[mode.name] = {
          count: modeResults.length,
          avgLatency: totalLatency / modeResults.length,
          successRate: (successful.length / modeResults.length) * 100
        };
      }
    });
    
    return modeStats;
  };

  const stats = getStats();

  return (
    <div className="container">
      <h1>🧠 Jean Memory Speed Test</h1>
      
      {isAuthenticated ? (
        <div className="auth-status success">
          ✅ Authenticated as: {user?.email || 'Test User'}
        </div>
      ) : (
        <div className="auth-status warning">
          ⚠️ Using test mode (not authenticated)
        </div>
      )}

      <div className="test-controls">
        <div className="input-group">
          <label htmlFor="query-input">Test Query:</label>
          <input
            id="query-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your test query..."
            disabled={!!isLoading || testingSuite}
          />
        </div>

        <div className="button-group">
          {modes.map(mode => (
            <button
              key={mode.name}
              onClick={() => testMode(mode.name)}
              disabled={!!isLoading || testingSuite}
              className={`mode-button ${isLoading === mode.name ? 'loading' : ''}`}
              style={{ borderColor: mode.color }}
            >
              {isLoading === mode.name ? (
                <span>Testing...</span>
              ) : (
                <>
                  <strong>{mode.name.toUpperCase()}</strong>
                  <small>{mode.expectedLatency}</small>
                </>
              )}
            </button>
          ))}
        </div>

        <div className="suite-controls">
          <button 
            onClick={runFullTestSuite} 
            disabled={!!isLoading || testingSuite}
            className="suite-button"
          >
            {testingSuite ? '🔄 Running Test Suite...' : '🚀 Run Full Test Suite'}
          </button>
          <button 
            onClick={clearResults} 
            disabled={!!isLoading || testingSuite || results.length === 0}
            className="clear-button"
          >
            🗑️ Clear Results
          </button>
        </div>
      </div>

      {Object.keys(stats).length > 0 && (
        <div className="stats-container">
          <h3>📊 Statistics</h3>
          <div className="stats-grid">
            {modes.map(mode => {
              const stat = stats[mode.name];
              if (!stat) return null;
              
              return (
                <div key={mode.name} className="stat-card" style={{ borderColor: mode.color }}>
                  <h4>{mode.name}</h4>
                  <div className="stat-item">
                    <span>Tests:</span> {stat.count}
                  </div>
                  <div className="stat-item">
                    <span>Avg Latency:</span> {stat.avgLatency.toFixed(2)}s
                  </div>
                  <div className="stat-item">
                    <span>Success Rate:</span> {stat.successRate.toFixed(0)}%
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="results-container">
        <h3>📝 Test Results ({results.length})</h3>
        {results.map((result, index) => (
          <div 
            key={index} 
            className={`result-card ${result.status}`}
            style={{ borderLeftColor: modes.find(m => m.name === result.mode)?.color }}
          >
            <div className="result-header">
              <div className="result-meta">
                <span className={`mode-badge mode-${result.mode}`}>
                  {result.mode.toUpperCase()}
                </span>
                <span className="latency-badge">
                  ⏱️ {result.latency.toFixed(2)}s
                </span>
                <span className={`status-badge ${result.status}`}>
                  {result.status === 'success' ? '✅' : '❌'} {result.status}
                </span>
                {result.isEmpty && (
                  <span className="warning-badge">⚠️ Empty Response</span>
                )}
              </div>
              <div className="timestamp">
                {result.timestamp.toLocaleTimeString()}
              </div>
            </div>
            
            <div className="result-query">
              Query: "{result.query}"
            </div>
            
            {result.errorMessage && (
              <div className="error-message">
                ❌ Error: {result.errorMessage}
              </div>
            )}
            
            <pre className="result-body">
              {formatResponse(result.response).substring(0, 500)}
              {formatResponse(result.response).length > 500 && '...'}
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
        <h1>⚙️ Configuration Required</h1>
        <div className="config-instructions">
          <p>Please provide your Jean Memory public API key to continue.</p>
          <p>Create a <code>.env</code> file in the <code>test-app</code> directory:</p>
          <pre>
            <code>REACT_APP_JEAN_MEMORY_API_KEY="your-public-api-key"</code>
          </pre>
          <p>Then restart the development server.</p>
        </div>
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