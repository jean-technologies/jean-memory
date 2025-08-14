/**
 * Jean Memory React SDK - Example React Chatbot
 * Complete 5-line integration example
 */
import React from 'react';
import { JeanProvider, JeanChat } from '@jeanmemory/react';

// Replace with your actual API key
const JEAN_API_KEY = process.env.REACT_APP_JEAN_API_KEY || "jean_sk_your_api_key_here";

function App() {
  // 🎯 5-line Jean Memory integration
  return (
    <JeanProvider apiKey={JEAN_API_KEY}>
      <div style={{ height: '100vh' }}>
        <JeanChat />
      </div>
    </JeanProvider>
  );
}

export default App;