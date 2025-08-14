/**
 * Jean Memory React SDK - Chat Component
 * Complete chat interface with authentication
 */
import React, { useState, useRef, useEffect } from 'react';
import { useJean } from './provider';
import { SignInWithJean } from './SignInWithJean';

interface JeanChatProps {
  className?: string;
  showHeader?: boolean;
  placeholder?: string;
}

export function JeanChat({ 
  className = '', 
  showHeader = true,
  placeholder = 'Type your message...'
}: JeanChatProps) {
  const agent = useJean();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [agent.messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || agent.isLoading) return;

    const message = input.trim();
    setInput('');

    try {
      await agent.sendMessage(message);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  // Show sign in if not authenticated
  if (!agent.isAuthenticated) {
    return (
      <div className={`flex items-center justify-center h-full ${className}`}>
        <div className="text-center p-8">
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gray-50 flex items-center justify-center border">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z" 
                    stroke="#636363" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Connect with Jean Memory</h3>
          <p className="text-gray-600 text-sm mb-6 max-w-sm">
            Access your personalized AI assistant with persistent memory across all your applications.
          </p>
          <SignInWithJean
            onSuccess={agent.setUser}
            apiKey={agent.apiKey}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Header */}
      {showHeader && (
        <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
              🧠
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Jean Memory Assistant</h3>
              <p className="text-xs text-gray-500">Connected as {agent.user?.email}</p>
            </div>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={agent.clearConversation}
              disabled={agent.messages.length === 0}
              className="px-3 py-1.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Clear
            </button>
            <button
              onClick={agent.signOut}
              className="px-3 py-1.5 text-xs font-medium bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {agent.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center mb-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                💬
              </div>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Start a conversation</h3>
            <p className="text-gray-500 text-sm max-w-sm">
              Ask me anything! I have access to your personal context and can help with a wide range of topics.
            </p>
          </div>
        ) : (
          <>
            {agent.messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] lg:max-w-[70%]`}>
                  <div className={`flex items-end space-x-2 ${
                    message.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
                  }`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {message.role === 'user' ? '👤' : '🧠'}
                    </div>
                    
                    <div
                      className={`px-4 py-2 rounded-2xl ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white rounded-br-md'
                          : 'bg-gray-100 text-gray-900 rounded-bl-md'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </p>
                    </div>
                  </div>
                  
                  <div className={`mt-1 px-10 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    <span className="text-xs text-gray-400">
                      {message.timestamp.toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {agent.isLoading && (
              <div className="flex justify-start">
                <div className="flex items-end space-x-2">
                  <div className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 flex items-center justify-center text-sm">
                    🧠
                  </div>
                  <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl rounded-bl-md">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-xs text-gray-500">Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        {agent.error && (
          <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600 text-sm">{agent.error}</p>
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex items-end space-x-3">
          <div className="flex-1 min-w-0">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              disabled={agent.isLoading}
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={agent.isLoading || !input.trim()}
            className="w-10 h-10 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {agent.isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}