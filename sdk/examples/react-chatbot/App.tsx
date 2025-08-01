/**
 * Jean Memory SDK Demo - React Chatbot with Assistant-UI
 * 5-line integration example using @assistant-ui/react and Jean Memory
 */
import React from 'react';
import { AssistantRuntimeProvider, Thread } from '@assistant-ui/react';
import { useJeanAgent } from '@jeanmemory/react';

// Replace with your actual API key
const JEAN_API_KEY = "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA";

function App() {
  // 🎯 5-line Jean Memory integration
  const { agent, signIn } = useJeanAgent({
    apiKey: JEAN_API_KEY,
    systemPrompt: "You are a helpful assistant with access to the user's personal context from Jean Memory."
  });

  if (!agent) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full space-y-8">
          <div className="text-center">
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              Jean Memory Chatbot
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              Sign in to start chatting with your personalized AI assistant
            </p>
          </div>
          <button
            onClick={signIn}
            className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            🧠 Sign in with Jean
          </button>
        </div>
      </div>
    );
  }

  // 🎯 Use assistant-ui with Jean Memory enhanced runtime
  return (
    <AssistantRuntimeProvider runtime={agent.runtime}>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto p-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-[80vh]">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">
                    Jean Memory Assistant
                  </h1>
                  <p className="text-sm text-gray-500">
                    Connected to your personal context • {agent.userId}
                  </p>
                </div>
                <button
                  onClick={() => window.location.reload()}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Sign Out
                </button>
              </div>
            </div>
            
            {/* Assistant-UI Thread Component */}
            <div className="h-full">
              <Thread />
            </div>
          </div>
        </div>
      </div>
    </AssistantRuntimeProvider>
  );
}

export default App;