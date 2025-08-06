"use client";

import React, { useState } from 'react';
import { ArrowLeft, Code, Package, Settings, Shield, Zap, Book, GitBranch, Copy, Check, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import ParticleNetwork from '@/components/landing/ParticleNetwork';
import { motion } from 'framer-motion';
import AICopyButton from '@/components/AICopyButton';
import { generateSDKAIContent } from '@/utils/aiDocContent';

const CodeBlock = ({ code, lang = 'typescript', title }: { code: string; lang?: string; title?: string }) => {
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
          
          if (lang === 'typescript' || lang === 'javascript') {
            styledLine = styledLine.replace(/(\/\/.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(const|let|var|function|return|if|import|from|export|interface|type|class|async|await)\b/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/\b(string|number|boolean|void|any|Promise)\b/g, '<span class="text-yellow-400">$&</span>');
          } else if (lang === 'python') {
            styledLine = styledLine.replace(/(#.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?')/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(from|import|def|return|if|class|async|await|self|None|True|False)\b/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/\b(str|int|bool|float|list|dict|Optional|List|Dict|Any)\b/g, '<span class="text-yellow-400">$&</span>');
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

const MethodCard = ({ 
  name, 
  description, 
  signature, 
  example, 
  lang = 'typescript' 
}: { 
  name: string;
  description: string;
  signature: string;
  example: string;
  lang?: string;
}) => {
  return (
    <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
      <h3 className="text-lg font-mono font-semibold text-blue-400 mb-2">{name}</h3>
      <p className="text-muted-foreground mb-4">{description}</p>
      <div className="space-y-3">
        <div>
          <h4 className="text-sm font-semibold text-slate-400 mb-2">Signature</h4>
          <CodeBlock code={signature} lang={lang} />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-slate-400 mb-2">Example</h4>
          <CodeBlock code={example} lang={lang} />
        </div>
      </div>
    </div>
  );
};

const TabSection = ({ 
  tabs, 
  activeTab, 
  onTabChange 
}: { 
  tabs: string[];
  activeTab: string;
  onTabChange: (tab: string) => void;
}) => {
  return (
    <div className="flex space-x-2 mb-6">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab)}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            activeTab === tab
              ? 'bg-blue-600 text-white'
              : 'bg-white/10 text-muted-foreground hover:bg-white/20'
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
};

export default function SDKReferencePage() {
  const [activeSDK, setActiveSDK] = useState<'React' | 'Python' | 'Node.js'>('React');

  const sdkContent = {
    React: {
      installation: `npm install @jeanmemory/react
# or
yarn add @jeanmemory/react
# or
pnpm add @jeanmemory/react`,
      configuration: `interface JeanAgentConfig {
  apiKey?: string;           // Your Jean Memory API key
  systemPrompt?: string;     // System prompt for AI behavior
  clientName?: string;       // Client identifier (default: "React App")
  baseUrl?: string;          // API base URL (default: production)
}`,
      mainHook: {
        name: 'useJeanAgent',
        description: 'Main React hook for initializing and managing the Jean Memory agent.',
        signature: `const {
  agent,           // Assistant-UI compatible agent config
  user,            // Current authenticated user
  messages,        // Conversation history
  isLoading,       // Loading state
  error,           // Error state
  signIn,          // Authentication function
  signOut,         // Sign out function
  sendMessage      // Send message function
} = useJeanAgent(config: JeanAgentConfig);`,
        example: `import { useJeanAgent } from '@jeanmemory/react';

function MyApp() {
  const { agent, signIn, user } = useJeanAgent({
    apiKey: "jean_sk_...",
    systemPrompt: "You are a helpful tutor"
  });

  if (!agent) {
    return <button onClick={signIn}>Sign In</button>;
  }

  return <div>Welcome, {user?.email}!</div>;
}`
      },
      components: [
        {
          name: 'SignInWithJean',
          description: 'Pre-built sign-in button component with Jean Memory branding.',
          signature: `<SignInWithJean 
  onSuccess?: (user: JeanUser) => void;
  apiKey?: string;
  className?: string;
/>`,
          example: `<SignInWithJean 
  onSuccess={(user) => console.log('Signed in:', user)}
  className="custom-button-styles"
/>`
        },
        {
          name: 'JeanChat',
          description: 'Complete chat interface component powered by Assistant-UI.',
          signature: `<JeanChat 
  agent: any;           // Agent from useJeanAgent
  className?: string;   // Custom styles
/>`,
          example: `const { agent, signIn } = useJeanAgent({...});

if (!agent) return <SignInWithJean onSuccess={signIn} />;
return <JeanChat agent={agent} className="h-96" />;`
        }
      ]
    },
    Python: {
      installation: `pip install jeanmemory
# or
pip3 install jeanmemory`,
      configuration: `class JeanAgent:
    def __init__(
        self,
        api_key: str,                    # Your Jean Memory API key
        system_prompt: str = "...",      # System prompt for AI behavior
        modality: str = "chat",          # Interaction mode
        client_name: str = "Python App"  # Client identifier
    )`,
      mainClass: {
        name: 'JeanAgent',
        description: 'Main Python class for Jean Memory integration.',
        signature: `agent = JeanAgent(
    api_key="jean_sk_...",
    system_prompt="You are a helpful assistant",
    modality="chat",
    client_name="My App"
)`,
        example: `from jeanmemory import JeanAgent

# Initialize the agent
agent = JeanAgent(
    api_key="jean_sk_...",
    system_prompt="You are a math tutor"
)

# Run interactive chat
agent.run()

# Or send individual messages
response = agent.send_message("What is 2+2?")
print(response)`
      },
      methods: [
        {
          name: 'authenticate()',
          description: 'Authenticate a user with their Jean Memory credentials.',
          signature: `def authenticate(
    self, 
    email: Optional[str] = None, 
    password: Optional[str] = None
) -> bool`,
          example: `# Interactive authentication (prompts for credentials)
agent.authenticate()

# Or provide credentials directly
agent.authenticate("user@example.com", "password")`
        },
        {
          name: 'send_message()',
          description: 'Send a message and receive an AI response with context.',
          signature: `def send_message(self, message: str) -> str`,
          example: `response = agent.send_message("Tell me about my last project")
print(response)  # AI response with user's context`
        },
        {
          name: 'run()',
          description: 'Start an interactive chat session in the terminal.',
          signature: `def run(self, auto_auth: bool = True)`,
          example: `# Start interactive chat with auto-authentication
agent.run()

# Or handle auth separately
agent.run(auto_auth=False)`
        },
        {
          name: 'get_conversation_history()',
          description: 'Retrieve the full conversation history.',
          signature: `def get_conversation_history(self) -> List[Dict]`,
          example: `history = agent.get_conversation_history()
for message in history:
    print(f"{message['role']}: {message['content']}")`
        }
      ]
    },
    'Node.js': {
      installation: `npm install @jeanmemory/node
# or
yarn add @jeanmemory/node
# or
pnpm add @jeanmemory/node`,
      configuration: `interface JeanAgentConfig {
  apiKey: string;           // Your Jean Memory API key
  systemPrompt?: string;    // System prompt for AI behavior
  clientName?: string;      // Client identifier
  model?: string;           // AI model to use
}`,
      mainClass: {
        name: 'JeanAgent',
        description: 'Main Node.js class for Jean Memory integration.',
        signature: `const agent = new JeanAgent({
  apiKey: "jean_sk_...",
  systemPrompt: "You are a helpful assistant",
  clientName: "Node App",
  model: "gpt-4"
});`,
        example: `import { JeanAgent } from '@jeanmemory/node';

const agent = new JeanAgent({
  apiKey: process.env.JEAN_API_KEY,
  systemPrompt: "You are a coding assistant"
});

// Authenticate user
await agent.authenticate('user@example.com', 'password');

// Send message
const response = await agent.sendMessage("Help me write a function");
console.log(response);`
      },
      methods: [
        {
          name: 'authenticate()',
          description: 'Authenticate a user with their Jean Memory credentials.',
          signature: `async authenticate(
  email?: string, 
  password?: string
): Promise<boolean>`,
          example: `// Interactive authentication
await agent.authenticate();

// Or with credentials
const success = await agent.authenticate('user@example.com', 'password');`
        },
        {
          name: 'sendMessage()',
          description: 'Send a message and receive an AI response.',
          signature: `async sendMessage(message: string): Promise<string>`,
          example: `const response = await agent.sendMessage("What did we discuss yesterday?");
console.log(response);`
        },
        {
          name: 'run()',
          description: 'Start an interactive chat session.',
          signature: `async run(autoAuth: boolean = true): Promise<void>`,
          example: `// Start interactive session
await agent.run();`
        },
        {
          name: 'getConversationHistory()',
          description: 'Get the full conversation history.',
          signature: `getConversationHistory(): Message[]`,
          example: `const history = agent.getConversationHistory();
history.forEach(msg => {
  console.log(\`\${msg.role}: \${msg.content}\`);
});`
        }
      ]
    }
  };

  const currentSDK = sdkContent[activeSDK];

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Particle Background */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="sdk-particles" className="h-full w-full" interactive={false} particleCount={60} />
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
              <div className="flex gap-2">
                <Link href="/api-docs/quickstart">
                  <Button variant="ghost" size="sm">Quick Start</Button>
                </Link>
                <Link href="/api-docs/examples">
                  <Button variant="ghost" size="sm">Examples</Button>
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* AI Quick Deploy Button */}
        <div className="fixed top-20 right-4 z-50">
          <AICopyButton 
            content={generateSDKAIContent()} 
            title="AI SDK Reference"
          />
        </div>

        {/* Main Content */}
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="max-w-6xl mx-auto">
            {/* Title Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-purple-500/20 border border-purple-500/30 text-purple-300 mb-6">
                <Package className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">Complete SDK Reference</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                SDK Reference
              </h1>
              <p className="text-xl text-muted-foreground">
                Complete documentation for React, Python, and Node.js SDKs
              </p>
            </motion.div>

            {/* SDK Tabs */}
            <TabSection tabs={['React', 'Python', 'Node.js']} activeTab={activeSDK} onTabChange={(tab) => setActiveSDK(tab as any)} />

            {/* Installation */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Package className="w-6 h-6 mr-2 text-blue-400" />
                Installation
              </h2>
              <CodeBlock code={currentSDK.installation} lang="bash" title="Terminal" />
            </section>

            {/* Configuration */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Settings className="w-6 h-6 mr-2 text-green-400" />
                Configuration
              </h2>
              <CodeBlock 
                code={currentSDK.configuration} 
                lang={activeSDK === 'Python' ? 'python' : 'typescript'} 
                title="Configuration Options"
              />
            </section>

            {/* Main API */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Code className="w-6 h-6 mr-2 text-purple-400" />
                {activeSDK === 'React' ? 'Main Hook' : 'Main Class'}
              </h2>
              <MethodCard
                name={activeSDK === 'React' ? currentSDK.mainHook.name : currentSDK.mainClass.name}
                description={activeSDK === 'React' ? currentSDK.mainHook.description : currentSDK.mainClass.description}
                signature={activeSDK === 'React' ? currentSDK.mainHook.signature : currentSDK.mainClass.signature}
                example={activeSDK === 'React' ? currentSDK.mainHook.example : currentSDK.mainClass.example}
                lang={activeSDK === 'Python' ? 'python' : 'typescript'}
              />
            </section>

            {/* Methods/Components */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <GitBranch className="w-6 h-6 mr-2 text-yellow-400" />
                {activeSDK === 'React' ? 'Components' : 'Methods'}
              </h2>
              <div className="space-y-6">
                {(activeSDK === 'React' ? currentSDK.components : currentSDK.methods).map((item, index) => (
                  <MethodCard
                    key={index}
                    name={item.name}
                    description={item.description}
                    signature={item.signature}
                    example={item.example}
                    lang={activeSDK === 'Python' ? 'python' : 'typescript'}
                  />
                ))}
              </div>
            </section>

            {/* Authentication */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Shield className="w-6 h-6 mr-2 text-red-400" />
                Authentication
              </h2>
              <Alert className="bg-blue-950/50 border-blue-800/60">
                <Shield className="w-4 h-4" />
                <AlertTitle>Two-Level Authentication</AlertTitle>
                <AlertDescription>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li><strong>Developer Level:</strong> Use your API key to initialize the SDK</li>
                    <li><strong>User Level:</strong> Users sign in with their Jean Memory account to access their personal memories</li>
                  </ul>
                </AlertDescription>
              </Alert>
              
              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-3">Authentication Flow</h3>
                <CodeBlock 
                  code={activeSDK === 'Python' 
                    ? `# 1. Developer provides API key
agent = JeanAgent(api_key="jean_sk_...")

# 2. User authenticates
agent.authenticate()  # Prompts for email/password

# 3. Access personalized memories
response = agent.send_message("What did I work on last week?")`
                    : activeSDK === 'React'
                    ? `// 1. Developer provides API key
const { agent, signIn } = useJeanAgent({
  apiKey: "jean_sk_..."
});

// 2. User clicks sign-in
if (!agent) return <SignInWithJean onSuccess={signIn} />;

// 3. Access personalized memories
return <JeanChat agent={agent} />;`
                    : `// 1. Developer provides API key
const agent = new JeanAgent({
  apiKey: "jean_sk_..."
});

// 2. User authenticates
await agent.authenticate();

// 3. Access personalized memories
const response = await agent.sendMessage("What are my goals?");`}
                  lang={activeSDK === 'Python' ? 'python' : 'typescript'}
                  title="Authentication Example"
                />
              </div>
            </section>

            {/* Best Practices */}
            <section className="mb-12 p-8 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <Book className="w-6 h-6 mr-2 text-orange-400" />
                Best Practices
              </h2>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <ChevronRight className="w-5 h-5 text-green-400 mt-0.5" />
                  <div>
                    <h3 className="font-semibold mb-1">Secure Your API Key</h3>
                    <p className="text-sm text-muted-foreground">
                      Never commit API keys to version control. Use environment variables or secure key management.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <ChevronRight className="w-5 h-5 text-green-400 mt-0.5" />
                  <div>
                    <h3 className="font-semibold mb-1">Clear System Prompts</h3>
                    <p className="text-sm text-muted-foreground">
                      Write specific, clear system prompts that define your AI's personality and capabilities.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <ChevronRight className="w-5 h-5 text-green-400 mt-0.5" />
                  <div>
                    <h3 className="font-semibold mb-1">Handle Errors Gracefully</h3>
                    <p className="text-sm text-muted-foreground">
                      Always handle authentication failures and network errors with user-friendly messages.
                    </p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <ChevronRight className="w-5 h-5 text-green-400 mt-0.5" />
                  <div>
                    <h3 className="font-semibold mb-1">Respect User Privacy</h3>
                    <p className="text-sm text-muted-foreground">
                      Users' memories are private. Never log or store user conversation data on your servers.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Performance Tips */}
            <section className="p-8 rounded-xl bg-gradient-to-br from-yellow-600/10 to-orange-600/10 border border-yellow-500/30">
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Zap className="w-6 h-6 mr-2 text-yellow-400" />
                Performance Tips
              </h2>
              <ul className="space-y-3 text-sm">
                <li className="flex items-start">
                  
                  <span><strong>Cache agent instances:</strong> Don't recreate the agent on every render/call</span>
                </li>
                <li className="flex items-start">
                  
                  <span><strong>Use streaming responses:</strong> For real-time chat experiences (coming soon)</span>
                </li>
                <li className="flex items-start">
                  
                  <span><strong>Batch operations:</strong> Group memory operations when possible</span>
                </li>
                <li className="flex items-start">
                  
                  <span><strong>Optimize context:</strong> Keep system prompts concise but clear</span>
                </li>
              </ul>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}