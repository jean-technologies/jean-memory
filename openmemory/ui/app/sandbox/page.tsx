"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Send, MessageCircle, Sparkles, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface SandboxMessage {
  id: string;
  type: 'user' | 'system' | 'memory';
  content: string;
  timestamp: Date;
  memoryId?: string;
}

interface SandboxSession {
  session_token: string;
  user_id: string;
  expires_in: number;
}

export default function SandboxPage() {
  const [session, setSession] = useState<SandboxSession | null>(null);
  const [messages, setMessages] = useState<SandboxMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    createSandboxSession();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const createSandboxSession = async () => {
    try {
      setIsCreatingSession(true);
      const response = await fetch(`${API_URL}/api/v1/sandbox/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
      }

      const sessionData: SandboxSession = await response.json();
      setSession(sessionData);
      
      // Add welcome message
      setMessages([
        {
          id: 'welcome',
          type: 'system',
          content: 'Welcome to Jean Memory! Share information about yourself to build your memory, then ask questions to test recall.',
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      console.error('Error creating sandbox session:', error);
      setMessages([
        {
          id: 'error',
          type: 'system',
          content: '❌ Failed to create sandbox session. Please try refreshing the page.',
          timestamp: new Date()
        }
      ]);
    } finally {
      setIsCreatingSession(false);
    }
  };

  const addMemory = async (text: string) => {
    if (!session) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/sandbox/memories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.session_token}`,
        },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add memory: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Add success message
      const successMessage: SandboxMessage = {
        id: `memory-${Date.now()}`,
        type: 'memory',
        content: `✓ Remembered: "${result.content}"`,
        timestamp: new Date(),
        memoryId: result.id
      };

      setMessages(prev => [...prev, successMessage]);

    } catch (error) {
      console.error('Error adding memory:', error);
              const errorMessage: SandboxMessage = {
          id: `error-${Date.now()}`,
          type: 'system',
          content: 'Failed to save memory. Please try again.',
          timestamp: new Date()
        };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const searchMemories = async (query: string) => {
    if (!session) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/sandbox/search?query=${encodeURIComponent(query)}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${session.session_token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to search memories: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.results && result.results.length > 0) {
        const searchResults = result.results.map((r: any) => r.memory || r.content).join('\n• ');
        const resultsMessage: SandboxMessage = {
          id: `search-${Date.now()}`,
          type: 'memory',
          content: `Found ${result.results.length} memories:\n• ${searchResults}`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, resultsMessage]);
      } else {
        const noResultsMessage: SandboxMessage = {
          id: `no-results-${Date.now()}`,
          type: 'system',
          content: 'No memories found. Try adding some information first.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, noResultsMessage]);
      }

    } catch (error) {
      console.error('Error searching memories:', error);
              const errorMessage: SandboxMessage = {
          id: `search-error-${Date.now()}`,
          type: 'system',
          content: 'Search failed. Please try again.',
          timestamp: new Date()
        };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !session || isLoading) return;

    const userMessage: SandboxMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    // Determine if this is a search or memory addition
    const isSearchQuery = inputText.toLowerCase().includes('what') || 
                         inputText.toLowerCase().includes('find') || 
                         inputText.toLowerCase().includes('search') ||
                         inputText.toLowerCase().includes('remember') ||
                         inputText.toLowerCase().includes('recall');

    try {
      if (isSearchQuery) {
        await searchMemories(inputText);
      } else {
        await addMemory(inputText);
      }
    } finally {
      setInputText("");
      setIsLoading(false);
    }
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user':
        return '•';
      case 'memory':
        return '•';
      case 'system':
        return '•';
      default:
        return '•';
    }
  };

  const getMessageBgColor = (type: string) => {
    switch (type) {
      case 'user':
        return 'bg-blue-500/10 border-blue-500/20';
      case 'memory':
        return 'bg-green-500/10 border-green-500/20';
      case 'system':
        return 'bg-purple-500/10 border-purple-500/20';
      default:
        return 'bg-gray-500/10 border-gray-500/20';
    }
  };

  if (isCreatingSession) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-lg">Creating your sandbox session...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="border-b border-white/10 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span>Back to Home</span>
            </Link>
            <div className="h-6 w-px bg-white/20" />
            <div className="flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-400" />
              <h1 className="text-xl font-bold">Jean Memory Sandbox</h1>
            </div>
          </div>
          <div className="text-sm text-gray-400">
            Session expires in {session ? Math.round((session.expires_in) / 3600) : 0} hours
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="max-w-4xl mx-auto p-4 h-[calc(100vh-120px)] flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 mb-4">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-lg border ${getMessageBgColor(message.type)}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-xl">{getMessageIcon(message.type)}</span>
                <div className="flex-1">
                  <div className="text-sm text-gray-400 mb-1">
                    {message.type === 'user' ? 'You' : message.type === 'memory' ? 'Memory System' : 'System'}
                    <span className="ml-2">{message.timestamp.toLocaleTimeString()}</span>
                  </div>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            </motion.div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Share information or ask questions..."
            className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isLoading}
            className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed rounded-lg transition-all duration-200 flex items-center gap-2"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>

        {/* Help Text */}
        <div className="mt-4 text-center text-sm text-gray-500">
          <p>Share information to build memory • Ask questions to test recall</p>
        </div>
      </div>
    </div>
  );
} 