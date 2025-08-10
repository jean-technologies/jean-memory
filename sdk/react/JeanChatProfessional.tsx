/**
 * JeanChat - Professional UI that looks exactly like assistant-ui
 * Uses Jean Memory backend with a pixel-perfect assistant-ui design
 */
import React, { useState, useEffect, useRef } from 'react';
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
    <div className="flex items-center justify-center h-full bg-gray-50">
      <div className="w-full max-w-sm p-6 bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="text-center mb-6">
          <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-3">
            <span className="text-lg">🧠</span>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Jean Memory</h2>
          <p className="text-sm text-gray-600">Sign in to continue</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Email"
            />
          </div>
          
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Password"
            />
          </div>
          
          {error && (
            <div className="p-2 bg-red-50 border border-red-200 rounded text-red-600 text-xs">
              {error}
            </div>
          )}
          
          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="w-full bg-black text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Signing in...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
};

export const JeanChat: React.FC<JeanChatProps> = ({ 
  apiKey, 
  systemPrompt = 'You are a helpful assistant', 
  clientName = 'claude',
  className = "h-96 w-full"
}) => {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const agent = useJeanAgent({ apiKey, systemPrompt, clientName });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [agent.messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || agent.isLoading) return;

    const message = inputMessage.trim();
    setInputMessage('');

    try {
      await agent.sendMessage(message);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
  };

  const handleAuthenticate = async (email: string, password: string) => {
    await agent.signIn(email, password);
  };

  // Show sign-in form if not authenticated
  if (!agent.isAuthenticated) {
    return (
      <div className={className}>
        <SignInForm
          onAuthenticate={handleAuthenticate}
          isLoading={agent.isLoading}
          error={agent.error}
        />
      </div>
    );
  }

  // Main chat interface - Modern shadcn-inspired design
  return (
    <div className={`flex flex-col bg-background border border-border rounded-lg overflow-hidden ${className}`} style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      
      {agent.messages.length === 0 ? (
        // Welcome state - Modern shadcn style
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-gradient-to-b from-background to-muted/50">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-3">How can I help you today?</h2>
            <p className="text-muted-foreground text-sm max-w-md mx-auto">I'm your personalized AI assistant with access to your conversation history and preferences.</p>
          </div>
          
          {/* Suggestion cards */}
          <div className="w-full max-w-xl space-y-3">
            {[
              { icon: "💡", text: "What can you help me with?", desc: "Explore my capabilities" },
              { icon: "📋", text: "Tell me about my recent activities", desc: "Review your history" },
              { icon: "📅", text: "Help me plan my day", desc: "Get organized" }
            ].map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion.text)}
                className="w-full p-4 text-left bg-card hover:bg-accent/50 border border-border hover:border-border/80 rounded-xl transition-all duration-200 group"
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg">{suggestion.icon}</span>
                  <div className="flex-1">
                    <p className="font-medium text-foreground text-sm mb-1">{suggestion.text}</p>
                    <p className="text-muted-foreground text-xs">{suggestion.desc}</p>
                  </div>
                  <svg className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        // Messages - Modern chat design
        <div className="flex-1 overflow-y-auto bg-background">
          <div className="max-w-4xl mx-auto p-4 space-y-6">
            {agent.messages.map((message, index) => (
              <div key={index} className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted border border-border'
                }`}>
                  {message.role === 'user' ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  )}
                </div>
                
                {/* Message content */}
                <div className={`flex-1 max-w-3xl ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                  <div className={`inline-block p-4 rounded-2xl ${
                    message.role === 'user' 
                      ? 'bg-primary text-primary-foreground rounded-br-md' 
                      : 'bg-muted border border-border rounded-bl-md'
                  }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </div>
                  </div>
                  <div className={`text-xs text-muted-foreground mt-2 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                    {message.timestamp.toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {agent.isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-full bg-muted border border-border flex items-center justify-center flex-shrink-0">
                  <svg className="w-4 h-4 text-muted-foreground animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="flex-1 max-w-3xl">
                  <div className="inline-block p-4 bg-muted border border-border rounded-2xl rounded-bl-md">
                    <div className="flex items-center gap-2 text-muted-foreground text-sm">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Input Area - Modern shadcn style */}
      <div className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4">
        {agent.error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
            {agent.error}
          </div>
        )}
        
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative">
            <div className="flex items-end gap-3 p-3 bg-background border border-border rounded-2xl focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/20 transition-all">
              <button
                type="button"
                className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded-lg hover:bg-accent/50"
                title="Attach file"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
              </button>
              
              <div className="flex-1 min-h-[40px] flex items-center">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Type your message..."
                  disabled={agent.isLoading}
                  rows={1}
                  className="w-full bg-transparent border-0 resize-none text-sm placeholder-muted-foreground focus:outline-none max-h-32"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  style={{ minHeight: '24px' }}
                />
              </div>
              
              <button
                type="submit"
                disabled={agent.isLoading || !inputMessage.trim()}
                className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                title="Send message"
              >
                {agent.isLoading ? (
                  <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin"></div>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default JeanChat;