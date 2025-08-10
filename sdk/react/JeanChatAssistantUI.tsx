/**
 * JeanChat - Proper Assistant-UI Integration
 * Uses assistant-ui's Thread component with Jean Memory runtime adapter
 */
import React, { useState } from 'react';
import { AssistantRuntimeProvider, useLocalRuntime } from '@assistant-ui/react';
import { Thread } from '@assistant-ui/react-ui';
import { useJeanAgent } from './useJeanAgent';

interface JeanChatProps {
  apiKey: string;
  systemPrompt?: string;
  clientName?: string;
  className?: string;
}

interface SignInFormProps {
  onAuthenticate: (email: string, password: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

const SignInForm: React.FC<SignInFormProps> = ({ onAuthenticate, isLoading, error }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onAuthenticate(email, password);
  };

  return (
    <div className="flex items-center justify-center h-full">
      <div className="w-full max-w-md p-8 bg-white rounded-xl shadow-lg border border-gray-200">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <span className="text-xl">🧠</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-1">Jean Memory Assistant</h2>
          <p className="text-sm text-gray-600">Sign in to start chatting</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1.5">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              placeholder="your@email.com"
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1.5">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              placeholder="••••••••"
            />
          </div>
          
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}
          
          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="w-full bg-blue-600 text-white py-2.5 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Adapter to connect Jean Memory to assistant-ui runtime
const createJeanMemoryAdapter = (jeanAgent: ReturnType<typeof useJeanAgent>) => {
  return {
    async run(options: any) {
      const { messages } = options;
      const lastMessage = messages[messages.length - 1];
      
      if (lastMessage?.role === 'user') {
        // Extract text content from the last user message
        const textContent = lastMessage.content?.find((part: any) => part.type === 'text')?.text || '';
        
        if (textContent) {
          const response = await jeanAgent.sendMessage(textContent);
          return {
            content: [{ type: 'text', text: response }],
          };
        }
      }
      
      return {
        content: [{ type: 'text', text: 'Hello! How can I help you today?' }],
      };
    },
  };
};

export const JeanChat: React.FC<JeanChatProps> = ({ 
  apiKey, 
  systemPrompt = 'You are a helpful assistant', 
  clientName = 'claude',
  className = "h-96 w-full"
}) => {
  const jeanAgent = useJeanAgent({ apiKey, systemPrompt, clientName });

  const handleAuthenticate = async (email: string, password: string) => {
    await jeanAgent.signIn(email, password);
  };

  // Show sign-in form if not authenticated
  if (!jeanAgent.isAuthenticated) {
    return (
      <div className={className}>
        <SignInForm
          onAuthenticate={handleAuthenticate}
          isLoading={jeanAgent.isLoading}
          error={jeanAgent.error}
        />
      </div>
    );
  }

  // Create the runtime adapter
  const adapter = createJeanMemoryAdapter(jeanAgent);
  const runtime = useLocalRuntime(adapter);

  // Assistant-UI Thread component
  return (
    <div className={className}>
      <AssistantRuntimeProvider runtime={runtime}>
        <div className="h-full bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <Thread
            welcome={{
              message: "👋 Hello! I'm your Jean Memory assistant. I can help with a wide range of topics and remember our conversations for personalized assistance.",
              suggestions: [
                { prompt: "What can you help me with?" },
                { prompt: "Tell me about my recent activities" }, 
                { prompt: "Help me plan my day" },
                { prompt: "What do you remember about me?" }
              ]
            }}
          />
        </div>
      </AssistantRuntimeProvider>
    </div>
  );
};

export default JeanChat;