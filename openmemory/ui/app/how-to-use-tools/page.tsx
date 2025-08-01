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
    description: "Quick keyword search through your memories",
    example: "search_memory: 'project goals'"
  },
  {
    name: "ask_memory", 
    description: "Simple questions about your stored memories",
    example: "ask_memory: 'What are my preferences?'"
  },
  {
    name: "add_memories",
    description: "Manually store specific information",
    example: "add_memories: 'Met with John about Q3 goals'"
  },
  {
    name: "list_memories",
    description: "Browse through stored memories",
    example: "list_memories"
  },
  {
    name: "deep_memory_query",
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
        <ParticleNetwork id="how-to-use-particles" className="h-full w-full" interactive={true} particleCount={80} />
      </div>
      <div className="absolute inset-0 bg-gradient-to-b from-background/30 via-background/80 to-background z-5" />
      
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
                <Card className={`${tool.isHighlighted ? 'bg-card border-l-4 border-l-foreground/20' : 'bg-card'} hover:bg-card/80 transition-colors duration-200`}>
                  <CardHeader>
                    <div>
                      <CardTitle className="flex items-center gap-2 font-mono text-lg mb-2">
                        {tool.name}
                        {tool.badge && (
                          <Badge variant="outline" className="text-xs">
                            {tool.badge}
                          </Badge>
                        )}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">{tool.description}</p>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <p className="text-xs text-muted-foreground">Examples:</p>
                      {tool.examples.map((example, i) => (
                        <div key={i} className="bg-muted/30 rounded p-3">
                          <pre className="text-xs text-foreground/70 overflow-x-auto">
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
                <CardTitle className="text-lg">
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
                        <div className="mb-2">
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
                <div className="flex items-center justify-between">
                  <div>
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