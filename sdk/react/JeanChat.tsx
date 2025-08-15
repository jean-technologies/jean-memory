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
  style?: React.CSSProperties;
}

export function JeanChat({ 
  className = '', 
  showHeader = true,
  placeholder = 'Type your message...',
  style
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
      <div className={`flex items-center justify-center h-full ${className} bg-white dark:bg-gray-950`} style={style}>
        <div className="text-center p-8 max-w-sm w-full">
          <div className="w-12 h-12 mx-auto mb-6 rounded-full bg-gray-50 dark:bg-gray-900 flex items-center justify-center border border-gray-100 dark:border-gray-800">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z" 
                    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                    className="text-gray-400 dark:text-gray-500"/>
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Connect to Jean Memory</h3>
          <p className="text-gray-500 dark:text-gray-400 text-sm mb-8 leading-relaxed">
            Sign in to access your personalized AI assistant with persistent memory.
          </p>
          <button 
            onClick={agent.signIn}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-sm rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-900 dark:focus:ring-gray-300 focus:ring-offset-2"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z" 
                    stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span>Sign In</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex flex-col h-full bg-white dark:bg-gray-950 ${className}`} style={style}>
      {showHeader && (
        <div className="flex justify-between items-center px-5 py-4 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
              <Bot size={16} className="text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white text-sm">Jean Memory</h3>
              <p className="text-xs text-gray-500 dark:text-gray-500">{agent.user?.email}</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setIsDark(!isDark)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900 rounded-lg transition-colors"
            >
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button
              onClick={() => window.location.reload()}
              disabled={agent.messages.length === 0}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Clear Conversation"
            >
              <Trash2 size={16} />
            </button>
            <button
              onClick={agent.signOut}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-gray-50 dark:hover:bg-gray-900 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {agent.messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-gray-50 dark:bg-gray-900 flex items-center justify-center mb-4">
               <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400 dark:text-gray-500">
                <path d="M12 2L13.09 8.26L20 9L13.09 15.74L12 22L10.91 15.74L4 9L10.91 8.26L12 2Z"></path>
              </svg>
            </div>
            <h3 className="text-base font-medium text-gray-900 dark:text-white mb-2">How can I help you today?</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs">
              I have access to your personal context and can assist with a wide range of topics.
            </p>
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto">
            {agent.messages.map((message: any) => (
              <div
                key={message.id}
                className={`flex items-start gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-900 flex items-center justify-center flex-shrink-0">
                  {message.role === 'user' ? (
                    <User size={14} className="text-gray-600 dark:text-gray-400" />
                  ) : (
                    <Bot size={14} className="text-gray-600 dark:text-gray-400" />
                  )}
                </div>
                <div className={`flex-1 max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div
                    className={`inline-block px-4 py-3 rounded-xl ${
                      message.role === 'user'
                        ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900'
                        : 'bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 border border-gray-100 dark:border-gray-800'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">
                      {message.content}
                    </p>
                  </div>
                  <div className={`mt-1.5 px-1 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                    <span className="text-xs text-gray-400 dark:text-gray-500">
                      {message.timestamp.toLocaleTimeString([], { 
                        hour: 'numeric', 
                        minute: '2-digit' 
                      })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            
            {agent.isLoading && (
              <div className="flex items-start gap-3 max-w-3xl mx-auto">
                <div className="w-7 h-7 rounded-full bg-gray-100 dark:bg-gray-900 flex items-center justify-center flex-shrink-0">
                  <Bot size={14} className="text-gray-600 dark:text-gray-400" />
                </div>
                <div className="bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 px-4 py-3 rounded-xl border border-gray-100 dark:border-gray-800">
                  <div className="flex items-center space-x-1">
                    <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="border-t border-gray-100 dark:border-gray-800 p-4">
        {agent.error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 rounded-lg flex items-start space-x-3">
            <div className="text-red-500 dark:text-red-400 mt-0.5">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
            </div>
            <div className="flex-1">
              <p className="text-red-600 dark:text-red-400 text-sm">{agent.error}</p>
            </div>
            <button 
              onClick={() => window.location.reload()} 
              className="p-1 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/50 rounded"
            >
              <X size={14}/>
            </button>
          </div>
        )}
        <form onSubmit={handleSubmit} className="relative max-w-3xl mx-auto">
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
            className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-1 focus:ring-gray-300 dark:focus:ring-gray-600 focus:border-transparent disabled:opacity-50 resize-none text-sm text-gray-900 dark:text-gray-100"
            rows={1}
          />
          <button
            type="submit"
            disabled={agent.isLoading || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            {agent.isLoading ? (
              <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Send size={14} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}