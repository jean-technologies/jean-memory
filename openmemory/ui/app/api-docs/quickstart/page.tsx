"use client";

import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Copy, Check, Zap, Code, Play, CheckCircle, Terminal, Package } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import ParticleNetwork from '@/components/landing/ParticleNetwork';
import { motion } from 'framer-motion';
import AICopyButton from '@/components/AICopyButton';
import { generateQuickstartAIContent } from '@/utils/aiDocContent';

const CodeBlock = ({ code, lang = 'bash', title }: { code: string; lang?: string; title?: string }) => {
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
        <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-700/50">
          <div className="px-4 py-2">{title}</div>
          <div className="px-4 py-2 text-green-400">{lang}</div>
        </div>
      )}
      <div className="p-4 pr-12 text-sm font-mono overflow-x-auto">
        {lines.map((line, i) => {
          let styledLine: string = line;
          
          // Language-specific syntax highlighting
          if (lang === 'bash') {
            styledLine = line.replace(/^(npm|pip|yarn|pnpm)/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/(install|add)/g, '<span class="text-cyan-400">$&</span>');
            styledLine = styledLine.replace(/(@jeanmemory\/\w+|jeanmemory)/g, '<span class="text-yellow-400">$&</span>');
          } else if (lang === 'python') {
            styledLine = styledLine.replace(/(#.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?')/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(from|import|def|return|if|class|async|await)\b/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/\b(JeanAgent|agent)\b/g, '<span class="text-sky-400">$&</span>');
          } else if (lang === 'typescript' || lang === 'tsx' || lang === 'javascript') {
            styledLine = styledLine.replace(/(\/\/.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(const|let|var|function|return|if|import|from|export|async|await)\b/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/\b(useJeanAgent|JeanAgent|SignInWithJean|JeanChat)\b/g, '<span class="text-sky-400">$&</span>');
          }
          
          return (
            <div key={i} className="flex items-start">
              <span className="text-right text-slate-600 select-none mr-4" style={{ minWidth: '2em' }}>
                {i + 1}
              </span>
              <code className="text-slate-200 whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: styledLine }} />
            </div>
          );
        })}
      </div>
      <button
        onClick={handleCopy}
        className="absolute top-4 right-2 p-2 rounded-md bg-slate-700/50 hover:bg-slate-700 transition-colors opacity-0 group-hover:opacity-100"
        aria-label="Copy code"
      >
        {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4 text-slate-400" />}
      </button>
    </div>
  );
};

const StepCard = ({ number, title, children }: { number: number; title: string; children: React.ReactNode }) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: number * 0.1 }}
      className="relative"
    >
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold">
          {number}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-semibold mb-4">{title}</h3>
          {children}
        </div>
      </div>
    </motion.div>
  );
};

export default function QuickstartPage() {
  const [selectedFramework, setSelectedFramework] = useState<'react' | 'python' | 'node'>('react');
  
  const frameworks = {
    react: {
      name: 'React/Next.js',
      install: 'npm install @jeanmemory/react',
      apiKeySetup: `// In your .env file
NEXT_PUBLIC_JEAN_API_KEY=jean_sk_your_api_key_here`,
      implementation: `import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function App() {
  // Initialize the agent with your system prompt
  const { agent, signIn } = useJeanAgent({
    apiKey: process.env.NEXT_PUBLIC_JEAN_API_KEY,
    systemPrompt: "You are a helpful assistant"
  });

  // Show sign-in if no user is authenticated
  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  
  // Render the chat interface
  return <JeanChat agent={agent} />;
}

export default App;`,
      runCommand: 'npm run dev'
    },
    python: {
      name: 'Python',
      install: 'pip install jeanmemory',
      apiKeySetup: `# In your .env file
JEAN_API_KEY=jean_sk_your_api_key_here`,
      implementation: `from jeanmemory import JeanAgent
import os

# Initialize the agent
agent = JeanAgent(
    api_key=os.getenv("JEAN_API_KEY"),
    system_prompt="You are a helpful assistant"
)

# Run the interactive chat
agent.run()`,
      runCommand: 'python app.py'
    },
    node: {
      name: 'Node.js',
      install: 'npm install @jeanmemory/node',
      apiKeySetup: `// In your .env file
JEAN_API_KEY=jean_sk_your_api_key_here`,
      implementation: `import { JeanAgent } from '@jeanmemory/node';
import dotenv from 'dotenv';

dotenv.config();

// Initialize the agent
const agent = new JeanAgent({
  apiKey: process.env.JEAN_API_KEY,
  systemPrompt: "You are a helpful assistant"
});

// Start the agent
await agent.run();`,
      runCommand: 'node app.js'
    }
  };

  const currentFramework = frameworks[selectedFramework];

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Particle Background */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="quickstart-particles" className="h-full w-full" interactive={false} particleCount={60} />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-white/10 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <Link href="/api-docs" className="flex items-center text-muted-foreground hover:text-foreground transition-colors">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to API Docs
              </Link>
              <Link href="/api-docs/examples">
                <Button variant="ghost" size="sm">
                  View Examples
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </header>

        {/* AI Quick Deploy Button */}
        <div className="fixed top-20 right-4 z-50">
          <AICopyButton 
            content={generateQuickstartAIContent()} 
            title="AI Quick Deploy"
          />
        </div>

        {/* Hero Section */}
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-500/20 border border-blue-500/30 text-blue-300 mb-6">
                <Zap className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">5-minute setup</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Quick Start Guide
              </h1>
              <p className="text-xl text-muted-foreground">
                Build your first Jean Memory application in just 5 lines of code
              </p>
            </motion.div>

            {/* Framework Selection */}
            <div className="mb-12">
              <h2 className="text-lg font-semibold mb-4 text-center">Choose Your Framework</h2>
              <div className="flex flex-wrap justify-center gap-2">
                {(Object.keys(frameworks) as Array<keyof typeof frameworks>).map((framework) => (
                  <button
                    key={framework}
                    onClick={() => setSelectedFramework(framework)}
                    className={`px-6 py-3 rounded-lg font-medium transition-all ${
                      selectedFramework === framework
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'bg-white/10 text-muted-foreground hover:bg-white/20'
                    }`}
                  >
                    {frameworks[framework].name}
                  </button>
                ))}
              </div>
            </div>

            {/* Step-by-step Guide */}
            <div className="space-y-12">
              <StepCard number={1} title="Get Your API Key">
                <p className="text-muted-foreground mb-4">
                  Sign up for a free Jean Memory account to get your API key.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link href="https://jeanmemory.com/signup" target="_blank">
                    <Button>
                      Create Free Account
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                  <Link href="https://jeanmemory.com/dashboard/api-keys" target="_blank">
                    <Button variant="outline">
                      Get API Key (if you have an account)
                    </Button>
                  </Link>
                </div>
                <Alert className="mt-4 bg-blue-950/50 border-blue-800/60">
                  <AlertDescription>
                    Your API key will look like: <code className="text-xs bg-black/30 px-2 py-1 rounded">jean_sk_gdy4KGuspLZ82PHGI...</code>
                  </AlertDescription>
                </Alert>
              </StepCard>

              <StepCard number={2} title="Install the SDK">
                <p className="text-muted-foreground mb-4">
                  Install the Jean Memory SDK for {currentFramework.name}.
                </p>
                <CodeBlock code={currentFramework.install} lang="bash" title="Terminal" />
              </StepCard>

              <StepCard number={3} title="Set Up Your API Key">
                <p className="text-muted-foreground mb-4">
                  Add your API key to your environment variables.
                </p>
                <CodeBlock code={currentFramework.apiKeySetup} lang="bash" title=".env" />
              </StepCard>

              <StepCard number={4} title="Write Your Application">
                <p className="text-muted-foreground mb-4">
                  Copy this code to create your first Jean Memory application.
                </p>
                <CodeBlock 
                  code={currentFramework.implementation} 
                  lang={selectedFramework === 'python' ? 'python' : 'typescript'} 
                  title={selectedFramework === 'python' ? 'app.py' : selectedFramework === 'node' ? 'app.js' : 'App.tsx'}
                />
              </StepCard>

              <StepCard number={5} title="Run Your Application">
                <p className="text-muted-foreground mb-4">
                  Start your application and begin chatting with your personalized AI.
                </p>
                <CodeBlock code={currentFramework.runCommand} lang="bash" title="Terminal" />
                
                <Alert className="mt-4 bg-green-950/50 border-green-800/60">
                  <CheckCircle className="w-4 h-4" />
                  <AlertDescription>
                    <strong>That's it!</strong> Your users can now sign in with their Jean Memory account and have personalized conversations.
                  </AlertDescription>
                </Alert>
              </StepCard>
            </div>

            {/* What's Next */}
            <section className="mt-16 p-8 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
              <h2 className="text-2xl font-bold mb-6">What's Next?</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Link href="/api-docs/sdk" className="block">
                  <div className="p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-white/10">
                    <Package className="w-6 h-6 mb-2 text-blue-400" />
                    <h3 className="font-semibold mb-1">SDK Reference</h3>
                    <p className="text-sm text-muted-foreground">
                      Explore all SDK methods and configuration options
                    </p>
                  </div>
                </Link>
                
                <Link href="/api-docs/examples" className="block">
                  <div className="p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-white/10">
                    <Code className="w-6 h-6 mb-2 text-green-400" />
                    <h3 className="font-semibold mb-1">Examples</h3>
                    <p className="text-sm text-muted-foreground">
                      See real-world implementations and use cases
                    </p>
                  </div>
                </Link>
                
                <Link href="/api-docs/rest" className="block">
                  <div className="p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-white/10">
                    <Terminal className="w-6 h-6 mb-2 text-purple-400" />
                    <h3 className="font-semibold mb-1">REST API</h3>
                    <p className="text-sm text-muted-foreground">
                      Build custom integrations with our REST endpoints
                    </p>
                  </div>
                </Link>
                
                <Link href="/api-docs/mcp" className="block">
                  <div className="p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-white/10">
                    <Play className="w-6 h-6 mb-2 text-yellow-400" />
                    <h3 className="font-semibold mb-1">MCP Protocol</h3>
                    <p className="text-sm text-muted-foreground">
                      Integrate with Claude, ChatGPT, and other AI assistants
                    </p>
                  </div>
                </Link>
              </div>
            </section>

            {/* Help Section */}
            <section className="mt-8 text-center">
              <p className="text-muted-foreground">
                Need help? Join our{' '}
                <Link href="https://discord.gg/jeanmemory" className="text-blue-400 hover:text-blue-300">
                  Discord community
                </Link>{' '}
                or check out the{' '}
                <Link href="https://github.com/jean-technologies/jean-memory" className="text-blue-400 hover:text-blue-300">
                  GitHub repository
                </Link>
              </p>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}