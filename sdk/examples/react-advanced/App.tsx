/**
 * Jean Memory React SDK - Advanced Example
 * Shows custom styling and direct MCP tool usage
 */
import React, { useState } from 'react';
import { JeanProvider, useJean, useJeanMCP, SignInWithJean } from '@jeanmemory/react';

// Example 1: Custom Styled App
function CustomStyledApp() {
  return (
    <JeanProvider apiKey={process.env.REACT_APP_JEAN_API_KEY!}>
      <div className="min-h-screen bg-gray-100 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h1 className="text-2xl font-bold mb-4">Personal AI Assistant</h1>
            <CustomChat />
          </div>
        </div>
      </div>
    </JeanProvider>
  );
}

// Example 2: Custom Chat with MCP Tools
function CustomChat() {
  const agent = useJean();
  const mcpTools = useJeanMCP({ 
    apiKey: process.env.REACT_APP_JEAN_API_KEY! 
  });
  const [input, setInput] = useState('');
  const [memories, setMemories] = useState<string[]>([]);

  const handleDirectMemoryAdd = async () => {
    if (!agent.user || !input.trim()) return;
    
    try {
      const result = await mcpTools.addMemory(agent.user, input);
      setMemories(prev => [...prev, input]);
      setInput('');
      console.log('Memory added:', result);
    } catch (error) {
      console.error('Failed to add memory:', error);
    }
  };

  const handleDirectSearch = async () => {
    if (!agent.user || !input.trim()) return;
    
    try {
      const results = await mcpTools.searchMemory(agent.user, input);
      console.log('Search results:', results);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  if (!agent.isAuthenticated) {
    return (
      <div className="text-center p-8">
        <h2 className="text-xl font-semibold mb-4">Sign in to continue</h2>
        <SignInWithJean onSuccess={agent.setUser} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-600">
          Welcome, {agent.user.email}
        </span>
        <button 
          onClick={agent.signOut}
          className="text-sm text-red-600 hover:text-red-800"
        >
          Sign Out
        </button>
      </div>
      
      {/* Direct Memory Tools */}
      <div className="border-2 border-blue-200 rounded-lg p-4 bg-blue-50">
        <h3 className="font-semibold mb-2">Direct MCP Tools</h3>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter text for memory operations..."
            className="flex-1 px-3 py-2 border rounded-md"
          />
          <button
            onClick={handleDirectMemoryAdd}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Add Memory
          </button>
          <button
            onClick={handleDirectSearch}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
          >
            Search
          </button>
        </div>
        {memories.length > 0 && (
          <div className="mt-2">
            <p className="text-sm text-gray-600">Recent memories added:</p>
            <ul className="text-xs text-gray-500">
              {memories.slice(-3).map((memory, i) => (
                <li key={i}>• {memory}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      
      {/* Regular Chat (using our JeanChat component) */}
      <div className="h-96 border-2 border-gray-200 rounded-lg">
        {/* You could use JeanChat here or build custom UI */}
        <div className="p-4 text-center text-gray-500">
          <p>Regular chat interface would go here</p>
          <p className="text-sm">Or use the JeanChat component</p>
        </div>
      </div>
    </div>
  );
}

export default CustomStyledApp;