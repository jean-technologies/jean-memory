import { useState, useEffect, useRef } from 'react'
import Head from 'next/head'

interface TestResult {
  id: string
  test_name: string
  success: boolean
  duration: number
  error?: string
  response_size?: number
}

export default function ChaosTestingApp() {
  const [results, setResults] = useState<TestResult[]>([])
  const [isRunning, setIsRunning] = useState(false)
  const [activeTests, setActiveTests] = useState(0)
  const [totalTests, setTotalTests] = useState(0)
  const ws = useRef<WebSocket | null>(null)

  const API_KEY = 'jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk'

  const addResult = (result: TestResult) => {
    setResults(prev => [result, ...prev.slice(0, 99)]) // Keep last 100 results
  }

  const runChaosTest = async () => {
    setIsRunning(true)
    setResults([])
    setActiveTests(0)
    setTotalTests(0)

    // Test 1: Basic React SDK functionality
    await testReactSDKBasics()

    // Test 2: Concurrent requests
    await testConcurrentRequests()

    // Test 3: Edge cases
    await testEdgeCases()

    // Test 4: Memory stress test
    await testMemoryStress()

    setIsRunning(false)
  }

  const testReactSDKBasics = async () => {
    const testName = 'react_sdk_basics'
    const startTime = Date.now()

    try {
      // Import React SDK dynamically
      const { JeanProvider, useJean } = await import('../../../sdk/react/dist/provider')
      
      addResult({
        id: Date.now().toString(),
        test_name: testName,
        success: true,
        duration: Date.now() - startTime,
        response_size: 0
      })
    } catch (error) {
      addResult({
        id: Date.now().toString(),
        test_name: testName,
        success: false,
        duration: Date.now() - startTime,
        error: error.message
      })
    }
  }

  const testConcurrentRequests = async () => {
    const concurrency = 10
    const requestsPerThread = 5
    setTotalTests(prev => prev + concurrency * requestsPerThread)

    const promises = []
    for (let i = 0; i < concurrency; i++) {
      for (let j = 0; j < requestsPerThread; j++) {
        promises.push(makeConcurrentRequest(i, j))
      }
    }

    await Promise.all(promises)
  }

  const makeConcurrentRequest = async (threadId: number, requestId: number) => {
    const testName = `concurrent_${threadId}_${requestId}`
    const startTime = Date.now()
    setActiveTests(prev => prev + 1)

    try {
      const response = await fetch('/api/test-jean', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: `Concurrent test from thread ${threadId}, request ${requestId}`,
          userToken: 'mock_jwt_token',
          isNewConversation: Math.random() > 0.5
        })
      })

      const data = await response.json()
      
      if (response.ok) {
        addResult({
          id: Date.now().toString() + Math.random(),
          test_name: testName,
          success: true,
          duration: Date.now() - startTime,
          response_size: data.text?.length || 0
        })
      } else {
        throw new Error(data.error || 'API request failed')
      }
    } catch (error) {
      addResult({
        id: Date.now().toString() + Math.random(),
        test_name: testName,
        success: false,
        duration: Date.now() - startTime,
        error: error.message
      })
    } finally {
      setActiveTests(prev => prev - 1)
    }
  }

  const testEdgeCases = async () => {
    const edgeCases = [
      { message: '', name: 'empty_message' },
      { message: ' ', name: 'whitespace_message' },
      { message: 'a'.repeat(10000), name: 'huge_message' },
      { message: '🔥'.repeat(100), name: 'emoji_spam' },
      { message: '{"json": "test"}', name: 'json_message' },
      { message: '<script>alert("xss")</script>', name: 'xss_attempt' },
      { message: "'; DROP TABLE users; --", name: 'sql_injection' }
    ]

    setTotalTests(prev => prev + edgeCases.length)

    for (const testCase of edgeCases) {
      const startTime = Date.now()
      setActiveTests(prev => prev + 1)

      try {
        const response = await fetch('/api/test-jean', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: testCase.message,
            userToken: 'mock_jwt_token',
            isNewConversation: false
          })
        })

        const data = await response.json()
        
        addResult({
          id: Date.now().toString() + Math.random(),
          test_name: `edge_case_${testCase.name}`,
          success: response.ok,
          duration: Date.now() - startTime,
          response_size: data.text?.length || 0,
          error: response.ok ? undefined : (data.error || 'Request failed')
        })
      } catch (error) {
        addResult({
          id: Date.now().toString() + Math.random(),
          test_name: `edge_case_${testCase.name}`,
          success: false,
          duration: Date.now() - startTime,
          error: error.message
        })
      } finally {
        setActiveTests(prev => prev - 1)
      }

      // Small delay to avoid overwhelming
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }

  const testMemoryStress = async () => {
    const memoryTests = 20
    setTotalTests(prev => prev + memoryTests)

    for (let i = 0; i < memoryTests; i++) {
      const startTime = Date.now()
      setActiveTests(prev => prev + 1)

      try {
        const uniqueId = Math.random().toString(36).substring(7)
        const memory = `CHAOS_MEMORY_${uniqueId}_${i}`

        // Store memory
        await fetch('/api/test-jean', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: `Remember this: ${memory}`,
            userToken: 'mock_jwt_token',
            isNewConversation: false
          })
        })

        // Try to retrieve it
        await new Promise(resolve => setTimeout(resolve, 1000)) // Wait 1 second

        const response = await fetch('/api/test-jean', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: `Do you remember ${uniqueId}?`,
            userToken: 'mock_jwt_token',
            isNewConversation: false
          })
        })

        const data = await response.json()
        const memoryFound = data.text?.includes(uniqueId) || false

        addResult({
          id: Date.now().toString() + Math.random(),
          test_name: `memory_stress_${i}`,
          success: response.ok && memoryFound,
          duration: Date.now() - startTime,
          response_size: data.text?.length || 0,
          error: response.ok ? (memoryFound ? undefined : 'Memory not found') : (data.error || 'Request failed')
        })
      } catch (error) {
        addResult({
          id: Date.now().toString() + Math.random(),
          test_name: `memory_stress_${i}`,
          success: false,
          duration: Date.now() - startTime,
          error: error.message
        })
      } finally {
        setActiveTests(prev => prev - 1)
      }
    }
  }

  const successCount = results.filter(r => r.success).length
  const failCount = results.length - successCount
  const avgDuration = results.length > 0 ? results.reduce((sum, r) => sum + r.duration, 0) / results.length : 0
  const avgResponseSize = results.filter(r => r.response_size).reduce((sum, r) => sum + (r.response_size || 0), 0) / Math.max(1, results.filter(r => r.response_size).length)

  return (
    <>
      <Head>
        <title>🔥 Jean Memory Chaos Testing</title>
      </Head>
      
      <div style={{ padding: '20px', fontFamily: 'monospace', backgroundColor: '#0a0a0a', color: '#00ff00', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ color: '#ff4444', fontSize: '2.5em', textShadow: '0 0 10px #ff4444' }}>
            🔥 REACT CHAOS TESTING 🔥
          </h1>
          <p style={{ color: '#ffaa00', fontSize: '1.2em' }}>
            ROUND 2: Frontend SDK Stress Testing
          </p>
        </div>

        <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', flexWrap: 'wrap' }}>
          <button
            onClick={runChaosTest}
            disabled={isRunning}
            style={{
              padding: '15px 30px',
              fontSize: '18px',
              backgroundColor: isRunning ? '#666' : '#ff4444',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: isRunning ? 'not-allowed' : 'pointer',
              textShadow: '0 0 5px #000'
            }}
          >
            {isRunning ? '🔥 CHAOS IN PROGRESS...' : '🚀 LAUNCH CHAOS'}
          </button>
          
          <div style={{ padding: '15px', backgroundColor: '#1a1a1a', borderRadius: '5px', border: '2px solid #333' }}>
            <strong>Active Tests:</strong> {activeTests} | <strong>Total Tests:</strong> {totalTests}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '20px' }}>
          <div style={{ padding: '15px', backgroundColor: '#1a1a1a', borderRadius: '5px', border: '2px solid #00aa00' }}>
            <h3 style={{ color: '#00ff00', margin: '0 0 10px 0' }}>✅ Success</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{successCount}</div>
          </div>
          
          <div style={{ padding: '15px', backgroundColor: '#1a1a1a', borderRadius: '5px', border: '2px solid #aa0000' }}>
            <h3 style={{ color: '#ff4444', margin: '0 0 10px 0' }}>❌ Failed</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{failCount}</div>
          </div>
          
          <div style={{ padding: '15px', backgroundColor: '#1a1a1a', borderRadius: '5px', border: '2px solid #aaaa00' }}>
            <h3 style={{ color: '#ffff00', margin: '0 0 10px 0' }}>⏱️ Avg Time</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{avgDuration.toFixed(0)}ms</div>
          </div>
          
          <div style={{ padding: '15px', backgroundColor: '#1a1a1a', borderRadius: '5px', border: '2px solid #00aaaa' }}>
            <h3 style={{ color: '#00ffff', margin: '0 0 10px 0' }}>📊 Avg Size</h3>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{avgResponseSize.toFixed(0)} chars</div>
          </div>
        </div>

        <div style={{ height: '400px', overflowY: 'auto', backgroundColor: '#1a1a1a', padding: '15px', borderRadius: '5px', border: '2px solid #333' }}>
          <h3 style={{ color: '#ffffff', marginTop: '0' }}>🔍 Real-time Results</h3>
          {results.map((result) => (
            <div
              key={result.id}
              style={{
                padding: '8px',
                margin: '5px 0',
                backgroundColor: result.success ? '#0a3a0a' : '#3a0a0a',
                borderRadius: '3px',
                borderLeft: `4px solid ${result.success ? '#00ff00' : '#ff4444'}`,
                fontSize: '12px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold', color: result.success ? '#00ff00' : '#ff4444' }}>
                  {result.success ? '✅' : '❌'} {result.test_name}
                </span>
                <span style={{ color: '#aaaaaa' }}>
                  {result.duration}ms
                  {result.response_size ? ` | ${result.response_size} chars` : ''}
                </span>
              </div>
              {result.error && (
                <div style={{ color: '#ff8888', fontSize: '11px', marginTop: '3px' }}>
                  Error: {result.error}
                </div>
              )}
            </div>
          ))}
          {results.length === 0 && (
            <div style={{ textAlign: 'center', color: '#666', padding: '50px' }}>
              No results yet. Click "LAUNCH CHAOS" to begin testing!
            </div>
          )}
        </div>
      </div>
    </>
  )
}