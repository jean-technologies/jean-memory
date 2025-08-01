"use client";

import { useState } from "react";
import KnowledgeGraph from "./components/KnowledgeGraph";
import AdvancedKnowledgeGraph from "./components/AdvancedKnowledgeGraph";
// import ChatInterface from "./components/ChatInterface";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { MessageSquare, Network, Map, RotateCcw, Sparkles } from "lucide-react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
/*
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
*/

export default function MyLifePage() {
  const [selectedMemory, setSelectedMemory] = useState<string | null>(null);
  const [mobileView, setMobileView] = useState<"graph" | "chat">("graph");
  const [isChatOpen, setIsChatOpen] = useState(true);

  return (
    <ProtectedRoute>
      <div className="h-[calc(100vh-3.5rem)] lg:h-[calc(100vh-3.5rem)] flex bg-background text-foreground">
      {/* Main Content Area */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Main Content Section */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          className="flex-1 relative overflow-hidden"
        >
          <AdvancedKnowledgeGraph onMemorySelect={setSelectedMemory} />
        </motion.div>
      </div>

      {/* Chat Interface Section */}
      {/*
      <div className={`
        ${mobileView === "chat" ? "flex" : "hidden"}
        lg:flex
      `}>
        <Collapsible
          open={isChatOpen}
          onOpenChange={setIsChatOpen}
          className="h-full"
        >
          <CollapsibleContent className="h-full">
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={`
                flex flex-col bg-card
                w-full lg:w-[400px] xl:w-[500px]
                h-[calc(100vh-7rem)] lg:h-full
              `}
            >
              <ChatInterface selectedMemory={selectedMemory} />
            </motion.div>
          </CollapsibleContent>
          <div className="hidden lg:flex items-center justify-center p-2 h-full border-l border-border bg-background">
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm">
                  <MessageSquare className={`h-4 w-4 transition-transform duration-300 ${isChatOpen ? 'rotate-90' : ''}`} />
                </Button>
              </CollapsibleTrigger>
          </div>
        </Collapsible>
      </div>
      */}
      </div>
    </ProtectedRoute>
  );
} 