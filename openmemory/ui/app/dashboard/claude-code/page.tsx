"use client";

import { useState, useEffect } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { SessionManager } from "@/components/claude-code/SessionManager";
import { useProfile } from "@/hooks/useProfile";
import { ProtectedRoute } from "@/components/ProtectedRoute";

export default function ClaudeCodePage() {
  const { profile } = useProfile();
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Connection URL copied to clipboard");
  };

  const singleAgentUrl = profile?.user_id 
    ? `https://api.jeanmemory.com/mcp/claude%20code/sse/${profile.user_id}`
    : "Loading...";

  return (
    <ProtectedRoute>
      <div className="claude-code-page space-y-6">
      <div className="flex flex-col space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">Claude Code Integration</h1>
        <p className="text-muted-foreground">
          Manage multi-agent Claude Code sessions and connections for collaborative coding
        </p>
      </div>

      <div className="claude-code-content space-y-6">
        <div className="quick-start-section">
          <h2 className="text-xl font-semibold mb-4">Quick Start</h2>
          <p className="text-muted-foreground mb-4">
            Connect Claude Code to Jean Memory for persistent memory across coding sessions.
          </p>
          
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="mode-card">
              <CardHeader>
                <h3 className="text-lg font-medium">Single Agent Mode</h3>
                <p className="text-sm text-muted-foreground">Standard Claude Code connection</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="bg-muted p-3 rounded-md">
                  <code className="text-sm break-all">
                    npx install-mcp {singleAgentUrl} --client claude code
                  </code>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => copyToClipboard(singleAgentUrl)}
                  disabled={!profile?.user_id}
                  className="w-full"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copy URL
                </Button>
              </CardContent>
            </Card>
            
            <Card className="mode-card">
              <CardHeader>
                <h3 className="text-lg font-medium">Multi-Agent Mode</h3>
                <p className="text-sm text-muted-foreground">Collaborative sessions with multiple agents</p>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">
                  Create sessions below to generate agent-specific connection URLs
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Features:</span>
                  <span>• File claiming</span>
                  <span>• Agent coordination</span>
                  <span>• Change broadcasting</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
        
        <div className="border-t pt-6">
          <SessionManager />
        </div>
      </div>
    </div>
    </ProtectedRoute>
  );
}