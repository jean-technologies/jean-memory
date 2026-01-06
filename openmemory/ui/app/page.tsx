"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import { ArrowRight, FileText, Users, Code, BookOpen, Building2 } from "lucide-react";

export default function DeveloperLandingPage() {
  const [activeTab, setActiveTab] = useState("react");

  const codeExamples = {
    react: {
      title: "React SDK",
      code: `import { JeanProvider, JeanChat } from '@jeanmemory/react';

function App() {
  return (
    <JeanProvider apiKey="YOUR_API_KEY">
      <JeanChat />
    </JeanProvider>
  );
}`,
      install: "npm install @jeanmemory/react"
    },
    python: {
      title: "Python SDK",
      code: `from jeanmemory import JeanClient

jean = JeanClient(api_key="YOUR_API_KEY")

# Get context before calling your LLM
context = jean.get_context(
    user_token="USER_TOKEN",
    message="What did we discuss?"
).text`,
      install: "pip install jeanmemory"
    },
    node: {
      title: "Node.js SDK",
      code: `import { JeanClient } from '@jeanmemory/node';

const jean = new JeanClient({ 
  apiKey: "YOUR_API_KEY" 
});

const context = await jean.getContext({
  user_token: userToken,
  message: "Previous conversation?"
});`,
      install: "npm install @jeanmemory/node"
    }
  };

  return (
    <div className="relative min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Background */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork 
          id="developer-particles" 
          particleColor="#94a3b8" 
          particleCount={80} 
        />
      </div>

      {/* Main Content */}
      <main className="relative z-10">
        {/* Hero Section */}
        <div className="container mx-auto px-6 pt-20 pb-12">
          <div className="max-w-6xl mx-auto">
            {/* Logo and Tagline */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <Image 
                src="/images/jean-logo-full-bw-transparent.png"
                alt="Jean Memory"
                width={200}
                height={67}
                className="mx-auto mb-6 dark:invert"
                priority
              />
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
                Add Memory to Your AI Applications
              </h1>
              <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
                Production-ready SDKs for intelligent context management. 
                Ship personalized AI experiences in minutes, not months.
              </p>
            </motion.div>

            {/* Quick Links */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="flex flex-wrap justify-center gap-4 mb-16"
            >
              <Link href="https://docs.jeanmemory.com" target="_blank">
                <Button size="lg" className="gap-2">
                  <BookOpen className="w-4 h-4" />
                  Documentation
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="https://github.com/jean-technologies/jean-memory" target="_blank">
                <Button size="lg" variant="outline" className="gap-2">
                  <Code className="w-4 h-4" />
                  View on GitHub
                </Button>
              </Link>
              <Link href="/ai-memory-landscape-review.pdf" target="_blank">
                <Button size="lg" variant="outline" className="gap-2">
                  <FileText className="w-4 h-4" />
                  AI Memory Landscape Review
                </Button>
              </Link>
            </motion.div>

            {/* Code Examples */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-8 mb-16"
            >
              <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
                5-Minute Integration
              </h2>
              
              {/* Tab Navigation */}
              <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
                {Object.keys(codeExamples).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 font-medium transition-colors ${
                      activeTab === tab
                        ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                    }`}
                  >
                    {codeExamples[tab as keyof typeof codeExamples].title}
                  </button>
                ))}
              </div>

              {/* Installation Command */}
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Install:</p>
                <code className="bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded text-sm">
                  {codeExamples[activeTab as keyof typeof codeExamples].install}
                </code>
              </div>

              {/* Code Example */}
              <CodeBlock 
                code={codeExamples[activeTab as keyof typeof codeExamples].code}
                language={activeTab === "python" ? "python" : "typescript"}
              />
            </motion.div>

            {/* Features Grid */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="grid md:grid-cols-3 gap-8 mb-16"
            >
              <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mb-4">
                  <Code className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  Production Ready
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Battle-tested SDKs with intelligent orchestration, automatic memory management, and enterprise-grade security.
                </p>
              </div>

              <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mb-4">
                  <Users className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  Multi-Platform
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Native SDKs for React, Python, and Node.js. Works with any LLM provider or framework.
                </p>
              </div>

              <div className="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mb-4">
                  <Building2 className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-white">
                  Enterprise Solutions
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  We build bespoke memory systems for companies. Custom integrations and dedicated support available.
                </p>
              </div>
            </motion.div>

            {/* CTA Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-center bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-white"
            >
              <h2 className="text-3xl font-bold mb-4">
                Ready to Build Intelligent Applications?
              </h2>
              <p className="text-xl mb-8 opacity-90">
                Get your API key and start building in minutes.
              </p>
              <div className="flex gap-4 justify-center">
                <Link href="https://docs.jeanmemory.com/quickstart" target="_blank">
                  <Button size="lg" variant="secondary" className="gap-2">
                    Get Started
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
                <Link href="mailto:jonathan@jeantechnologies.com">
                  <Button size="lg" variant="outline" className="gap-2 bg-white/10 text-white border-white/20 hover:bg-white/20">
                    Contact Sales
                  </Button>
                </Link>
              </div>
            </motion.div>

            {/* Enterprise Note */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="text-center mt-12 p-6 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800"
            >
              <p className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                🏢 Looking for a custom memory solution?
              </p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                We specialize in building bespoke memory systems tailored to your company's needs. 
                <Link href="mailto:jonathan@jeantechnologies.com" className="underline font-medium ml-1">
                  Let's discuss your requirements
                </Link>
              </p>
            </motion.div>

            {/* Footer with link to old product */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="text-center mt-16 pt-8 border-t border-gray-200 dark:border-gray-800"
            >
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Looking for the consumer memory management app?{" "}
                <Link href="/dashboard" className="underline hover:text-gray-700 dark:hover:text-gray-300">
                  Access the legacy dashboard
                </Link>
              </p>
            </motion.div>
          </div>
        </div>
      </main>
    </div>
  );
}