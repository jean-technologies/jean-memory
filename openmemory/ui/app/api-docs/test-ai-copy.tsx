"use client";

import React from 'react';
import AICopyButton from '@/components/AICopyButton';
import { 
  generateQuickstartAIContent,
  generateSDKAIContent,
  generateMCPAIContent,
  generateRestAPIContent,
  generateExamplesAIContent
} from '@/utils/aiDocContent';

/**
 * Test page to demonstrate AI Quick Deploy functionality
 * This shows how AI agents can copy complete implementation guides
 */
export default function TestAICopyPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-4">AI Quick Deploy Test Page</h1>
          <p className="text-muted-foreground mb-8">
            Click any button below to copy a complete, AI-optimized implementation guide.
            Paste it into Claude, ChatGPT, or any AI assistant and say "implement this".
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-lg bg-white/5 border border-white/10">
            <h2 className="text-xl font-semibold mb-3">Quick Start Guide</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Complete 5-line implementation with all frameworks
            </p>
            <AICopyButton 
              content={generateQuickstartAIContent()}
              title="Copy Quick Start"
            />
          </div>

          <div className="p-6 rounded-lg bg-white/5 border border-white/10">
            <h2 className="text-xl font-semibold mb-3">SDK Reference</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Complete SDK documentation for React, Python, Node.js
            </p>
            <AICopyButton 
              content={generateSDKAIContent()}
              title="Copy SDK Reference"
            />
          </div>

          <div className="p-6 rounded-lg bg-white/5 border border-white/10">
            <h2 className="text-xl font-semibold mb-3">MCP Protocol</h2>
            <p className="text-sm text-muted-foreground mb-4">
              MCP implementation for Claude, ChatGPT, Cursor
            </p>
            <AICopyButton 
              content={generateMCPAIContent()}
              title="Copy MCP Guide"
            />
          </div>

          <div className="p-6 rounded-lg bg-white/5 border border-white/10">
            <h2 className="text-xl font-semibold mb-3">REST API</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Complete REST API reference with examples
            </p>
            <AICopyButton 
              content={generateRestAPIContent()}
              title="Copy API Reference"
            />
          </div>

          <div className="p-6 rounded-lg bg-white/5 border border-white/10 md:col-span-2">
            <h2 className="text-xl font-semibold mb-3">Production Examples</h2>
            <p className="text-sm text-muted-foreground mb-4">
              12+ complete, production-ready implementations
            </p>
            <AICopyButton 
              content={generateExamplesAIContent()}
              title="Copy All Examples"
            />
          </div>
        </div>

        <div className="mt-12 p-6 rounded-lg bg-blue-500/10 border border-blue-500/30">
          <h2 className="text-lg font-semibold mb-3">How This Works</h2>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Click any button to copy the complete implementation guide</li>
            <li>Open Claude, ChatGPT, or any AI coding assistant</li>
            <li>Paste the content and say "implement this"</li>
            <li>The AI will have everything needed to build a complete Jean Memory integration</li>
          </ol>
          <p className="mt-4 text-sm font-medium">
            This is the future of programming - AI-readable documentation that becomes instant implementations.
          </p>
        </div>

        <div className="mt-8 p-6 rounded-lg bg-green-500/10 border border-green-500/30">
          <h2 className="text-lg font-semibold mb-3">What's Included</h2>
          <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
            <li>Complete, runnable code examples</li>
            <li>Environment setup instructions</li>
            <li>API key configuration</li>
            <li>Error handling patterns</li>
            <li>Production deployment checklist</li>
            <li>Testing strategies</li>
            <li>Best practices and patterns</li>
          </ul>
        </div>
      </div>
    </div>
  );
}