/**
 * Jean Memory React SDK - Complete Working Example
 * 
 * This example follows the exact instructions from /api-docs
 * Copy this code to test the 5-line integration working with real Jean Memory
 * 
 * Prerequisites:
 * 1. npm install jeanmemory-react
 * 2. Have a Jean Memory account (sign up at jeanmemory.com)
 * 3. Run this in a React/Next.js application
 */

import React, { useState } from 'react';
import { useJeanAgent, SignInWithJean, JeanChat } from 'jeanmemory-react';

export default function JeanMemoryDemo() {
  const [activeDemo, setActiveDemo] = useState<'math' | 'therapist' | 'custom'>('math');

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h1 className="text-3xl font-bold text-center mb-4">
            🧠 Jean Memory React SDK Demo
          </h1>
          <p className="text-center text-gray-600 mb-6">
            Testing 5-line integration matching Python SDK functionality
          </p>
          
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
                Uses /auth/login endpoint with Supabase integration. 
                Same authentication flow as Python SDK.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">💬 MCP Integration</h3>
              <p className="text-sm text-gray-600">
                Uses /mcp/messages/ endpoint with JSON-RPC for jean_memory tool calls.
                Matches Python SDK functionality exactly.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">🧠 System Prompts</h3>
              <p className="text-sm text-gray-600">
                Injects system prompts using [SYSTEM: prompt] format.
                Enables different AI personalities per application.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">⚡ Memory Context</h3>
              <p className="text-sm text-gray-600">
                Automatically retrieves user's personal context.
                Multi-tenant isolation ensures privacy.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Example 1: Math Tutor (5 lines of code from /api-docs)
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
        <pre className="text-sm overflow-x-auto">
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

// Example 2: Therapist (matches Python SDK functionality from /api-docs)
function TherapistDemo() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a supportive therapist who provides empathetic guidance"
  });

  return (
    <div className="border-2 border-green-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-green-700">
        🌱 Therapist Demo (matches Python SDK)
      </h2>
      <div className="bg-green-50 p-4 rounded mb-4">
        <pre className="text-sm overflow-x-auto">
{`const { agent, signIn } = useJeanAgent({
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

// Example 3: Custom styled demo (advanced usage from /api-docs)
function CustomDemo() {
  const { agent, signIn, user, error } = useJeanAgent({
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

/**
 * Test Instructions:
 * 
 * 1. Install the SDK:
 *    npm install jeanmemory-react
 * 
 * 2. Import and use this component in your React app:
 *    import JeanMemoryDemo from './JeanMemoryReactExample';
 *    
 *    function App() {
 *      return <JeanMemoryDemo />;
 *    }
 * 
 * 3. Sign in with your Jean Memory account when prompted
 * 
 * 4. Test different system prompts:
 *    - Math Tutor: "Help me solve 2x + 5 = 13" 
 *    - Therapist: "I'm feeling overwhelmed with work"
 *    - Custom: "Tell me something about myself"
 * 
 * Expected Results:
 * - Each agent should behave according to its system prompt
 * - The AI should have access to your personal Jean Memory context
 * - Authentication should work seamlessly across all demos
 * - Chat interface should be responsive and functional
 * 
 * If you encounter issues:
 * - Check browser console for error messages
 * - Verify your Jean Memory account credentials
 * - Ensure you have a stable internet connection
 * - Contact support if authentication fails repeatedly
 */