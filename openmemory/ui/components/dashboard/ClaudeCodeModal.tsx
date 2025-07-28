"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Copy, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { SessionManager } from "@/components/claude-code/SessionManager";
import { useProfile } from "@/hooks/useProfile";

interface ClaudeCodeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ClaudeCodeModal({ open, onOpenChange }: ClaudeCodeModalProps) {
  const { profile } = useProfile();
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Command copied to clipboard");
  };

  const singleAgentUrl = profile?.user_id 
    ? `https://api.jeanmemory.com/mcp/claude%20code/sse/${profile.user_id}`
    : "Loading...";
    
  const singleAgentCommand = profile?.user_id
    ? `npx install-mcp ${singleAgentUrl} --client claude-code`
    : "Loading...";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">Claude Code Integration</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          <p className="text-muted-foreground">
            Manage multi-agent Claude Code sessions and connections for collaborative coding
          </p>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Quick Start</h3>
              <p className="text-muted-foreground mb-4">
                Connect Claude Code to Jean Memory for persistent memory across coding sessions.
              </p>
              
              <div className="grid md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <h4 className="text-md font-medium">Single Agent Mode</h4>
                    <p className="text-sm text-muted-foreground">Standard Claude Code connection</p>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="bg-muted p-3 rounded-md">
                      <code className="text-sm break-all">
                        {singleAgentCommand}
                      </code>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => copyToClipboard(singleAgentCommand)}
                      disabled={!profile?.user_id}
                      className="w-full"
                    >
                      <Copy className="w-4 h-4 mr-2" />
                      Copy Command
                    </Button>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <h4 className="text-md font-medium">Multi-Agent Mode</h4>
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
      </DialogContent>
    </Dialog>
  );
}