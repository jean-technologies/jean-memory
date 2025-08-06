"use client";

import React, { useState } from 'react';
import { ArrowLeft, Bot, Code, Server, Shield, Settings, Terminal, GitBranch, Copy, Check, AlertTriangle, Cpu, Info } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import ParticleNetwork from '@/components/landing/ParticleNetwork';
import { motion } from 'framer-motion';
import AICopyButton from '@/components/AICopyButton';
import { generateMCPAIContent } from '@/utils/aiDocContent';

const CodeBlock = ({ code, lang = 'json', title }: { code: string; lang?: string; title?: string }) => {
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
          
          if (lang === 'json') {
            styledLine = styledLine.replace(/"([^"]+)":/g, '<span class="text-sky-300">"$1"</span>:');
            styledLine = styledLine.replace(/: "([^"]*)"/g, ': <span class="text-emerald-400">"$1"</span>');
            styledLine = styledLine.replace(/: ([\d.]+)/g, ': <span class="text-purple-400">$1</span>');
            styledLine = styledLine.replace(/: (true|false)/g, ': <span class="text-pink-400">$1</span>');
            styledLine = styledLine.replace(/: (null)/g, ': <span class="text-slate-500">$1</span>');
          } else if (lang === 'bash') {
            styledLine = line.replace(/^(curl|POST|GET)/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/(-X POST|-H|-d)/g, '<span class="text-cyan-400">$&</span>');
            styledLine = styledLine.replace(/(https:\/\/[^\s]+)/g, '<span class="text-amber-400">$&</span>');
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

const ToolCard = ({ 
  name, 
  description, 
  parameters,
  example 
}: { 
  name: string;
  description: string;
  parameters: { name: string; type: string; description: string; required?: boolean }[];
  example: string;
}) => {
  return (
    <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
      <h3 className="text-lg font-mono font-semibold text-purple-400 mb-2">{name}</h3>
      <p className="text-muted-foreground mb-4">{description}</p>
      
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-slate-400 mb-2">Parameters</h4>
        <div className="space-y-2">
          {parameters.map((param, i) => (
            <div key={i} className="flex items-start space-x-2 text-sm">
              <code className="text-blue-400 font-mono">{param.name}</code>
              <span className="text-slate-500">({param.type})</span>
              {param.required && <span className="text-red-400 text-xs">required</span>}
              <span className="text-muted-foreground">- {param.description}</span>
            </div>
          ))}
        </div>
      </div>
      
      <div>
        <h4 className="text-sm font-semibold text-slate-400 mb-2">Example</h4>
        <CodeBlock code={example} lang="json" />
      </div>
    </div>
  );
};

const SetupStep = ({ 
  number, 
  title, 
  children,
  platform 
}: { 
  number: number;
  title: string;
  children: React.ReactNode;
  platform?: 'claude' | 'chatgpt' | 'cursor';
}) => {
  const colors = {
    claude: 'from-orange-500/20 to-orange-600/10 border-orange-500/30',
    chatgpt: 'from-green-500/20 to-green-600/10 border-green-500/30',
    cursor: 'from-blue-500/20 to-blue-600/10 border-blue-500/30'
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: number * 0.1 }}
      className={`relative p-6 rounded-lg bg-gradient-to-br ${platform ? colors[platform] : 'from-white/5 to-white/10'} border ${platform ? '' : 'border-white/10'}`}
    >
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white/20 text-white flex items-center justify-center font-bold text-sm">
          {number}
        </div>
        <div className="flex-1">
          <h3 className="text-lg font-semibold mb-3">{title}</h3>
          {children}
        </div>
      </div>
    </motion.div>
  );
};

export default function MCPGuidePage() {
  const [activeClient, setActiveClient] = useState<'claude' | 'chatgpt' | 'cursor'>('claude');
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://jean-memory-api-virginia.onrender.com";

  const clientSetups = {
    claude: {
      name: 'Claude Desktop',
      icon: '',
      configPath: '~/Library/Application Support/Claude/claude_desktop_config.json',
      config: `{
  "mcpServers": {
    "jean-memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-jean-memory"
      ],
      "env": {
        "JEAN_API_KEY": "jean_sk_your_api_key_here"
      }
    }
  }
}`
    },
    chatgpt: {
      name: 'ChatGPT',
      icon: '💬',
      configPath: 'Custom GPT Action',
      config: `{
  "openapi": "3.0.0",
  "servers": [
    {
      "url": "${API_URL}"
    }
  ],
  "paths": {
    "/mcp/messages/": {
      "post": {
        "operationId": "callJeanMemory",
        "x-openai-isConsequential": false
      }
    }
  }
}`
    },
    cursor: {
      name: 'Cursor',
      icon: '',
      configPath: '~/.cursor/config.json',
      config: `{
  "mcpServers": {
    "jean-memory": {
      "command": "node",
      "args": [
        "/path/to/jean-memory-mcp-server.js"
      ],
      "env": {
        "JEAN_API_KEY": "jean_sk_your_api_key_here"
      }
    }
  }
}`
    }
  };

  const currentSetup = clientSetups[activeClient];

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Particle Background */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="mcp-particles" className="h-full w-full" interactive={false} particleCount={60} />
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
                <Link href="/api-docs/rest">
                  <Button variant="ghost" size="sm">REST API</Button>
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
            content={generateMCPAIContent()} 
            title="AI MCP Guide"
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
                <Bot className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">AI Assistant Integration</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                MCP Protocol Guide
              </h1>
              <p className="text-xl text-muted-foreground">
                Integrate Jean Memory with Claude, ChatGPT, Cursor, and other AI assistants
              </p>
            </motion.div>

            {/* What is MCP */}
            <section className="mb-12 p-8 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
              <h2 className="text-2xl font-bold mb-4 flex items-center">
                <Info className="w-6 h-6 mr-2 text-blue-400" />
                What is MCP?
              </h2>
              <p className="text-muted-foreground mb-4">
                The Model Context Protocol (MCP) is a standardized way for AI assistants to interact with external tools and data sources. 
                Jean Memory implements MCP to allow AI assistants to access and manage user memories seamlessly.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                  <h3 className="font-semibold mb-2">Tool Discovery</h3>
                  <p className="text-sm text-muted-foreground">AI assistants automatically discover available memory tools</p>
                </div>
                <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                  <h3 className="font-semibold mb-2">OAuth 2.1 Security</h3>
                  <p className="text-sm text-muted-foreground">Secure authentication with PKCE flow</p>
                </div>
                <div className="p-4 rounded-lg bg-white/5 border border-white/10">
                  <h3 className="font-semibold mb-2">Real-time Updates</h3>
                  <p className="text-sm text-muted-foreground">SSE or HTTP for streaming responses</p>
                </div>
              </div>
            </section>

            {/* Client Selection */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6">Choose Your AI Platform</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {(Object.keys(clientSetups) as Array<keyof typeof clientSetups>).map((client) => (
                  <button
                    key={client}
                    onClick={() => setActiveClient(client)}
                    className={`p-6 rounded-lg border transition-all ${
                      activeClient === client
                        ? 'bg-white/10 border-purple-500 shadow-lg'
                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                    }`}
                  >
                    <div className="text-3xl mb-2">{clientSetups[client].icon}</div>
                    <h3 className="font-semibold">{clientSetups[client].name}</h3>
                  </button>
                ))}
              </div>
            </section>

            {/* Setup Instructions */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6">Setup Instructions for {currentSetup.name}</h2>
              <div className="space-y-6">
                <SetupStep number={1} title="Get Your API Key" platform={activeClient}>
                  <p className="text-muted-foreground mb-4">
                    Sign up for a Jean Memory account and create an API key.
                  </p>
                  <Link href="https://jeanmemory.com/dashboard/api-keys" target="_blank">
                    <Button size="sm">Get API Key</Button>
                  </Link>
                </SetupStep>

                <SetupStep number={2} title="Configure MCP" platform={activeClient}>
                  <p className="text-muted-foreground mb-4">
                    Add Jean Memory to your {currentSetup.name} configuration.
                  </p>
                  <div className="mb-2">
                    <p className="text-sm text-slate-400 mb-1">Configuration file location:</p>
                    <code className="text-xs bg-black/30 px-2 py-1 rounded">{currentSetup.configPath}</code>
                  </div>
                  <CodeBlock code={currentSetup.config} lang="json" title="Configuration" />
                </SetupStep>

                <SetupStep number={3} title={`Restart ${currentSetup.name}`} platform={activeClient}>
                  <p className="text-muted-foreground">
                    Restart {currentSetup.name} to load the Jean Memory MCP server. The tools will be automatically available.
                  </p>
                </SetupStep>
              </div>
            </section>

            {/* MCP Tools */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <Code className="w-6 h-6 mr-2 text-purple-400" />
                Available MCP Tools
              </h2>
              
              <Alert className="mb-6 bg-purple-950/50 border-purple-800/60">
                <AlertTriangle className="w-4 h-4" />
                <AlertTitle>Tool Availability</AlertTitle>
                <AlertDescription>
                  The exact tools available depend on your authentication method. Claude Desktop users get a simplified toolset for stability.
                </AlertDescription>
              </Alert>

              <div className="space-y-6">
                <ToolCard
                  name="jean_memory"
                  description="Primary tool for intelligent context retrieval and memory management. Automatically determines what memories to retrieve based on the conversation."
                  parameters={[
                    { name: 'user_message', type: 'string', description: 'The user message to process', required: true },
                    { name: 'is_new_conversation', type: 'boolean', description: 'Whether this is the start of a new conversation', required: true },
                    { name: 'needs_context', type: 'boolean', description: 'Whether to retrieve personal context', required: false }
                  ]}
                  example={`{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "jean_memory",
    "arguments": {
      "user_message": "What did I work on last week?",
      "is_new_conversation": true,
      "needs_context": true
    }
  },
  "id": 1
}`}
                />

                <ToolCard
                  name="add_memories"
                  description="Store new information in the user's long-term memory."
                  parameters={[
                    { name: 'text', type: 'string', description: 'Information to remember', required: true },
                    { name: 'tags', type: 'array', description: 'Optional tags for categorization (API users only)', required: false }
                  ]}
                  example={`{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "add_memories",
    "arguments": {
      "text": "User prefers TypeScript over JavaScript for new projects"
    }
  },
  "id": 2
}`}
                />

                <ToolCard
                  name="search_memory"
                  description="Search through stored memories using semantic search."
                  parameters={[
                    { name: 'query', type: 'string', description: 'Search query', required: true },
                    { name: 'limit', type: 'integer', description: 'Maximum results to return', required: false }
                  ]}
                  example={`{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_memory",
    "arguments": {
      "query": "programming preferences",
      "limit": 5
    }
  },
  "id": 3
}`}
                />

                <ToolCard
                  name="store_document"
                  description="Store large documents or code files for later retrieval."
                  parameters={[
                    { name: 'title', type: 'string', description: 'Document title', required: true },
                    { name: 'content', type: 'string', description: 'Full document content', required: true },
                    { name: 'document_type', type: 'string', description: 'Type of document (markdown, code, etc.)', required: false }
                  ]}
                  example={`{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "store_document",
    "arguments": {
      "title": "Project Architecture",
      "content": "# System Design\\n\\n...",
      "document_type": "markdown"
    }
  },
  "id": 4
}`}
                />
              </div>
            </section>

            {/* Protocol Details */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <Server className="w-6 h-6 mr-2 text-green-400" />
                Protocol Details
              </h2>
              
              <div className="space-y-6">
                <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                  <h3 className="text-lg font-semibold mb-3">Endpoint</h3>
                  <CodeBlock 
                    code={`POST ${API_URL}/mcp/messages/`} 
                    lang="bash" 
                    title="MCP Endpoint" 
                  />
                </div>

                <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                  <h3 className="text-lg font-semibold mb-3">Authentication</h3>
                  <p className="text-muted-foreground mb-3">
                    MCP uses OAuth 2.1 with PKCE for secure authentication. The flow is handled automatically by the MCP client.
                  </p>
                  <CodeBlock 
                    code={`Authorization: Bearer <oauth_token>
X-Client-Name: claude-desktop
X-User-Id: <user_id>`} 
                    lang="bash" 
                    title="Headers" 
                  />
                </div>

                <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                  <h3 className="text-lg font-semibold mb-3">Initialize Handshake</h3>
                  <CodeBlock 
                    code={`{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": {
        "listChanged": true
      }
    },
    "clientInfo": {
      "name": "claude-desktop",
      "version": "1.0.0"
    }
  },
  "id": 1
}`} 
                    lang="json" 
                    title="Initialize Request" 
                  />
                </div>

                <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                  <h3 className="text-lg font-semibold mb-3">Tool Discovery</h3>
                  <CodeBlock 
                    code={`{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 2
}`} 
                    lang="json" 
                    title="List Tools Request" 
                  />
                </div>
              </div>
            </section>

            {/* OAuth Flow */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <Shield className="w-6 h-6 mr-2 text-red-400" />
                OAuth 2.1 Authentication Flow
              </h2>
              
              <Alert className="mb-6 bg-blue-950/50 border-blue-800/60">
                <Info className="w-4 h-4" />
                <AlertTitle>Automatic Authentication</AlertTitle>
                <AlertDescription>
                  Most MCP clients handle OAuth authentication automatically. Users will be prompted to sign in with their Jean Memory account when first connecting.
                </AlertDescription>
              </Alert>

              <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                <h3 className="text-lg font-semibold mb-3">OAuth Endpoints</h3>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-slate-400">Discovery:</span>
                    <code className="ml-2 text-blue-400">/.well-known/oauth-authorization-server</code>
                  </div>
                  <div>
                    <span className="text-slate-400">Authorize:</span>
                    <code className="ml-2 text-blue-400">/oauth/authorize</code>
                  </div>
                  <div>
                    <span className="text-slate-400">Token:</span>
                    <code className="ml-2 text-blue-400">/oauth/token</code>
                  </div>
                  <div>
                    <span className="text-slate-400">Register:</span>
                    <code className="ml-2 text-blue-400">/oauth/register</code>
                  </div>
                </div>
              </div>
            </section>

            {/* Troubleshooting */}
            <section className="p-8 rounded-xl bg-gradient-to-br from-red-600/10 to-orange-600/10 border border-red-500/30">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <AlertTriangle className="w-6 h-6 mr-2 text-orange-400" />
                Troubleshooting
              </h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Tools not appearing in Claude/Cursor</h3>
                  <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                    <li>Ensure your API key is valid and correctly set in the config</li>
                    <li>Restart the application completely (not just reload)</li>
                    <li>Check the MCP server logs for connection errors</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">Authentication failures</h3>
                  <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                    <li>Clear OAuth cache and re-authenticate</li>
                    <li>Ensure your Jean Memory account is active</li>
                    <li>Check that OAuth redirect URIs are properly configured</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">Slow response times</h3>
                  <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                    <li>MCP adds 100-200ms overhead for protocol handling</li>
                    <li>First requests may be slower due to initialization</li>
                    <li>Consider using the SDK for production applications</li>
                  </ul>
                </div>
              </div>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}