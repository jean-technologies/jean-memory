/**
 * Test the new MCP-based React SDK implementation
 * This validates that the business case integration works
 */
import React from 'react';
import { JeanAgent } from './sdk/react';

// Test 1: Business Case 5-line Integration - Math Tutor
function TestMathTutor() {
  return (
    <div>
      <h1>Test: Math Tutor (Business Case)</h1>
      <JeanAgent 
        apiKey="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"
        systemPrompt="You are an expert math tutor who helps students with algebra, calculus, and statistics"
        className="h-96 border rounded-lg"
      />
    </div>
  );
}

// Test 2: Business Case 5-line Integration - Writing Coach  
function TestWritingCoach() {
  return (
    <div>
      <h1>Test: Writing Coach (Business Case)</h1>
      <JeanAgent 
        apiKey="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA"
        systemPrompt="You are an expert writing coach who helps improve clarity and engagement"
        className="h-96 border rounded-lg"
      />
    </div>
  );
}

// Test App
export default function TestMCPSDK() {
  return (
    <div className="p-8 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-4">🧠 Jean Memory React SDK Test</h1>
        <p className="text-gray-600 mb-8">Testing the new MCP-based implementation</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <TestMathTutor />
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-lg">
          <TestWritingCoach />
        </div>
      </div>
      
      <div className="text-center text-sm text-gray-500">
        <p>✅ Both examples should show sign-in forms initially</p>
        <p>✅ After signing in, they should provide AI responses using jean_memory MCP tool</p>
        <p>✅ Math tutor should act like a math tutor, writing coach like a writing coach</p>
        <p>✅ Responses should be intelligent and contextual (not generic acknowledgments)</p>
      </div>
    </div>
  );
}