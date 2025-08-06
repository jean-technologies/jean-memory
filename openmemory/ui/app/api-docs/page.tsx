"use client";

import React, { useState, useEffect, useRef } from 'react';
import { GitBranch, Shield, BookOpen, Puzzle, Terminal, Code, Server, Key, BrainCircuit, Copy, Check, LucideIcon, ListTree, Bot, Lightbulb, Briefcase, Share2, Component, PlayCircle, Cpu, FileText, Sparkles, AlertTriangle, Zap, Rocket, ArrowRight, ChevronRight, Users, Globe } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import ParticleNetwork from '@/components/landing/ParticleNetwork';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import Link from 'next/link';
import AICopyButton from '@/components/AICopyButton';
import { generateQuickstartAIContent } from '@/utils/aiDocContent';

// A simple syntax-highlighted code block component with a copy button
const CodeBlock = ({ code, lang = 'bash', title }: { code: string, lang?: string, title?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code.trim());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const lines = code.trim().split('\n');

  return (
    <div className="relative group my-4 bg-slate-900/70 backdrop-blur-sm rounded-lg border border-slate-700/50 shadow-lg">
      {title && (
      <div className="flex text-xs text-slate-400 border-b border-slate-700/50">
          <div className="px-4 py-2">{title}</div>
        </div>
      )}
      <div className="flex text-xs text-slate-400 border-b border-slate-700/50">
        <div className="px-4 py-2">{lang}</div>
      </div>
      <div className="p-4 pr-12 text-sm font-mono overflow-x-auto">
        {lines.map((line, i) => {
          let styledLine: string = line;
          if (lang === 'bash' || lang === 'http') {
              styledLine = line.replace(/curl/g, '<span class="text-pink-400">curl</span>');
              styledLine = styledLine.replace(/(-X POST|-H|-d)/g, '<span class="text-cyan-400">$&</span>');
              styledLine = styledLine.replace(/(https:\/\/[^\s]+)/g, '<span class="text-amber-400">$&</span>');
              styledLine = styledLine.replace(/(X-Api-Key:)/g, '<span class="text-sky-400">$&</span>');
          } else if (lang === 'python') {
              styledLine = styledLine.replace(/(#.*$)/g, '<span class="text-slate-500">$&</span>');
              styledLine = styledLine.replace(/(".*?"|'.*?')/g, '<span class="text-emerald-400">$&</span>');
              styledLine = styledLine.replace(/\b(from|import|def|return|print|if|for|in|not|try|except|raise|as)\b/g, '<span class="text-pink-400">$&</span>');
              styledLine = styledLine.replace(/\b(requests|json|os|JeanAgent|agent)\b/g, '<span class="text-sky-400">$&</span>');
          } else if (lang === 'typescript' || lang === 'tsx' || lang === 'jsx') {
              styledLine = styledLine.replace(/(\/\/.*$)/g, '<span class="text-slate-500">$&</span>');
              styledLine = styledLine.replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="text-emerald-400">$&</span>');
              styledLine = styledLine.replace(/\b(const|let|var|function|return|if|for|import|from|export|default|async|await)\b/g, '<span class="text-pink-400">$&</span>');
              styledLine = styledLine.replace(/\b(useJeanAgent|SignInWithJean|JeanChat|React)\b/g, '<span class="text-sky-400">$&</span>');
          } else if (lang === 'json') {
             styledLine = styledLine.replace(/"([^"]+)":/g, '<span class="text-sky-300">"$1"</span>:');
             styledLine = styledLine.replace(/: "([^"]*)"/g, ': <span class="text-emerald-400">"$1"</span>');
             styledLine = styledLine.replace(/: ([\d.]+)/g, ': <span class="text-purple-400">$1</span>');
             styledLine = styledLine.replace(/: (true|false)/g, ': <span class="text-pink-400">$1</span>');
             styledLine = styledLine.replace(/: (null)/g, ': <span class="text-slate-500">$1</span>');
          }
          return (
            <div key={i} className="flex items-start">
              <span className="text-right text-slate-600 select-none mr-4" style={{ minWidth: '2em' }}>
                {i + 1}
              </span>
              <code className="text-slate-200 whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: styledLine }} />
            </div>
          )
        })}
      </div>
      <button
        onClick={handleCopy}
        className="absolute top-12 right-2 p-2 rounded-md bg-slate-700/50 hover:bg-slate-700 transition-colors opacity-0 group-hover:opacity-100"
        aria-label="Copy code"
      >
        {copied ? (
          <Check className="h-4 w-4 text-green-400" />
        ) : (
          <Copy className="h-4 w-4 text-slate-400" />
        )}
      </button>
    </div>
  );
};

// Interactive Quick Demo Component
const QuickDemo = () => {
  const [activeTab, setActiveTab] = useState<'python' | 'react' | 'node'>('python');
  
  const demos = {
    python: {
      install: `pip install jeanmemory`,
      code: `from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_...", 
    system_prompt="You are a helpful tutor"
)
agent.run()`
    },
    react: {
      install: `npm install @jeanmemory/react`,
      code: `import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function App() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a helpful tutor"
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />;
}`
    },
    node: {
      install: `npm install @jeanmemory/node`,
      code: `import { JeanAgent } from '@jeanmemory/node';

const agent = new JeanAgent({
  apiKey: "jean_sk_...",
  systemPrompt: "You are a helpful tutor"
});

await agent.run();`
    }
  };

    return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex space-x-2 mb-4">
        {(['python', 'react', 'node'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-t-lg font-medium capitalize transition-all ${
              activeTab === tab 
                ? 'bg-slate-800 text-white border-b-2 border-blue-500' 
                : 'bg-slate-900/50 text-slate-400 hover:text-white'
            }`}
          >
            {tab === 'react' ? 'React/Next.js' : tab === 'node' ? 'Node.js' : 'Python'}
          </button>
        ))}
      </div>
      
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <CodeBlock code={demos[activeTab].install} lang="bash" title="Step 1: Install" />
        <CodeBlock code={demos[activeTab].code} lang={activeTab === 'python' ? 'python' : 'typescript'} title="Step 2: Build Your App" />
      </motion.div>
    </div>
  );
};

// Path Selection Card Component
const PathCard = ({ 
  title, 
  description, 
  icon: Icon, 
  color, 
  features, 
  href,
  badge 
}: { 
  title: string;
  description: string;
  icon: LucideIcon;
  color: string;
  features: string[];
  href: string;
  badge?: string;
}) => {
  return (
    <Link href={href} className="block h-full">
      <motion.div
        whileHover={{ scale: 1.02, y: -4 }}
        whileTap={{ scale: 0.98 }}
        className={`h-full p-6 rounded-xl border bg-gradient-to-br ${color} backdrop-blur-sm shadow-lg hover:shadow-xl transition-all cursor-pointer relative overflow-hidden group`}
      >
        {badge && (
          <span className="absolute top-4 right-4 px-2 py-1 text-xs font-bold bg-yellow-500 text-black rounded-full">
            {badge}
          </span>
        )}
        
        <div className="relative z-10">
          <div className="flex items-center mb-4">
            <div className="p-3 rounded-lg bg-white/10 backdrop-blur-sm">
              <Icon className="w-6 h-6" />
            </div>
          </div>
          
          <h3 className="text-xl font-bold mb-2">{title}</h3>
          <p className="text-sm opacity-90 mb-4">{description}</p>
          
          <ul className="space-y-2 mb-4">
            {features.map((feature, i) => (
              <li key={i} className="flex items-center text-sm">
                <ChevronRight className="w-4 h-4 mr-2 opacity-60" />
                {feature}
              </li>
            ))}
          </ul>
          
          <div className="flex items-center text-sm font-medium group-hover:translate-x-2 transition-transform">
            Get Started <ArrowRight className="w-4 h-4 ml-2" />
      </div>
             </div>
        
        {/* Decorative gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      </motion.div>
    </Link>
  );
};

// Feature Showcase Component
const FeatureShowcase = () => {
  const features = [
    {
      icon: Globe,
      title: "Your Memories, Everywhere",
      description: "One API, infinite possibilities. Your personal context follows you across the internet."
    },
    {
      icon: Shield,
      title: "Privacy First",
      description: "Complete user isolation. Your memories are yours alone, encrypted and secure."
    },
    {
      icon: Zap,
      title: "Lightning Fast",
      description: "Sub-100ms retrieval with vector search, graph relationships, and AI synthesis."
    },
    {
      icon: Users,
      title: "Multi-Tenant Ready",
      description: "Built for scale. Serve millions of users with isolated memory spaces."
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {features.map((feature, i) => {
        const Icon = feature.icon;
        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all"
          >
            <Icon className="w-8 h-8 mb-3 text-blue-400" />
            <h4 className="font-semibold mb-2">{feature.title}</h4>
            <p className="text-sm text-muted-foreground">{feature.description}</p>
          </motion.div>
        );
      })}
    </div>
  );
};

const ApiDocsPage = () => {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://jean-memory-api-virginia.onrender.com";

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
        {/* Keep the beloved particle background */}
        <div className="absolute inset-0 z-0">
          <ParticleNetwork 
            id="api-docs-particles" 
            className="h-full w-full" 
            interactive={false} 
            particleCount={80} 
          />
              </div>

        <div className="relative z-10">
          {/* AI Quick Deploy Button */}
          <div className="fixed top-20 right-4 z-50">
            <AICopyButton 
              content={generateQuickstartAIContent()} 
              title="AI Quick Deploy"
            />
            </div>

          {/* Hero Section */}
          <section className="relative py-20 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Jean Memory API
                </h1>
                <p className="text-xl sm:text-2xl text-muted-foreground mb-8 max-w-3xl mx-auto">
                  Your memories, everywhere on the internet.
                  <span className="block mt-2 text-lg">Build personalized AI in <span className="text-blue-400 font-bold">5 lines of code</span>.</span>
                </p>
              </motion.div>

              {/* Quick Win - The 5-line magic upfront */}
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                className="mb-12"
              >
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-300 mb-6">
                  <Rocket className="w-4 h-4 mr-2" />
                  <span className="text-sm font-medium">See it in action</span>
            </div>
                <QuickDemo />
              </motion.div>

              {/* Three Paths - Clear audience separation */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.6, duration: 0.6 }}
              >
                <h2 className="text-2xl font-bold mb-8">Choose Your Integration Path</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto">
                  <PathCard
                    title="SDK Developer"
                    description="Get started in minutes with our SDK"
                    icon={Zap}
                    color="from-blue-600/20 to-blue-800/10 border-blue-500/30 hover:border-blue-400/50 text-blue-100"
                    features={[
                      "5-line integration",
                      "React, Python, Node.js",
                      "Built-in authentication",
                      "Automatic context retrieval"
                    ]}
                    href="/api-docs/quickstart"
                    badge="EASIEST"
                  />
                  
                  <PathCard
                    title="AI Builder"
                    description="Integrate with Claude, ChatGPT, or Cursor"
                    icon={Bot}
                    color="from-purple-600/20 to-purple-800/10 border-purple-500/30 hover:border-purple-400/50 text-purple-100"
                    features={[
                      "MCP protocol support",
                      "Tool discovery",
                      "OAuth 2.1 security",
                      "Streaming responses"
                    ]}
                    href="/api-docs/mcp"
                  />
                  
                  <PathCard
                    title="API Power User"
                    description="Direct REST API access for custom integrations"
                    icon={Code}
                    color="from-green-600/20 to-green-800/10 border-green-500/30 hover:border-green-400/50 text-green-100"
                    features={[
                      "RESTful endpoints",
                      "Advanced filtering",
                      "Metadata & tags",
                      "Batch operations"
                    ]}
                    href="/api-docs/rest"
                  />
            </div>
              </motion.div>
          </div>
        </section>
        
          {/* Features Section */}
          <section className="py-16 px-4 sm:px-6 lg:px-8 border-t border-white/10">
            <div className="max-w-7xl mx-auto">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.8 }}
                className="text-center mb-12"
              >
                <h2 className="text-3xl font-bold mb-4">Why Jean Memory?</h2>
                <p className="text-muted-foreground max-w-2xl mx-auto">
                  One unified memory layer that works everywhere. No more context switching, no more data silos.
                </p>
              </motion.div>
              <FeatureShowcase />
           </div>
        </section>

          {/* Quick Links Section */}
          <section className="py-16 px-4 sm:px-6 lg:px-8 border-t border-white/10">
            <div className="max-w-7xl mx-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Link href="/api-docs/quickstart" className="group">
                  <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all">
                    <BookOpen className="w-8 h-8 mb-3 text-blue-400 group-hover:scale-110 transition-transform" />
                    <h3 className="font-semibold mb-2">Quick Start Guide</h3>
                    <p className="text-sm text-muted-foreground">Get running in 5 minutes</p>
            </div>
                </Link>
                
                <Link href="/api-docs/examples" className="group">
                  <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all">
                    <Lightbulb className="w-8 h-8 mb-3 text-yellow-400 group-hover:scale-110 transition-transform" />
                    <h3 className="font-semibold mb-2">Examples</h3>
                    <p className="text-sm text-muted-foreground">Real-world use cases</p>
              </div>
                </Link>
                
                <Link href="/api-docs/rest#reference" className="group">
                  <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all">
                    <Server className="w-8 h-8 mb-3 text-green-400 group-hover:scale-110 transition-transform" />
                    <h3 className="font-semibold mb-2">API Reference</h3>
                    <p className="text-sm text-muted-foreground">Complete endpoint docs</p>
              </div>
                </Link>
                
                <Link href="https://github.com/jean-technologies/jean-memory" className="group">
                  <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 hover:bg-white/10 transition-all">
                    <GitBranch className="w-8 h-8 mb-3 text-purple-400 group-hover:scale-110 transition-transform" />
                    <h3 className="font-semibold mb-2">GitHub</h3>
                    <p className="text-sm text-muted-foreground">Contribute & star</p>
            </div>
                </Link>
            </div>
          </div>
        </section>

          {/* CTA Section */}
          <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-white/10">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-3xl font-bold mb-4">Ready to Build?</h2>
              <p className="text-muted-foreground mb-8">
                Join thousands of developers building the next generation of personalized AI
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="/api-docs/quickstart">
                  <Button size="lg" className="group">
                    Start Building
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <Link href="https://jeanmemory.com">
                  <Button size="lg" variant="outline">
                    Get API Key
                  </Button>
                </Link>
            </div>
          </div>
        </section>
          </div>
          </div>
    </ProtectedRoute>
  );
};

export default ApiDocsPage;