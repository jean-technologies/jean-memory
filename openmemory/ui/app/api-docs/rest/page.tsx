"use client";

import React, { useState } from 'react';
import { ArrowLeft, Server, Shield, Code, Database, AlertTriangle, Copy, Check, ChevronRight, Tag, Search, Plus, Edit, Trash2, Key } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import ParticleNetwork from '@/components/landing/ParticleNetwork';
import { motion } from 'framer-motion';
import AICopyButton from '@/components/AICopyButton';
import { generateRestAPIContent } from '@/utils/aiDocContent';

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
          } else if (lang === 'bash' || lang === 'http') {
            styledLine = line.replace(/^(curl|POST|GET|PUT|DELETE|PATCH)/g, '<span class="text-pink-400">$&</span>');
            styledLine = styledLine.replace(/(-X|-H|-d|--data|--header)/g, '<span class="text-cyan-400">$&</span>');
            styledLine = styledLine.replace(/(https:\/\/[^\s]+)/g, '<span class="text-amber-400">$&</span>');
            styledLine = styledLine.replace(/(Authorization:|X-Api-Key:|Content-Type:)/g, '<span class="text-sky-400">$&</span>');
          } else if (lang === 'python') {
            styledLine = styledLine.replace(/(#.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?')/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(import|from|def|return|if|for|print|requests)\b/g, '<span class="text-pink-400">$&</span>');
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

const EndpointCard = ({
  method,
  path,
  description,
  auth,
  params,
  request,
  response,
  example
}: {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  description: string;
  auth?: string;
  params?: { name: string; type: string; required?: boolean; description: string }[];
  request?: string;
  response?: string;
  example?: string;
}) => {
  const methodColors = {
    GET: 'bg-blue-500',
    POST: 'bg-green-500',
    PUT: 'bg-yellow-500',
    DELETE: 'bg-red-500',
    PATCH: 'bg-purple-500'
  };

  return (
    <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <span className={`px-3 py-1 rounded text-xs font-bold text-white ${methodColors[method]}`}>
            {method}
          </span>
          <code className="text-sm font-mono text-blue-400">{path}</code>
        </div>
        {auth && (
          <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded">
            {auth}
          </span>
        )}
      </div>
      
      <p className="text-muted-foreground mb-4">{description}</p>
      
      {params && params.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-slate-400 mb-2">Parameters</h4>
          <div className="space-y-2">
            {params.map((param, i) => (
              <div key={i} className="flex items-start space-x-2 text-sm">
                <code className="text-blue-400 font-mono">{param.name}</code>
                <span className="text-slate-500">({param.type})</span>
                {param.required && <span className="text-red-400 text-xs">required</span>}
                <span className="text-muted-foreground">- {param.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {request && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-slate-400 mb-2">Request Body</h4>
          <CodeBlock code={request} lang="json" />
        </div>
      )}
      
      {response && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-slate-400 mb-2">Response</h4>
          <CodeBlock code={response} lang="json" />
        </div>
      )}
      
      {example && (
        <div>
          <h4 className="text-sm font-semibold text-slate-400 mb-2">Example</h4>
          <CodeBlock code={example} lang="bash" />
        </div>
      )}
    </div>
  );
};

export default function RestAPIPage() {
  const [activeSection, setActiveSection] = useState<'memories' | 'mcp' | 'apps' | 'auth'>('memories');
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://jean-memory-api-virginia.onrender.com";

  const sections = {
    memories: {
      name: 'Memory Operations',
      icon: Database,
      color: 'text-blue-400'
    },
    mcp: {
      name: 'MCP Tools',
      icon: Server,
      color: 'text-purple-400'
    },
    apps: {
      name: 'App Management',
      icon: Code,
      color: 'text-green-400'
    },
    auth: {
      name: 'Authentication',
      icon: Shield,
      color: 'text-red-400'
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Particle Background */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="rest-particles" className="h-full w-full" interactive={false} particleCount={60} />
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
            content={generateRestAPIContent()} 
            title="AI API Reference"
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
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-500/20 border border-green-500/30 text-green-300 mb-6">
                <Server className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">Direct API Access</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                REST API Reference
              </h1>
              <p className="text-xl text-muted-foreground">
                Complete REST API documentation for custom integrations
              </p>
            </motion.div>

            {/* Base URL */}
            <section className="mb-12 p-6 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
              <h2 className="text-lg font-semibold mb-3">Base URL</h2>
              <CodeBlock code={API_URL} lang="http" title="Production Endpoint" />
            </section>

            {/* Authentication */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <Shield className="w-6 h-6 mr-2 text-red-400" />
                Authentication
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Key className="w-5 h-5 mr-2 text-yellow-400" />
                    API Key Authentication
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Recommended for programmatic access. Provides full API features including metadata and tags.
                  </p>
                  <CodeBlock 
                    code={`X-Api-Key: jean_sk_your_api_key_here`} 
                    lang="http" 
                    title="Header"
                  />
                </div>
                
                <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                  <h3 className="text-lg font-semibold mb-3 flex items-center">
                    <Shield className="w-5 h-5 mr-2 text-blue-400" />
                    Bearer Token
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    For user-authenticated requests using Supabase JWT tokens.
                  </p>
                  <CodeBlock 
                    code={`Authorization: Bearer <jwt_token>`} 
                    lang="http" 
                    title="Header"
                  />
                </div>
              </div>

              <Alert className="mt-6 bg-yellow-950/50 border-yellow-800/60">
                <AlertTriangle className="w-4 h-4" />
                <AlertTitle>Security Best Practice</AlertTitle>
                <AlertDescription>
                  Never expose API keys in client-side code. Use environment variables and server-side proxies for production applications.
                </AlertDescription>
              </Alert>
            </section>

            {/* API Sections */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6">API Endpoints</h2>
              
              {/* Section Tabs */}
              <div className="flex flex-wrap gap-2 mb-8">
                {(Object.keys(sections) as Array<keyof typeof sections>).map((section) => {
                  const Icon = sections[section].icon;
                  return (
                    <button
                      key={section}
                      onClick={() => setActiveSection(section)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center ${
                        activeSection === section
                          ? 'bg-white/20 text-white'
                          : 'bg-white/10 text-muted-foreground hover:bg-white/15'
                      }`}
                    >
                      <Icon className={`w-4 h-4 mr-2 ${sections[section].color}`} />
                      {sections[section].name}
                    </button>
                  );
                })}
              </div>

              {/* Memory Operations */}
              {activeSection === 'memories' && (
                <div className="space-y-6">
                  <EndpointCard
                    method="GET"
                    path="/api/v1/memories"
                    description="List all memories for the authenticated user with optional filtering."
                    auth="API Key or Bearer Token"
                    params={[
                      { name: 'search_query', type: 'string', description: 'Search memories by content' },
                      { name: 'categories', type: 'string', description: 'Comma-separated list of categories' },
                      { name: 'limit', type: 'integer', description: 'Maximum number of results (default: 50)' },
                      { name: 'offset', type: 'integer', description: 'Pagination offset' }
                    ]}
                    response={`{
  "memories": [
    {
      "id": "mem_123",
      "content": "User prefers TypeScript",
      "categories": ["preferences", "programming"],
      "created_at": "2024-01-15T10:00:00Z",
      "metadata": {
        "tags": ["work", "tech-stack"]
      }
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}`}
                    example={`curl -X GET "${API_URL}/api/v1/memories?search_query=typescript&limit=10" \\
  -H "X-Api-Key: jean_sk_your_api_key"`}
                  />

                  <EndpointCard
                    method="POST"
                    path="/api/v1/memories"
                    description="Create a new memory for the authenticated user."
                    auth="API Key or Bearer Token"
                    request={`{
  "content": "Important meeting notes from project kickoff",
  "app_id": "app_uuid_optional",
  "metadata": {
    "tags": ["work", "project-alpha", "meetings"]
  }
}`}
                    response={`{
  "id": "mem_124",
  "content": "Important meeting notes from project kickoff",
  "created_at": "2024-01-15T10:00:00Z",
  "status": "active"
}`}
                    example={`curl -X POST "${API_URL}/api/v1/memories" \\
  -H "X-Api-Key: jean_sk_your_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "User completed Python course"}'`}
                  />

                  <EndpointCard
                    method="PATCH"
                    path="/api/v1/memories/{memory_id}"
                    description="Update an existing memory."
                    auth="API Key or Bearer Token"
                    params={[
                      { name: 'memory_id', type: 'string', required: true, description: 'The ID of the memory to update' }
                    ]}
                    request={`{
  "content": "Updated memory content",
  "metadata": {
    "tags": ["updated", "important"]
  }
}`}
                    response={`{
  "id": "mem_123",
  "content": "Updated memory content",
  "updated_at": "2024-01-15T11:00:00Z"
}`}
                  />

                  <EndpointCard
                    method="DELETE"
                    path="/api/v1/memories/{memory_id}"
                    description="Delete a memory permanently."
                    auth="API Key or Bearer Token"
                    params={[
                      { name: 'memory_id', type: 'string', required: true, description: 'The ID of the memory to delete' }
                    ]}
                    response={`{
  "success": true,
  "message": "Memory deleted successfully"
}`}
                  />
                </div>
              )}

              {/* MCP Tools */}
              {activeSection === 'mcp' && (
                <div className="space-y-6">
                  <Alert className="mb-6 bg-purple-950/50 border-purple-800/60">
                    <Server className="w-4 h-4" />
                    <AlertTitle>Unified MCP Endpoint</AlertTitle>
                    <AlertDescription>
                      All MCP tool calls go through a single endpoint using JSON-RPC 2.0 protocol.
                    </AlertDescription>
                  </Alert>

                  <EndpointCard
                    method="POST"
                    path="/mcp/messages/"
                    description="Execute MCP tools using JSON-RPC protocol."
                    auth="X-Api-Key (recommended)"
                    request={`{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "add_memories",
    "arguments": {
      "text": "User prefers dark mode in all applications",
      "tags": ["preferences", "ui"]
    }
  },
  "id": "request-123"
}`}
                    response={`{
  "jsonrpc": "2.0",
  "result": "Memory successfully added with ID: mem_125",
  "id": "request-123"
}`}
                    example={`curl -X POST "${API_URL}/mcp/messages/" \\
  -H "X-Api-Key: jean_sk_your_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_memory_v2",
      "arguments": {
        "query": "programming preferences",
        "tags_filter": ["work"]
      }
    },
    "id": 1
  }'`}
                  />

                  <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                    <h3 className="text-lg font-semibold mb-3">Available MCP Tools</h3>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-start">
                        <ChevronRight className="w-4 h-4 mt-0.5 mr-2 text-green-400" />
                        <div>
                          <code className="text-blue-400">add_memories</code> - Store new information with optional tags
                        </div>
                      </li>
                      <li className="flex items-start">
                        <ChevronRight className="w-4 h-4 mt-0.5 mr-2 text-green-400" />
                        <div>
                          <code className="text-blue-400">search_memory</code> - Basic semantic search
                        </div>
                      </li>
                      <li className="flex items-start">
                        <ChevronRight className="w-4 h-4 mt-0.5 mr-2 text-green-400" />
                        <div>
                          <code className="text-blue-400">search_memory_v2</code> - Advanced search with tag filtering (API key only)
                        </div>
                      </li>
                      <li className="flex items-start">
                        <ChevronRight className="w-4 h-4 mt-0.5 mr-2 text-green-400" />
                        <div>
                          <code className="text-blue-400">list_memories</code> - List all memories with pagination
                        </div>
                      </li>
                      <li className="flex items-start">
                        <ChevronRight className="w-4 h-4 mt-0.5 mr-2 text-green-400" />
                        <div>
                          <code className="text-blue-400">store_document</code> - Store large documents
                        </div>
                      </li>
                    </ul>
                  </div>
                </div>
              )}

              {/* App Management */}
              {activeSection === 'apps' && (
                <div className="space-y-6">
                  <EndpointCard
                    method="GET"
                    path="/api/v1/apps"
                    description="List all connected applications for the user."
                    auth="Bearer Token"
                    response={`{
  "apps": [
    {
      "id": "app_123",
      "name": "My Chatbot",
      "created_at": "2024-01-01T00:00:00Z",
      "memory_count": 150
    }
  ]
}`}
                  />

                  <EndpointCard
                    method="POST"
                    path="/api/v1/apps/{app_id}/sync"
                    description="Trigger synchronization for a specific app."
                    auth="Bearer Token"
                    params={[
                      { name: 'app_id', type: 'string', required: true, description: 'The ID of the app to sync' }
                    ]}
                    response={`{
  "task_id": "task_456",
  "status": "processing",
  "message": "Sync initiated"
}`}
                  />

                  <EndpointCard
                    method="GET"
                    path="/api/v1/apps/task/{task_id}"
                    description="Check the status of a sync task."
                    auth="Bearer Token"
                    params={[
                      { name: 'task_id', type: 'string', required: true, description: 'The task ID returned from sync' }
                    ]}
                    response={`{
  "task_id": "task_456",
  "status": "completed",
  "result": {
    "memories_added": 25,
    "memories_updated": 10
  }
}`}
                  />
                </div>
              )}

              {/* Authentication */}
              {activeSection === 'auth' && (
                <div className="space-y-6">
                  <EndpointCard
                    method="POST"
                    path="/api/v1/keys"
                    description="Create a new API key for your account."
                    auth="Bearer Token"
                    request={`{
  "name": "Production API Key",
  "permissions": ["read", "write"]
}`}
                    response={`{
  "key": "jean_sk_abc123...",
  "name": "Production API Key",
  "created_at": "2024-01-15T10:00:00Z",
  "last_used": null
}`}
                  />

                  <EndpointCard
                    method="GET"
                    path="/api/v1/keys"
                    description="List all API keys for your account."
                    auth="Bearer Token"
                    response={`{
  "keys": [
    {
      "id": "key_123",
      "name": "Development Key",
      "created_at": "2024-01-01T00:00:00Z",
      "last_used": "2024-01-15T09:00:00Z",
      "prefix": "jean_sk_gdy4..."
    }
  ]
}`}
                  />

                  <EndpointCard
                    method="DELETE"
                    path="/api/v1/keys/{key_id}"
                    description="Revoke an API key."
                    auth="Bearer Token"
                    params={[
                      { name: 'key_id', type: 'string', required: true, description: 'The ID of the key to revoke' }
                    ]}
                    response={`{
  "success": true,
  "message": "API key revoked successfully"
}`}
                  />
                </div>
              )}
            </section>

            {/* Error Responses */}
            <section className="mb-12">
              <h2 className="text-2xl font-bold mb-6 flex items-center">
                <AlertTriangle className="w-6 h-6 mr-2 text-orange-400" />
                Error Responses
              </h2>
              
              <div className="p-6 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10">
                <p className="text-muted-foreground mb-4">
                  The API uses standard HTTP status codes and returns detailed error messages.
                </p>
                
                <div className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">400 Bad Request</h3>
                    <CodeBlock 
                      code={`{
  "error": "Invalid request",
  "message": "Missing required parameter: content",
  "code": "MISSING_PARAMETER"
}`} 
                      lang="json" 
                    />
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-2">401 Unauthorized</h3>
                    <CodeBlock 
                      code={`{
  "error": "Authentication failed",
  "message": "Invalid or expired API key",
  "code": "INVALID_API_KEY"
}`} 
                      lang="json" 
                    />
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-2">429 Too Many Requests</h3>
                    <CodeBlock 
                      code={`{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please retry after 60 seconds",
  "retry_after": 60
}`} 
                      lang="json" 
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* Rate Limits */}
            <section className="mb-12 p-8 rounded-xl bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/30">
              <h2 className="text-2xl font-bold mb-6">Rate Limits</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-3">Free Tier</h3>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li>• 100 requests per minute</li>
                    <li>• 1,000 memories stored</li>
                    <li>• 10MB document storage</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-3">Pro Tier</h3>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li>• 1,000 requests per minute</li>
                    <li>• Unlimited memories</li>
                    <li>• 1GB document storage</li>
                  </ul>
                </div>
              </div>
              
              <Alert className="mt-6 bg-blue-950/50 border-blue-800/60">
                <AlertDescription>
                  Rate limit headers are included in all responses: <code>X-RateLimit-Limit</code>, <code>X-RateLimit-Remaining</code>, <code>X-RateLimit-Reset</code>
                </AlertDescription>
              </Alert>
            </section>

            {/* Pagination */}
            <section className="p-8 rounded-xl bg-white/5 backdrop-blur-sm border border-white/10">
              <h2 className="text-2xl font-bold mb-6">Pagination</h2>
              
              <p className="text-muted-foreground mb-4">
                List endpoints support pagination using <code>limit</code> and <code>offset</code> parameters.
              </p>
              
              <CodeBlock 
                code={`# First page
GET /api/v1/memories?limit=20&offset=0

# Second page
GET /api/v1/memories?limit=20&offset=20

# Response includes pagination metadata
{
  "memories": [...],
  "total": 100,
  "limit": 20,
  "offset": 0,
  "has_more": true
}`} 
                lang="bash" 
                title="Pagination Example"
              />
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}