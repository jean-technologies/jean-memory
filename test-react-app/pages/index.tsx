/**
 * Jean Memory React SDK Test Application
 * Demonstrates the 5-line integration working like Python SDK
 */
import React, { useState } from 'react';

export default function Home() {
  const [activeDemo, setActiveDemo] = useState<'math' | 'therapist' | 'custom'>('math');

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h1 className="text-3xl font-bold text-center mb-4">
            🧠 Jean Memory React SDK Test
          </h1>
          <p className="text-gray-600 text-center mb-6">
            Testing 5-line integration matching Python SDK functionality
          </p>
          <div className="text-center mb-6 space-x-4">
            <a 
              href="/mcp" 
              className="inline-block bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              🚀 Try New MCP Integration
            </a>
            <a 
              href="/oauth-test" 
              className="inline-block bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              🔐 Test OAuth Flow
            </a>
            <a 
              href="/jean-memory-tool-test" 
              className="inline-block bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              🧠 Test Jean Memory Tool
            </a>
            <p className="text-xs text-gray-500 mt-2">
              Direct jean_memory tool integration (same as Claude Desktop) | OAuth 2.1 PKCE Testing | Tool Depth Analysis
            </p>
          </div>
          
          <div className="flex justify-center space-x-4 mb-8">
            <button
              onClick={() => setActiveDemo('math')}
              className={`px-4 py-2 rounded ${
                activeDemo === 'math' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Math Tutor Demo
            </button>
            <button
              onClick={() => setActiveDemo('therapist')}
              className={`px-4 py-2 rounded ${
                activeDemo === 'therapist' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Therapist Demo
            </button>
            <button
              onClick={() => setActiveDemo('custom')}
              className={`px-4 py-2 rounded ${
                activeDemo === 'custom' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Custom Demo
            </button>
          </div>

          <div className="space-y-8">
            <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200">
              <h3 className="text-lg font-semibold mb-2 text-yellow-800">🚧 SDK Integration Under Testing</h3>
              <p className="text-yellow-700">
                The published SDK (jeanmemory-react@0.1.3) has module resolution issues that need to be fixed before launch.
                Use the OAuth Test page to test authentication functionality.
              </p>
              <div className="mt-4">
                <a 
                  href="/oauth-test" 
                  className="inline-block bg-yellow-600 text-white px-4 py-2 rounded-lg hover:bg-yellow-700 transition-colors"
                >
                  🔐 Test OAuth Flow Instead
                </a>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">How it Works</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-2">🔐 Authentication</h3>
              <p className="text-sm text-gray-600">
                Uses /sdk/auth/login endpoint with API key validation. 
                Same as Python SDK.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">💬 Chat Integration</h3>
              <p className="text-sm text-gray-600">
                Uses /sdk/chat/enhance endpoint with system prompt injection.
                Matches Python SDK functionality.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">🧠 Memory Context</h3>
              <p className="text-sm text-gray-600">
                Retrieves personalized user context automatically.
                Multi-tenant isolation per user.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">⚡ 5-Line Integration</h3>
              <p className="text-sm text-gray-600">
                Import → useJeanAgent → SignInWithJean → JeanChat. Done!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Demo components temporarily disabled due to SDK issues
// See /oauth-test page for OAuth flow testing