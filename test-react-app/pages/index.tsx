/**
 * Jean Memory React SDK Test Application
 * Demonstrates the 5-line integration working like Python SDK
 */
import React, { useState } from 'react';
import { useJeanAgent, SignInWithJean, JeanChat } from '../components/useJeanAgent';

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
          <div className="text-center mb-6">
            <a 
              href="/mcp" 
              className="inline-block bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              🚀 Try New MCP Integration
            </a>
            <p className="text-xs text-gray-500 mt-2">
              Direct jean_memory tool integration (same as Claude Desktop)
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
            {activeDemo === 'math' && <MathTutorDemo />}
            {activeDemo === 'therapist' && <TherapistDemo />}
            {activeDemo === 'custom' && <CustomDemo />}
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

// Example 1: Math Tutor (from /api-docs page)
function MathTutorDemo() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a patient math tutor who explains concepts step by step"
  });

  return (
    <div className="border-2 border-blue-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-blue-700">
        📚 Math Tutor Demo (5 lines of code)
      </h2>
      <div className="bg-blue-50 p-4 rounded mb-4">
        <pre className="text-sm">
{`const { agent, signIn } = useJeanAgent({
  systemPrompt: "You are a patient math tutor"
});

if (!agent) return <SignInWithJean onSuccess={signIn} />;
return <JeanChat agent={agent} />;`}
        </pre>
      </div>
      
      {!agent ? (
        <div className="text-center py-8">
          <p className="mb-4 text-gray-600">Sign in to test the math tutor</p>
          <SignInWithJean onSuccess={signIn} />
        </div>
      ) : (
        <JeanChat agent={agent} className="h-80 border rounded-lg p-4" />
      )}
    </div>
  );
}

// Example 2: Therapist (matching Python SDK example)
function TherapistDemo() {
  const { agent, signIn } = useJeanAgent({
    apiKey: "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
    systemPrompt: "You are a supportive therapist who provides empathetic guidance"
  });

  return (
    <div className="border-2 border-green-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-green-700">
        🌱 Therapist Demo (matches Python SDK)
      </h2>
      <div className="bg-green-50 p-4 rounded mb-4">
        <pre className="text-sm">
{`const { agent, signIn } = useJeanAgent({
  apiKey: "jean_sk_...",
  systemPrompt: "You are a supportive therapist"
});

if (!agent) return <SignInWithJean onSuccess={signIn} />;
return <JeanChat agent={agent} />;`}
        </pre>
      </div>
      
      {!agent ? (
        <div className="text-center py-8">
          <p className="mb-4 text-gray-600">Sign in to test the therapist</p>
          <SignInWithJean onSuccess={signIn} />
        </div>
      ) : (
        <JeanChat agent={agent} className="h-80 border rounded-lg p-4" />
      )}
    </div>
  );
}

// Example 3: Custom styled
function CustomDemo() {
  const { agent, signIn, user, isLoading, error } = useJeanAgent({
    systemPrompt: "You are a helpful AI assistant who knows the user's personal context"
  });

  if (!agent) {
    return (
      <div className="border-2 border-purple-200 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-purple-700">
          ✨ Custom Styled Demo
        </h2>
        <div className="text-center py-8">
          <h3 className="text-lg mb-2">Welcome to Your Personal AI</h3>
          <p className="text-gray-600 mb-6">
            Sign in with Jean Memory to get a personalized AI experience
          </p>
          <SignInWithJean 
            onSuccess={signIn}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          />
          {error && <p className="text-red-500 mt-4">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="border-2 border-purple-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-purple-700">
        ✨ Custom Styled Demo
      </h2>
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          Logged in as: <span className="font-semibold">{user?.email}</span>
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="text-sm text-purple-600 hover:text-purple-800"
        >
          Sign Out
        </button>
      </div>
      <JeanChat 
        agent={agent} 
        className="h-80 border-2 border-purple-200 rounded-lg p-4 bg-purple-50"
      />
    </div>
  );
}