"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Send, Sparkles, Brain, MessageSquare, Plus, Search, BookOpen, Shield } from "lucide-react";
import Link from "next/link";
import { useToast } from "@/hooks/use-toast";

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  action?: 'add_memory' | 'search_memory' | 'ask_memory';
}

interface SuggestionCard {
  title: string;
  description: string;
  action: () => void;
  icon: React.ReactNode;
}

export default function TestPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [sessionStats, setSessionStats] = useState({ memoryCount: 0, operationCount: 0 });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Sample suggestions for users to try
  const suggestions: SuggestionCard[] = [
    {
      title: "Add a Memory",
      description: "Store information about yourself",
      icon: <Plus className="w-4 h-4" />,
      action: () => setInput("Remember that I love hiking and spending time outdoors on weekends")
    },
    {
      title: "Search Memories", 
      description: "Find specific information",
      icon: <Search className="w-4 h-4" />,
      action: () => setInput("Search for information about my hobbies")
    },
    {
      title: "Ask Questions",
      description: "Query your stored memories",
      icon: <MessageSquare className="w-4 h-4" />,
      action: () => setInput("What do you know about my interests?")
    },
    {
      title: "Add Work Info",
      description: "Store professional details",
      icon: <BookOpen className="w-4 h-4" />,
      action: () => setInput("I work as a software engineer and love building AI applications")
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Generate sessionId on client side to avoid hydration mismatch
  useEffect(() => {
    if (!sessionId) {
      setSessionId(`test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
    }
  }, [sessionId]);

  // Add welcome message after component mounts to avoid hydration issues
  useEffect(() => {
    if (messages.length === 0) {
      addMessage("👋 Welcome to Jean Memory! This is a live demo where you can test our memory functionality. Try adding memories, searching them, or asking questions.", 'system');
    }
  }, [messages.length]);

  const addMessage = (content: string, type: Message['type'], action?: Message['action']) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date(),
      action
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleTestMemoryAction = async (action: string, input: string) => {
    if (!sessionId) return; // Don't make API calls until sessionId is ready
    
    setIsLoading(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/test/memory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          input,
          sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        addMessage(data.result, 'assistant', action as Message['action']);
        
        // Update session stats
        if (data.sessionInfo) {
          setSessionStats({
            memoryCount: data.sessionInfo.memoryCount || 0,
            operationCount: sessionStats.operationCount + 1
          });
        }
        
        toast({
          title: "Success",
          description: `Memory ${action.replace('_', ' ')} completed successfully!`,
        });
      } else {
        addMessage(`Error: ${data.error}`, 'assistant');
        toast({
          title: "Error",
          description: data.error,
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('Error:', error);
      addMessage("Sorry, there was an error processing your request. This is just a demo - the full version is much more reliable!", 'assistant');
      toast({
        title: "Error",
        description: "Failed to process request. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !sessionId) return;

    const userInput = input.trim();
    addMessage(userInput, 'user');
    setInput("");

    // Determine action based on input keywords
    let action = 'ask_memory'; // default
    if (userInput.toLowerCase().includes('remember') || userInput.toLowerCase().includes('store') || userInput.toLowerCase().includes('add')) {
      action = 'add_memory';
    } else if (userInput.toLowerCase().includes('search') || userInput.toLowerCase().includes('find')) {
      action = 'search_memory';
    }

    await handleTestMemoryAction(action, userInput);
  };

  const handleSuggestionClick = (suggestion: SuggestionCard) => {
    suggestion.action();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-800">
      {/* Header */}
      <div className="border-b border-zinc-800 bg-black/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Brain className="w-8 h-8 text-purple-400" />
                <span className="text-xl font-bold text-white">Jean Memory</span>
              </div>
              <div className="hidden sm:flex items-center space-x-4 text-sm text-zinc-400">
                <span>{sessionStats.memoryCount} memories stored</span>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm" asChild>
                <Link href="/">← Back to Home</Link>
              </Button>
              <Button size="sm" asChild className="bg-purple-600 hover:bg-purple-700">
                <Link href="/auth">Get Started Free</Link>
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Suggestions Panel */}
          <div className="lg:col-span-1">
            <Card className="bg-zinc-900/50 border-zinc-700 sticky top-24">
              <CardHeader>
                <CardTitle className="text-white flex items-center space-x-2">
                  <Sparkles className="w-5 h-5 text-yellow-400" />
                  <span>Quick Start</span>
                </CardTitle>
                <CardDescription>Click any suggestion to get started</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {suggestions.map((suggestion, index) => (
                  <motion.button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="w-full p-3 text-left bg-zinc-800/50 hover:bg-zinc-700/50 border border-zinc-600 rounded-lg transition-colors"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    disabled={isLoading || !sessionId}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="text-purple-400 mt-0.5">
                        {suggestion.icon}
                      </div>
                      <div>
                        <div className="text-white font-medium text-sm">{suggestion.title}</div>
                        <div className="text-zinc-400 text-xs mt-1">{suggestion.description}</div>
                      </div>
                    </div>
                  </motion.button>
                ))}
              </CardContent>
            </Card>

            {/* Privacy Notice */}
            <Card className="bg-green-900/20 border-green-700/50 mt-6">
              <CardHeader>
                <CardTitle className="text-green-300 text-sm flex items-center space-x-2">
                  <Shield className="w-4 h-4" />
                  <span>Privacy Guaranteed</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-green-200">
                <div>• Your data is completely private</div>
                <div>• Never shared, sold, or given away</div>
                <div>• Automatically deleted after sessions</div>
                <div>• Enterprise-grade security</div>
              </CardContent>
            </Card>

          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <Card className="bg-zinc-900/30 border-zinc-700/50 h-[70vh] flex flex-col">
              <CardHeader className="flex-shrink-0 pb-3">
                <CardTitle className="text-white text-lg">Memory Assistant</CardTitle>
                <CardDescription className="text-sm text-zinc-400">
                  {sessionId ? `Session: ${sessionId.split('_')[1]}` : 'Loading...'}
                </CardDescription>
              </CardHeader>
              
              {/* Messages */}
              <CardContent className="flex-1 overflow-hidden p-0">
                <div className="h-full overflow-y-auto p-6 space-y-4">
                  <AnimatePresence>
                    {messages.map((message) => (
                      <motion.div
                        key={message.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[85%] p-3 rounded-xl ${
                          message.type === 'user' 
                            ? 'bg-purple-600 text-white ml-auto' 
                            : message.type === 'system'
                            ? 'bg-blue-500/10 border border-blue-500/20 text-blue-200'
                            : 'bg-zinc-800/80 text-white'
                        }`}>
                          <div className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</div>
                          <div className="text-xs opacity-60 mt-2 flex justify-between items-center">
                            <span>{message.timestamp.toLocaleTimeString()}</span>
                            {message.action && (
                              <span className="text-xs opacity-50">
                                {message.action.replace('_', ' ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  {isLoading && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex justify-start"
                    >
                      <div className="bg-zinc-700 text-white p-3 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className="animate-spin w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full"></div>
                          <span className="text-sm">Processing...</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              </CardContent>

              {/* Input */}
              <div className="border-t border-zinc-700/50 p-4">
                <form onSubmit={handleSubmit} className="flex space-x-3">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question or add a memory..."
                    className="flex-1 bg-zinc-800/50 border-zinc-600/50 text-white placeholder:text-zinc-400 focus:border-purple-500/50"
                    disabled={isLoading}
                  />
                  <Button 
                    type="submit" 
                    disabled={isLoading || !input.trim() || !sessionId}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </form>
              </div>
            </Card>
          </div>
        </div>


      </div>
    </div>
  );
} 