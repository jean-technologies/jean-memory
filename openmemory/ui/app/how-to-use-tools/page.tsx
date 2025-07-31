"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BotMessageSquare, BrainCircuit, Search, List, Wand2, ArrowRight, Lightbulb, FileText, ChevronDown, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import { Badge } from "@/components/ui/badge";
import { RequestFeatureModal } from "@/components/tools/RequestFeatureModal";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

const primaryTools = [
  {
    name: "jean_memory",
    icon: <BrainCircuit className="w-7 h-7 text-blue-600 dark:text-blue-400" />,
    description: "The intelligent memory layer that automatically learns from every conversation and provides relevant context when you need it. Simply use this tool and Jean Memory handles everything else.",
    examples: [
      "jean_memory: 'I just finished my morning workout' (is_new_conversation: true)",
      "jean_memory: 'What did I work on yesterday?' (needs_context: true)",
      "jean_memory: 'I prefer dark mode in my apps' (is_new_conversation: false)"
    ],
    badge: "Primary",
    isHighlighted: true
  },
  {
    name: "store_document",
    icon: <FileText className="w-6 h-6 text-gray-700 dark:text-gray-300" />,
    description: "Store large documents, files, or lengthy content. Perfect for saving meeting notes, documentation, or articles for future reference.",
    examples: [
      'store_document: { title: "Meeting Notes", content: "..." }'
    ],
    badge: "Documents"
  }
];

const otherTools = [
  {
    name: "search_memory",
    icon: <Search className="w-6 h-6 text-gray-500" />,
    description: "Quick keyword search through your memories",
    example: "search_memory: 'project goals'"
  },
  {
    name: "ask_memory", 
    icon: <BrainCircuit className="w-6 h-6 text-gray-500" />,
    description: "Simple questions about your stored memories",
    example: "ask_memory: 'What are my preferences?'"
  },
  {
    name: "add_memories",
    icon: <BotMessageSquare className="w-6 h-6 text-gray-500" />,
    description: "Manually store specific information",
    example: "add_memories: 'Met with John about Q3 goals'"
  },
  {
    name: "list_memories",
    icon: <List className="w-6 h-6 text-gray-500" />,
    description: "Browse through stored memories",
    example: "list_memories"
  },
  {
    name: "deep_memory_query",
    icon: <Wand2 className="w-6 h-6 text-gray-500" />,
    description: "Complex analysis across all memories",
    example: "Tell me everything about my work patterns"
  }
];

export default function HowToUsePage() {
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [isOtherToolsOpen, setIsOtherToolsOpen] = useState(false);

  return (
    <ProtectedRoute>
      <div className="relative min-h-screen w-full bg-background">
      <div className="absolute inset-0 z-0 h-full w-full">
        <ParticleNetwork id="how-to-use-particles" className="h-full w-full" interactive={false} particleCount={120} />
      </div>
      <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background/70 to-background z-5" />
      
      <div className="relative z-10 container mx-auto px-4 py-16 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
            Jean Memory
          </h1>
          <p className="mt-4 text-lg text-muted-foreground max-w-3xl mx-auto">
            An agentic memory layer that learns from your conversations and provides intelligent context. Simply use these tools and Jean Memory handles the rest.
          </p>
        </motion.div>

        <div className="space-y-8">
          {/* Primary Tools Section */}
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-center text-foreground mb-6">
              Essential Tools
            </h2>
            
            {primaryTools.map((tool, index) => (
              <motion.div
                key={tool.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 * (index + 1) }}
              >
                <Card className={`${tool.isHighlighted ? 'bg-card border-2 border-blue-200 dark:border-blue-800 shadow-lg' : 'bg-card'} hover:bg-card/80 transition-colors duration-200`}>
                  <CardHeader>
                    <div className="flex items-start gap-4">
                      <div className={`p-3 ${tool.isHighlighted ? 'bg-blue-50 dark:bg-blue-900/20' : 'bg-secondary'} rounded-md`}>{tool.icon}</div>
                      <div className="flex-1">
                        <CardTitle className="flex items-center gap-2 font-mono text-lg mb-2">
                          {tool.name}
                          <Badge variant={tool.isHighlighted ? "default" : "secondary"} className={`text-xs ${tool.isHighlighted ? 'bg-blue-600 text-white' : ''}`}>
                            {tool.badge}
                          </Badge>
                        </CardTitle>
                        <p className="text-sm text-muted-foreground">{tool.description}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <p className="text-xs text-muted-foreground">Examples:</p>
                      {tool.examples.map((example, i) => (
                        <div key={i} className="bg-muted/50 rounded p-3">
                          <pre className="text-xs text-foreground/80 overflow-x-auto">
                            <code>{example}</code>
                          </pre>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* How It Works Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Card className="bg-muted/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <BrainCircuit className="w-5 h-5 text-foreground" />
                  How Jean Memory Works
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-foreground rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <p className="font-medium text-sm">Always Learning</p>
                      <p className="text-xs text-muted-foreground">Every conversation automatically adds to your memory layer</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-foreground rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <p className="font-medium text-sm">Intelligent Context</p>
                      <p className="text-xs text-muted-foreground">Provides relevant context automatically based on your conversation</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-foreground rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <p className="font-medium text-sm">Adaptive Speed</p>
                      <p className="text-xs text-muted-foreground">Fast responses for quick questions, deep analysis for new conversations</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Collapsible Other Tools Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.6 }}
          >
            <Collapsible open={isOtherToolsOpen} onOpenChange={setIsOtherToolsOpen}>
              <CollapsibleTrigger asChild>
                <Card className="bg-card/50 hover:bg-card/70 transition-colors cursor-pointer border-dashed">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {isOtherToolsOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                        <CardTitle className="text-base">Additional Tools</CardTitle>
                      </div>
                      <p className="text-xs text-muted-foreground">Advanced functionality</p>
                    </div>
                  </CardHeader>
                </Card>
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-4 mt-4">
                <div className="grid gap-3">
                  {otherTools.map((tool, index) => (
                    <Card key={tool.name} className="bg-card/30 border-dashed">
                      <CardContent className="pt-4">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="p-1 bg-secondary/30 rounded">{tool.icon}</div>
                          <span className="font-mono text-sm font-medium">{tool.name}</span>
                        </div>
                        <p className="text-sm text-muted-foreground mb-2">{tool.description}</p>
                        <pre className="text-xs bg-secondary/30 p-2 rounded text-muted-foreground">
                          <code>{tool.example}</code>
                        </pre>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                <div className="mt-4 p-3 bg-muted/30 rounded">
                  <p className="text-xs text-muted-foreground text-center">
                    Most users only need <strong>jean_memory</strong> and <strong>store_document</strong>. 
                    These advanced tools are available when you need specific functionality.
                  </p>
                </div>
              </CollapsibleContent>
            </Collapsible>
          </motion.div>

          {/* Request Feature Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.8 }}
            onClick={() => setIsRequestModalOpen(true)}
            className="cursor-pointer"
          >
            <Card className="bg-card/50 hover:bg-card/70 transition-colors">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Lightbulb className="w-5 h-5 text-foreground" />
                  <div className="flex-1">
                    <CardTitle className="text-base">
                      Request a Tool or Feature
                    </CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">
                      Have an idea for a new tool or improvement? Let us know.
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-muted-foreground" />
                </div>
              </CardHeader>
            </Card>
          </motion.div>
        </div>
      </div>
      <RequestFeatureModal
        open={isRequestModalOpen}
        onOpenChange={setIsRequestModalOpen}
      />
    </div>
    </ProtectedRoute>
  );
} 