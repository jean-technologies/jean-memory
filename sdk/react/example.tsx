/**
 * Jean Memory React SDK - Example Usage
 * This demonstrates the 5-line integration working like the Python SDK
 */
import React from 'react';
import { useJeanAgent, SignInWithJean, JeanChat } from './index';

// Example 1: Math Tutor App (exact code from /api-docs page)
function MathTutorApp() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a patient math tutor"
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />;
}

// Example 2: Therapist App (matching Python SDK example)
function TherapistApp() {
  const { agent, signIn } = useJeanAgent({
    apiKey: "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
    systemPrompt: "You are a supportive therapist"
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />;
}

// Example 3: Custom styling
function CustomStyledApp() {
  const { agent, signIn, user, isLoading, error } = useJeanAgent({
    systemPrompt: "You are a helpful assistant"
  });

  if (!agent) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h1 className="text-2xl font-bold mb-4">Welcome to My AI App</h1>
          <p className="text-gray-600 mb-4">
            Sign in with your Jean Memory account to get personalized assistance.
          </p>
          <SignInWithJean 
            onSuccess={signIn}
            className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
          />
          {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold">Personal AI Assistant</h1>
            <div className="text-sm text-gray-600">
              Welcome, {user?.email} | <button onClick={() => window.location.reload()}>Sign Out</button>
            </div>
          </div>
          <JeanChat 
            agent={agent} 
            className="h-96 border-2 border-gray-200 rounded-lg p-4"
          />
        </div>
      </div>
    </div>
  );
}

export { MathTutorApp, TherapistApp, CustomStyledApp };