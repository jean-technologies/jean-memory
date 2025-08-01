"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const ChatBubble = ({ message, isUser, isPersonalized }: { message: string; isUser: boolean; isPersonalized?: boolean; }) => (
    <div className={`flex items-start gap-3 my-2 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className={`w-8 h-8 rounded-full flex-shrink-0 ${isPersonalized ? "bg-slate-500" : "bg-gray-400"}`}></div>
      )}
      <div
        className={`px-4 py-2 rounded-lg max-w-xs text-sm md:text-base ${
          isUser
            ? "bg-gray-700 text-white rounded-br-none"
            : "bg-gray-200 text-gray-800 rounded-bl-none"
        }`}
      >
        {message}
      </div>
    </div>
  );

const AppIcon = ({ src, alt }: { src: string; alt: string; }) => (
    <motion.div
        whileHover={{ scale: 1.1, y: -5 }}
        transition={{ type: "spring", stiffness: 300 }}
        className="bg-white p-3 rounded-full shadow-md"
    >
        <Image src={src} alt={alt} width={32} height={32} />
    </motion.div>
);

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState("developers");

  useEffect(() => {
    const params = new URLSearchParams(
      window.location.search + window.location.hash.substring(1)
    );
    if (params.get("code") || params.get("access_token")) {
      return;
    }
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-black">
        Loading...
      </div>
    );
  }

  const reactCode = `import { SignInWithJean, JeanChat, useJeanAgent } from '@jeanmemory/react';

function MathTutorApp() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a patient math tutor for a 10th grader."
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;

  return <JeanChat agent={agent} />;
}`;

  const primaryButtonClass = "px-8 py-6 text-lg bg-white/50 border border-gray-300 backdrop-blur-sm hover:bg-white/80";
  const secondaryButtonClass = "px-8 py-6 text-lg hover:bg-gray-200/50";

  return (
    <div className="relative min-h-screen bg-gray-50 text-gray-900 overflow-hidden">
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="landing-particles-final" particleColor="#cccccc" particleCount={150} />
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center w-full max-w-7xl mx-auto"
        >
          <motion.h1
            className="text-6xl sm:text-7xl md:text-8xl font-semibold mb-4 text-gray-900 tracking-tight"
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Jean
          </motion.h1>

          <motion.p
            className="text-xl sm:text-2xl text-gray-600 mb-10 max-w-3xl mx-auto"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            The universal memory across your applications
          </motion.p>
          
          <motion.div
              className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16 h-20" // Set fixed height
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.6 }}
            >
              {activeTab === 'users' ? (
                  <Link href={user ? "/dashboard" : "/auth?animate=true"} passHref>
                    <Button size="lg" variant="ghost" className={primaryButtonClass}>
                        {user ? "Go to Dashboard" : "Sign In With Jean"}
                    </Button>
                  </Link>
              ) : (
                <>
                  <Link href="https://calendly.com/jonathan-jeantechnologies/30min" passHref>
                    <Button size="lg" variant="ghost" className={primaryButtonClass}>
                      Request a Demo
                    </Button>
                  </Link>
                  <Link href={user ? "/dashboard" : "/auth?animate=true"} passHref>
                    <Button variant="ghost" size="lg" className={secondaryButtonClass}>
                        {user ? "Go to Dashboard" : "Sign In"}
                    </Button>
                  </Link>
                </>
              )}
          </motion.div>

          <Tabs defaultValue="developers" className="w-full" onValueChange={setActiveTab}>
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 mb-10 bg-gray-200/70 backdrop-blur-sm">
                <TabsTrigger value="users">For Users</TabsTrigger>
                <TabsTrigger value="developers">For Developers</TabsTrigger>
            </TabsList>

            <TabsContent value="users">
                <motion.div 
                    key="users"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                >
                    <div className="flex justify-center items-center space-x-4 md:space-x-6 mb-8">
                        <AppIcon src="/images/ChatGPT-Logo.svg" alt="ChatGPT Logo" />
                        <AppIcon src="/images/claude.webp" alt="Claude Logo" />
                        <AppIcon src="/images/notion.svg" alt="Notion Logo" />
                        <AppIcon src="/images/obsidian.svg" alt="Obsidian Logo" />
                        <AppIcon src="/images/substack.png" alt="Substack Logo" />
                        <AppIcon src="/images/vscode.svg" alt="VS Code Logo" />
                    </div>
                    <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-white/60 backdrop-blur-sm border border-gray-200 rounded-xl p-4">
                            <h3 className="text-xl font-bold mb-2 text-center text-gray-500">Generic AI</h3>
                            <div className="p-2 rounded-lg flex flex-col justify-end h-48">
                                <ChatBubble isUser={true} message="What should I work on today?" />
                                <ChatBubble isUser={false} message="You could work on tasks, check your calendar, or read emails. What are your priorities?" />
                            </div>
                        </div>
                        <div className="bg-white/60 backdrop-blur-sm border border-orange-300 rounded-xl p-4">
                            <h3 className="text-xl font-bold mb-2 text-center text-gray-900">Personalized with Jean</h3>
                            <div className="p-2 rounded-lg flex flex-col justify-end h-48">
                                <ChatBubble isUser={true} message="What should I work on today?" />
                                <ChatBubble isUser={false} message="Finalize the Q3 launch slides. You also wanted to practice Spanish. Start with that?" isPersonalized={true} />
                            </div>
                        </div>
                    </div>
                </motion.div>
            </TabsContent>
            
            <TabsContent value="developers">
                <motion.div 
                    key="developers"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                    className="max-w-4xl mx-auto"
                >
                    <h2 className="text-3xl font-bold text-center mb-4">
                        Instantly personalize with 5 lines of code
                    </h2>
                    <p className="text-lg text-gray-600 text-center mb-8 max-w-2xl mx-auto">
                        With the Jean SDK, you can add memory and personalization to any AI application.
                    </p>
                    <CodeBlock language="jsx" value={reactCode} />
                </motion.div>
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}
