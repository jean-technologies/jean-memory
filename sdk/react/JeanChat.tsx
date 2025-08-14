/**
 * Jean Memory React SDK - Chat Component
 * Complete chat interface with authentication
 */
import React, { useState, useRef, useEffect } from 'react';
import { useJean } from './provider';
import { SignInWithJean } from './SignInWithJean';
import { User, Bot, Send, LogOut, Trash2, X, Sun, Moon } from 'lucide-react';

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
  const [isDark, setIsDark] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [agent.messages]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedTheme = localStorage.getItem('jean-chat-theme');
      if (storedTheme === 'dark') {
        setIsDark(true);
      }
    }
  }, []);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('jean-chat-theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('jean-chat-theme', 'light');
    }
  }, [isDark]);

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

  if (!agent.isAuthenticated) {
    return (
      <div className={`flex items-center justify-center h-full ${className} bg-gray-50 dark:bg-gray-900`}>
        <div className="text-center p-8 max-w-md w-full">
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-white dark:bg-gray-800 flex items-center justify-center border border-gray-200 dark:border-gray-700">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z" 
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                    className="text-gray-600 dark:text-gray-400"/>
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Connect with Jean Memory</h3>
          <p className="text-gray-600 dark:text-gray-400 text-sm mb-6">
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
    <div className={`flex flex-col h-full bg-white dark:bg-gray-900 text-gray-900 dark:text-white ${className}`}>
      {showHeader && (
        <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center">
              <Bot size={20} className="text-white" />
            </div>
            <div>
              <h3 className="font-semibold">Jean Memory Assistant</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">Connected as {agent.user?.email}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full transition-colors"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              onClick={agent.clearConversation}
              disabled={agent.messages.length === 0}
              className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-full disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="Clear Conversation"
            >
              <Trash2 size={16} />
            </button>
            <button
              onClick={agent.signOut}
              className="p-2 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/50 rounded-full transition-colors"
              title="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {agent.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
            <div className="w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
               <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400 dark:text-gray-500">
                <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z"></path>
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-1">Start a conversation</h3>
            <p className="text-sm max-w-sm">
              Ask me anything! I have access to your personal context and can help with a wide range of topics.
            </p>
          </div>
        ) : (
          <>
            {agent.messages.map((message: any) => (
              <div
                key={message.id}
                className={`flex items-start gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role !== 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center flex-shrink-0">
                    <Bot size={18} className="text-white" />
                  </div>
                )}
                <div className={`max-w-[80%]`}>
                  <div
                    className={`px-4 py-2.5 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white rounded-br-lg'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-lg'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {message.content}
                    </p>
                  </div>
                   <div className={`mt-1.5 px-1 ${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {message.timestamp.toLocaleTimeString([], { 
                        hour: 'numeric', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                </div>
                 {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                    <User size={18} className="text-gray-600 dark:text-gray-300" />
                  </div>
                )}
              </div>
            ))}
            
            {agent.isLoading && (
              <div className="flex items-start gap-3 justify-start">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center flex-shrink-0">
                  <Bot size={18} className="text-white" />
                </div>
                <div className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-4 py-2.5 rounded-2xl rounded-bl-lg">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800">
        {agent.error && (
          <div className="mb-3 p-3 bg-red-100 dark:bg-red-900/30 border border-red-200 dark:border-red-800/50 rounded-lg flex items-start space-x-3">
            <div className="text-red-600 dark:text-red-400 mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-red-700 dark:text-red-300 text-sm font-medium">Error</p>
              <p className="text-red-600 dark:text-red-400 text-sm">{agent.error}</p>
            </div>
            <button 
              onClick={() => agent.setError(null)} 
              className="p-1 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 rounded-full"
            >
              <X size={16}/>
            </button>
          </div>
        )}
        <form onSubmit={handleSubmit} className="relative">
          <textarea
            value={input}
            onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
            onKeyDown={(e: React.KeyboardEvent<HTMLTextAreaElement>) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e as any);
              }
            }}
            placeholder={placeholder}
            disabled={agent.isLoading}
            className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 resize-none text-sm"
            rows={1}
          />
          <button
            type="submit"
            disabled={agent.isLoading || !input.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {agent.isLoading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Send size={16} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}