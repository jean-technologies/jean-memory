"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import ParticleNetwork from "@/components/landing/ParticleNetwork";
import { Button } from "@/components/ui/button";
import { CodeBlock } from "@/components/ui/code-block";
import { FileText } from "lucide-react";

export default function LandingPage() {
  const { user, isLoading } = useAuth();

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

  const reactCode = `import { JeanChat, useJeanAgent } from 'jeanmemory-react';

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

      <main className="relative z-10 grid grid-cols-1 lg:grid-cols-5 min-h-screen">
        {/* Left Column: Content */}
        <div className="flex flex-col items-center p-8 pt-24 pb-12 lg:justify-center lg:p-16 lg:col-span-3">
          <div className="max-w-2xl w-full text-center">
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
                className="flex flex-col items-center justify-center gap-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.6 }}
            >
                <Link href="https://calendly.com/jonathan-jeantechnologies/30min" passHref className="w-full">
                  <Button size="lg" variant="outline" className="w-full text-md py-6 border-gray-300 bg-white/50 hover:bg-gray-200/50">
                    Request a Demo
                  </Button>
                </Link>
                <div className="flex gap-3 w-full">
                  <a href="https://docs.jeanmemory.com" target="_blank" rel="noopener noreferrer" className="flex-1">
                    <Button variant="ghost" size="lg" className="w-full text-md text-gray-500 hover:text-gray-800">
                      View the Docs
                    </Button>
                  </a>
                  <a href="/ai-memory-industry-report.pdf" target="_blank" rel="noopener noreferrer" className="flex-1">
                    <Button variant="ghost" size="lg" className="w-full text-md text-gray-500 hover:text-gray-800 gap-2">
                      <FileText className="w-4 h-4" />
                      AI Memory Report
                    </Button>
                  </a>
                </div>
            </motion.div>
          </div>
        </div>

        {/* Right Column / Mobile Section: Visuals */}
        <div className="flex items-center justify-center p-4 md:p-8 pt-0 lg:p-8 bg-gray-100/30 backdrop-blur-sm lg:bg-transparent lg:col-span-2">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="w-full max-w-xl"
            >
                <div>
                    <h2 className="text-2xl font-bold text-center mb-4">
                        Instantly personalize with 5 lines of code
                    </h2>
                    <p className="text-md text-gray-600 text-center mb-6 max-w-lg mx-auto">
                        With the Jean SDK, you can add memory and personalization to any AI application.
                    </p>
                    <CodeBlock language="jsx" value={reactCode} />
                </div>
            </motion.div>
        </div>
      </main>
    </div>
  );
}
