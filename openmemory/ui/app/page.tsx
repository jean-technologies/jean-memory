"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import { cn } from "@/lib/utils";

const ChatBubble = ({ message, isUser, isPersonalized }: { message: string; isUser: boolean; isPersonalized?: boolean; }) => (
    <div className={`flex items-start gap-3 my-2 ${isUser ? "justify-end" : ""}`}>
      {!isUser && (
        <div className={`w-8 h-8 rounded-full flex-shrink-0 ${isPersonalized ? "bg-slate-400" : "bg-gray-400"}`}></div>
      )}
      <div className="min-w-0"> 
        <div
          className={`px-4 py-2 rounded-lg max-w-xs text-sm inline-block break-words ${
            isUser
              ? "bg-gray-800 text-white rounded-br-none"
              : "bg-gray-200 text-gray-800 rounded-bl-none"
          }`}
        >
          {message}
        </div>
      </div>
    </div>
  );

const AppIcon = ({ src, alt }: { src: string; alt: string; }) => (
    <motion.div
        whileHover={{ scale: 1.1, y: -5 }}
        transition={{ type: "spring", stiffness: 300 }}
        className="bg-white p-3 rounded-full shadow-md"
    >
        <Image src={src} alt={alt} width={28} height={28} />
    </motion.div>
);

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState("users");

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

  const reactCode = `import { JeanChat, useJeanAgent } from '@jeanmemory/react';

function MathTutorApp() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "A patient math tutor."
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;

  return <JeanChat agent={agent} />;
}`;

  return (
    <div className="relative min-h-screen bg-gray-50 text-gray-900 overflow-hidden">
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="landing-particles-final" particleColor="#e5e7eb" particleCount={120} />
      </div>

      <main className="relative z-10 grid grid-cols-1 lg:grid-cols-2 min-h-screen">
        {/* Left Column: Content */}
        <div className="flex flex-col items-center p-8 pt-24 pb-12 lg:justify-center lg:p-16">
          <div className="max-w-lg w-full text-center">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mb-8"
            >
              <Image 
                src="/images/jean-logo-full-bw-transparent.png"
                alt="Jean Logo"
                width={240}
                height={80}
                className="mx-auto"
                priority
              />
            </motion.div>
            
            <motion.p
              className="text-2xl lg:text-3xl text-gray-600 mb-8 lg:mb-12 text-center"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              Universal memory across your applications
            </motion.p>
            
            <motion.div 
              className="flex bg-gray-200/70 p-1 rounded-lg mb-8 lg:mb-12"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.6 }}
            >
              <button onClick={() => setActiveTab("users")} className={cn("w-1/2 p-2 rounded-md text-sm font-medium transition-colors", activeTab === 'users' ? "bg-gray-900 text-white shadow" : "text-gray-600 hover:bg-gray-300/50")}>For Users</button>
              <button onClick={() => setActiveTab("developers")} className={cn("w-1/2 p-2 rounded-md text-sm font-medium transition-colors", activeTab === 'developers' ? "bg-gray-900 text-white shadow" : "text-gray-600 hover:bg-gray-300/50")}>For Developers</button>
            </motion.div>

            <motion.div
                className="flex flex-col items-center justify-center gap-4 h-28"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.8 }}
              >
                <AnimatePresence mode="wait">
                  {activeTab === 'users' ? (
                      <motion.div key="user-cta" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="w-full">
                        <Link href={user ? "/dashboard" : "/auth?animate=true"} passHref className="w-full">
                          <Button size="lg" variant="outline" className="w-full text-md py-6 border-orange-400 bg-white/50 hover:bg-gray-200/50">
                              {user ? "Go to Dashboard" : "Sign In With Jean"}
                          </Button>
                        </Link>
                      </motion.div>
                  ) : (
                    <motion.div key="dev-cta" initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="w-full space-y-4">
                      <Link href="https://calendly.com/jonathan-jeantechnologies/30min" passHref className="w-full">
                        <Button size="lg" variant="outline" className="w-full text-md py-6 border-gray-300 bg-white/50 hover:bg-gray-200/50">
                          Request a Demo
                        </Button>
                      </Link>
                      <Link href={user ? "/dashboard" : "/auth?animate=true"} passHref className="w-full">
                        <Button variant="ghost" size="lg" className="w-full text-md text-gray-500 hover:text-gray-800">
                            {user ? "Go to Dashboard" : "Sign In"}
                        </Button>
                      </Link>
                    </motion.div>
                  )}
                </AnimatePresence>
            </motion.div>
          </div>
        </div>

        {/* Right Column / Mobile Section: Visuals */}
        <div className="flex items-center justify-center p-4 md:p-8 pt-0 lg:p-8 bg-gray-100/30 backdrop-blur-sm lg:bg-transparent">
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className="w-full max-w-xl"
                >
                    {activeTab === 'users' ? (
                        <div className="space-y-4 md:space-y-6">
                            <div className="flex justify-center items-center space-x-4">
                                <AppIcon src="/images/ChatGPT-Logo.svg" alt="ChatGPT Logo" />
                                <AppIcon src="/images/claude.webp" alt="Claude Logo" />
                                <AppIcon src="/images/notion.svg" alt="Notion Logo" />
                                <AppIcon src="/images/obsidian.svg" alt="Obsidian Logo" />
                                <AppIcon src="/images/substack.png" alt="Substack Logo" />
                                <AppIcon src="/images/vscode.svg" alt="VS Code Logo" />
                            </div>
                            <div className="bg-white/60 backdrop-blur-sm border border-gray-200 rounded-xl p-4 flex flex-col h-56">
                                <h3 className="text-md font-semibold mb-2 text-center text-gray-500 flex-shrink-0">Generic AI</h3>
                                <div className="p-2 rounded-lg flex flex-col justify-end flex-grow min-h-0">
                                    <ChatBubble isUser={true} message="What should I work on today?" />
                                    <ChatBubble isUser={false} message="You could work on tasks, check your calendar, or read emails." />
                                </div>
                            </div>
                            <div className="bg-white/60 backdrop-blur-sm border border-gray-200 rounded-xl p-4 flex flex-col h-56">
                                <h3 className="text-md font-semibold mb-2 text-center text-gray-900 flex-shrink-0">Personalized with Jean</h3>
                                <div className="p-2 rounded-lg flex flex-col justify-end flex-grow min-h-0">
                                    <ChatBubble isUser={true} message="What should I work on today?" />
                                    <ChatBubble isUser={false} message="Finalize the Q3 launch slides. You also wanted to practice Spanish." isPersonalized={true} />
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <h2 className="text-2xl font-bold text-center mb-4">
                                Instantly personalize with 5 lines of code
                            </h2>
                            <p className="text-md text-gray-600 text-center mb-6 max-w-lg mx-auto">
                                With the Jean SDK, you can add memory and personalization to any AI application.
                            </p>
                            <CodeBlock language="jsx" value={reactCode} />
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
