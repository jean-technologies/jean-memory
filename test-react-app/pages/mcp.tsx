/**
 * Jean Memory React SDK MCP Test Application
 * Tests direct MCP tool integration (jean_memory + store_document)
 */
import React, { useState } from 'react';
import { useJeanAgentMCP, SignInWithJeanMCP, JeanChatMCP } from '../components/useJeanAgentMCP';

export default function MCPTest() {
  const [activeDemo, setActiveDemo] = useState<'math' | 'therapist' | 'custom'>('math');

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h1 className="text-3xl font-bold text-center mb-4">
            🧠 Jean Memory React SDK - MCP Integration
          </h1>
          <p className="text-gray-600 text-center mb-6">
            Direct integration with jean_memory and store_document MCP tools
            <br />
            <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
              Same tools used by Claude Desktop and Cursor
            </span>
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
              Math Tutor MCP
            </button>
            <button
              onClick={() => setActiveDemo('therapist')}
              className={`px-4 py-2 rounded ${
                activeDemo === 'therapist' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Therapist MCP
            </button>
            <button
              onClick={() => setActiveDemo('custom')}
              className={`px-4 py-2 rounded ${
                activeDemo === 'custom' 
                  ? 'bg-purple-600 text-white' 
                  : 'bg-gray-200 text-gray-700'
              }`}
            >
              Custom MCP
            </button>
          </div>

          <div className="space-y-8">
            {activeDemo === 'math' && <MathTutorMCPDemo />}
            {activeDemo === 'therapist' && <TherapistMCPDemo />}
            {activeDemo === 'custom' && <CustomMCPDemo />}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">🔧 MCP Architecture</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold mb-2 text-blue-600">🧠 jean_memory Tool</h3>
              <p className="text-sm text-gray-600">
                Context engineering, memory triage, and intelligent retrieval.
                Same logic as Claude Desktop integration.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2 text-green-600">📄 store_document Tool</h3>
              <p className="text-sm text-gray-600">
                Fast document storage with background processing.
                Perfect for conversation archiving.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2 text-purple-600">🚀 Direct MCP Calls</h3>
              <p className="text-sm text-gray-600">
                No intermediate layers - calls /mcp/{'{'}client{'}'}/messages/{'{'}user_id{'}'} 
                with JSON-RPC format.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2 text-orange-600">⚡ True Parity</h3>
              <p className="text-sm text-gray-600">
                Identical to Claude Desktop/Cursor behavior.
                Uses the same MCP infrastructure.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Math Tutor MCP Demo
function MathTutorMCPDemo() {
  const agent = useJeanAgentMCP({
    systemPrompt: "You are a patient math tutor who explains concepts step by step"
  });

  return (
    <div className="border-2 border-blue-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-blue-700">
        📚 Math Tutor MCP Demo
      </h2>
      <div className="bg-blue-50 p-4 rounded mb-4">
        <h4 className="font-semibold mb-2">🔧 MCP Tools Used:</h4>
        <ul className="text-sm space-y-1">
          <li>• <code>jean_memory</code> - Context retrieval and memory saving</li>
          <li>• <code>store_document</code> - Conversation archiving</li>
          <li>• Direct JSON-RPC calls to MCP endpoint</li>
        </ul>
      </div>
      
      {!agent.isAuthenticated ? (
        <SignInWithJeanMCP onSuccess={agent.signIn} />
      ) : (
        <JeanChatMCP agent={agent} className="h-80 border rounded-lg" />
      )}
    </div>
  );
}

// Therapist MCP Demo
function TherapistMCPDemo() {
  const agent = useJeanAgentMCP({
    apiKey: "jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
    systemPrompt: "You are a supportive therapist who provides empathetic guidance"
  });

  return (
    <div className="border-2 border-green-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-green-700">
        🌱 Therapist MCP Demo
      </h2>
      <div className="bg-green-50 p-4 rounded mb-4">
        <h4 className="font-semibold mb-2">🔧 MCP Integration:</h4>
        <ul className="text-sm space-y-1">
          <li>• Same MCP tools as Claude Desktop/Cursor</li>
          <li>• Intelligent context engineering</li>
          <li>• Automatic memory triage and saving</li>
        </ul>
      </div>
      
      {!agent.isAuthenticated ? (
        <SignInWithJeanMCP onSuccess={agent.signIn} />
      ) : (
        <JeanChatMCP agent={agent} className="h-80 border rounded-lg" />
      )}
    </div>
  );
}

// Custom MCP Demo
function CustomMCPDemo() {
  const agent = useJeanAgentMCP({
    systemPrompt: "You are a helpful AI assistant who knows the user's personal context"
  });

  if (!agent.isAuthenticated) {
    return (
      <div className="border-2 border-purple-200 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4 text-purple-700">
          ✨ Custom MCP Demo
        </h2>
        <div className="text-center py-8">
          <h3 className="text-lg mb-2">MCP-Powered Personal AI</h3>
          <p className="text-gray-600 mb-6">
            Direct integration with jean_memory and store_document tools
          </p>
          <SignInWithJeanMCP 
            onSuccess={agent.signIn}
            className="max-w-md mx-auto"
          />
        </div>
      </div>
    );
  }

  return (
    <div className="border-2 border-purple-200 rounded-lg p-6">
      <h2 className="text-xl font-bold mb-4 text-purple-700">
        ✨ Custom MCP Demo
      </h2>
      <div className="flex justify-between items-center mb-4">
        <div className="text-sm text-gray-600">
          MCP User: <span className="font-semibold">{agent.user?.email}</span>
        </div>
        <div className="flex space-x-2">
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            jean_memory
          </span>
          <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
            store_document
          </span>
        </div>
      </div>
      <JeanChatMCP 
        agent={agent} 
        className="h-80 border-2 border-purple-200 rounded-lg bg-purple-50"
      />
    </div>
  );
}