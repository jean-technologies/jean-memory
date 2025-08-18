"use client";

import React, { useState } from 'react';
import { App } from '@/store/appsSlice';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { MobileOptimizedDialog, MobileOptimizedDialogContent, MobileOptimizedDialogHeader, MobileOptimizedDialogTitle, MobileOptimizedDialogDescription } from '@/components/ui/mobile-optimized-dialog';
import { Copy, Check, Loader2 } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import apiClient from '@/lib/apiClient';

interface InstallModalProps {
  app: App | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSyncStart: (appId: string, taskId: string) => void;
}

export function InstallModal({ app, open, onOpenChange, onSyncStart }: InstallModalProps) {
  const [copied, setCopied] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSync = async () => {
    if (!app || !inputValue) return;

    setIsLoading(true);

    try {
      const endpoint = app.id === 'twitter' 
        ? '/api/v1/integrations/sync/twitter' 
        : '/api/v1/integrations/substack/sync';
      
      let response;
      if (app.id === 'twitter') {
        const params = { username: inputValue.replace('@', ''), max_posts: 40 };
        response = await apiClient.post(endpoint, null, { params });
      } else {
        const data = { substack_url: inputValue, max_posts: 20 };
        response = await apiClient.post(endpoint, data);
      }
      
      onSyncStart(app.id, response.data.task_id);

      toast({
        title: "Sync Started",
        description: "This may take a few minutes. Set up some of your other apps.",
      });
      
      onOpenChange(false);

    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: error.response?.data?.detail || `Failed to connect ${app.name}. Please check the input and try again.`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!app) return null;

  const userId = user?.id || 'your-user-id';
  const MCP_URL = 'https://api.jeanmemory.com';

  // VSCode configuration objects
  const vscodeEnableSettings = {
    "mcp.enabled": true
  };

  const vscodeMcpConfig = {
    "jeanmemory": {
      "transport": "sse",
      "url": `https://api.jeanmemory.com/mcp/vscode/sse/${userId}`
    }
  };

  return (
    <MobileOptimizedDialog open={open} onOpenChange={onOpenChange}>
      <MobileOptimizedDialogContent className="overflow-y-auto max-h-[90vh]">
        <MobileOptimizedDialogHeader>
          <MobileOptimizedDialogTitle>Connect {app.name}</MobileOptimizedDialogTitle>
          <MobileOptimizedDialogDescription>
            {app.id === 'claude code' ? 'Connect Jean Memory to Claude Code via MCP' :
             app.id === 'vscode' ? 'Connect Jean Memory to VS Code via MCP' :
             `Connect your ${app.name} to Jean Memory`}
          </MobileOptimizedDialogDescription>
        </MobileOptimizedDialogHeader>
        
        <div className="space-y-4">
          {app.id === 'claude code' ? (
            <div className="py-2 text-left">
              <p className="text-muted-foreground text-sm mb-4">
                Jean Memory tracks your projects and builds a working memory.
              </p>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-foreground mb-2">1. Add MCP Server</h3>
                  <p className="text-xs text-muted-foreground mb-2">Add Jean Memory as an HTTP MCP server:</p>
                  <div className="relative bg-background border rounded-md">
                    <div className="overflow-x-auto p-3 pr-12 font-mono text-xs text-foreground">
                      <code className="whitespace-pre-wrap break-words">claude mcp add --transport http jean-memory {MCP_URL}/mcp</code>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="absolute right-1 top-1/2 -translate-y-1/2" 
                      onClick={() => handleCopy(`claude mcp add --transport http jean-memory ${MCP_URL}/mcp`)}
                    >
                      {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">OAuth authentication will be handled automatically by Claude</p>
                </div>

                <div>
                  <h3 className="font-medium text-foreground mb-2">2. Verify Installation</h3>
                  <p className="text-xs text-muted-foreground mb-2">Check that Jean Memory is active:</p>
                  <div className="relative bg-background border rounded-md">
                    <div className="overflow-x-auto p-3 pr-12 font-mono text-xs text-foreground">
                      <code>claude mcp list</code>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="absolute right-1 top-1/2 -translate-y-1/2" 
                      onClick={() => handleCopy("claude mcp list")}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">You should see "jean-memory" in the list of active servers.</p>
                </div>

                <div className="bg-muted rounded-md p-3 border">
                  <h4 className="font-medium text-foreground text-xs mb-2">Configuration Note</h4>
                  <p className="text-muted-foreground text-xs">
                    This command creates the same configuration as the Claude Desktop extension, 
                    ensuring identical functionality and API endpoints.
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-950/30 rounded-md p-3 border border-blue-200 dark:border-blue-800 mt-4">
                <p className="text-blue-800 dark:text-blue-200 text-xs font-medium mb-1">Your User ID</p>
                <p className="text-blue-700 dark:text-blue-300 text-xs mb-2">
                  Keep this ID for manual configuration if needed:
                </p>
                <div className="relative bg-white dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-md">
                  <div className="overflow-x-auto p-2 pr-10 font-mono text-xs text-blue-900 dark:text-blue-100">
                    <code>{userId}</code>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 p-0" 
                    onClick={() => handleCopy(userId)}
                  >
                    {copied ? <Check className="h-3 w-3 text-green-400" /> : <Copy className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
            </div>
          ) : app.id === 'vscode' ? (
            <div className="py-2 text-left">
              <p className="text-muted-foreground text-sm mb-4">
                VS Code has native MCP support. Just add a configuration file and enable MCP.
              </p>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-foreground mb-2">1. Enable MCP in settings.json</h3>
                  <p className="text-xs text-muted-foreground mb-2">Add this to your VS Code settings:</p>
                  <div className="relative bg-background border rounded-md">
                    <pre className="p-3 pr-12 font-mono text-xs text-foreground min-w-0">
                      <code className="whitespace-pre-wrap break-words">{JSON.stringify(vscodeEnableSettings, null, 2)}</code>
                    </pre>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="absolute right-1 top-1/2 -translate-y-1/2" 
                      onClick={() => handleCopy(JSON.stringify(vscodeEnableSettings, null, 2))}
                    >
                      {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div>
                  <h3 className="font-medium text-foreground mb-2">2. Create .vscode/mcp.json</h3>
                  <p className="text-xs text-muted-foreground mb-2">Add this configuration file to your project:</p>
                  <div className="relative bg-background border rounded-md">
                    <pre className="p-3 pr-12 font-mono text-xs text-foreground min-w-0">
                      <code className="whitespace-pre-wrap break-words">{JSON.stringify(vscodeMcpConfig, null, 2)}</code>
                    </pre>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      className="absolute right-1 top-1/2 -translate-y-1/2" 
                      onClick={() => handleCopy(JSON.stringify(vscodeMcpConfig, null, 2))}
                    >
                      {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>

                <div className="bg-muted rounded-md p-3 border">
                  <h4 className="font-medium text-foreground text-xs mb-2">Final Steps</h4>
                  <ul className="text-muted-foreground text-xs space-y-1">
                    <li>1. Restart VS Code completely</li>
                    <li>2. Open Command Palette (Cmd/Ctrl+Shift+P)</li>
                    <li>3. Run "MCP: Reload Servers"</li>
                  </ul>
                </div>
              </div>
            </div>
          ) : (
            // Other app types (Twitter, Substack, etc.)
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="input" className="text-sm font-medium">
                  {app.id === 'twitter' ? 'Twitter Username' : 'Substack URL'}
                </label>
                <Input
                  id="input"
                  type="text"
                  placeholder={app.id === 'twitter' ? '@username' : 'https://example.substack.com'}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  className="w-full"
                />
              </div>
              
              <Button 
                onClick={handleSync} 
                disabled={!inputValue || isLoading}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Syncing...
                  </>
                ) : (
                  `Connect ${app.name}`
                )}
              </Button>
            </div>
          )}
        </div>
      </MobileOptimizedDialogContent>
    </MobileOptimizedDialog>
  );
}