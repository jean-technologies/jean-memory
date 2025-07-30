"use client";

import React, { useState, useEffect } from 'react';
import { App } from '@/store/appsSlice';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { MobileOptimizedDialog, MobileOptimizedDialogContent, MobileOptimizedDialogHeader, MobileOptimizedDialogTitle, MobileOptimizedDialogDescription } from '@/components/ui/mobile-optimized-dialog';
import { Copy, Check, Key, Shield, Loader2, MessageSquareText, Info, Download } from 'lucide-react';
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/use-toast";
import { constants } from "@/components/shared/source-app";
import Image from 'next/image';
import apiClient from '@/lib/apiClient';
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

interface InstallModalProps {
  app: App | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSyncStart: (appId: string, taskId: string) => void;
}

type VerificationStatus = 'idle' | 'sending' | 'sent' | 'verifying' | 'verified' | 'error';

export function InstallModal({ app, open, onOpenChange, onSyncStart }: InstallModalProps) {
  const [copied, setCopied] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [hasConsented, setHasConsented] = useState(false);
  const [status, setStatus] = useState<VerificationStatus>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadExtension = () => {
    // Download the HTTP v2 extension (faster transport)
    const backendUrl = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8765' 
      : 'https://jean-memory-api-virginia.onrender.com';
    window.open(`${backendUrl}/download/claude-extension-http`, '_blank');
    
    toast({
      title: "Download Started", 
      description: "The Claude Desktop Extension is downloading. Double-click the file to install.",
    });
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
        // Twitter uses query parameters
        const params = { username: inputValue.replace('@', ''), max_posts: 40 };
        response = await apiClient.post(endpoint, null, { params });
      } else {
        // Substack uses POST body
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

  const handleSendCode = async () => {
    if (!phoneNumber || !hasConsented) return;
    setStatus('sending');
    setErrorMessage('');
    try {
      await apiClient.post('/api/v1/profile/phone/add', { phone_number: phoneNumber });
      setStatus('sent');
      toast({
        title: "Verification Code Sent",
        description: "Check your phone for a 6-digit code.",
      });
    } catch (error: any) {
      const detail = error.response?.data?.detail || "An unexpected error occurred.";
      setErrorMessage(detail);
      setStatus('error');
      toast({
        variant: "destructive",
        title: "Failed to Send Code",
        description: detail,
      });
    }
  };

  const handleVerifyCode = async () => {
    if (!verificationCode) return;
    setStatus('verifying');
    setErrorMessage('');
    try {
      await apiClient.post('/api/v1/profile/phone/verify', { verification_code: verificationCode });
      setStatus('verified');
      toast({
        title: "Success!",
        description: "Your phone number has been verified.",
        className: "bg-green-500 text-white",
      });
      // Close modal after a short delay
      setTimeout(() => onOpenChange(false), 1500);
    } catch (error: any) {
      const detail = error.response?.data?.detail || "An unexpected error occurred.";
      setErrorMessage(detail);
      setStatus('error');
      toast({
        variant: "destructive",
        title: "Verification Failed",
        description: detail,
      });
    }
  };
  
  // Reset state when modal is closed or app changes
  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setPhoneNumber('');
        setVerificationCode('');
        setHasConsented(false);
        setStatus('idle');
        setErrorMessage('');
      }, 300);
    }
  }, [open]);

  if (!app) return null;

  const appConfig = constants[app.id as keyof typeof constants] || constants.default;
  
  // Most clients use HTTP (actual API URL), only specific clients need SSE (Cloudflare Worker)
  const needsSSE = ['vscode', 'chatgpt'].includes(app.id);
  const MCP_URL = needsSSE ? "https://api.jeanmemory.com" : (process.env.NEXT_PUBLIC_API_URL || "https://jean-memory-api-dev.onrender.com");

  // Define a base command that can be used as a fallback, fixing the regression.
  let rawInstallCommand = app.installCommand;
  if (!rawInstallCommand) {
    if (app.id === 'chorus') {
      rawInstallCommand = `-y mcp-remote ${MCP_URL}/mcp/${app.id}/sse/{user_id} --header "x-user-id:{user_id}" --header "x-client-name:chorus"`;
    } else if (app.id === 'claude') {
      // Use HTTP v2 transport for Claude (50% faster)
      rawInstallCommand = `npx -y supergateway --stdio ${MCP_URL}/mcp/v2/claude/{user_id}`;
    } else if (app.id === 'cursor') {
      // Use proper npx install-mcp command for Cursor
      rawInstallCommand = `npx install-mcp "${MCP_URL}/mcp/cursor/sse/{user_id}" --client cursor`;
    } else if (app.id === 'claude code') {
      // Use claude-code as client name (with hyphen, not space) and proper URL quoting
      rawInstallCommand = `npx install-mcp "${MCP_URL}/mcp/claude code/sse/{user_id}" --client claude-code`;
    } else {
      rawInstallCommand = `npx install-mcp "${MCP_URL}/mcp/${app.id}/sse/{user_id}" --client ${app.id}`;
    }
  }
  
  // Handle the special case for Chorus with a multi-part command
  if (app.id === 'chorus' && rawInstallCommand && rawInstallCommand.includes('#')) {
    const parts = rawInstallCommand.split('#');
    // Extract the args part for Chorus
    const currentUserId = user?.id || '';
    rawInstallCommand = currentUserId ? parts[1].replace(/\{USER_ID\}/g, currentUserId) : parts[1];
  }
  
  // Ensure we have a valid user ID before replacing
  const currentUserId = user?.id || '';
  
  // Debug logging to help troubleshoot
  console.log('InstallModal Debug:', { 
    userId: currentUserId, 
    rawCommand: rawInstallCommand,
    hasUser: !!user
  });
  
  const installCommand = currentUserId ? rawInstallCommand
    .replace(/\{user_id\}/g, currentUserId)
    .replace(/\{USER_ID\}/g, currentUserId) : rawInstallCommand;
    
  const mcpLink = `${MCP_URL}/mcp/openmemory/sse/${user?.id}`;
  const chatgptLink = `${MCP_URL}/mcp/chatgpt/sse/${user?.id}`;

  const userId = user?.id || '{YOUR_USER_ID}'; // Fallback for display

  const vscodeEnableSettings = {
    "chat.mcp.enabled": true,
    "chat.mcp.discovery.enabled": true
  };

  const vscodeMcpConfig = {
    "servers": {
      "jean-memory": {
        "type": "sse",
        "url": `https://api.jeanmemory.com/mcp/vscode/sse/${userId}`
      }
    }
  };

  return (
    <MobileOptimizedDialog open={open} onOpenChange={onOpenChange}>
      <MobileOptimizedDialogContent 
        className="sm:max-w-lg bg-card text-card-foreground border shadow-2xl shadow-blue-500/10"
        onOpenChange={onOpenChange}
      >
        <MobileOptimizedDialogHeader className="text-center pb-4">
          <div className="mx-auto w-16 h-16 rounded-lg bg-muted border flex items-center justify-center mb-4">
            {app.id === 'sms' ? (
                <MessageSquareText className="w-9 h-9 text-primary" />
            ) : app.imageUrl ? (
                <Image src={app.imageUrl} alt={app.name} width={36} height={36} />
            ) : appConfig.iconImage ? (
                <Image src={appConfig.iconImage} alt={app.name} width={36} height={36} />
            ) : (
                <div className="w-9 h-9 flex items-center justify-center">{appConfig.icon}</div>
            )}
          </div>
          <MobileOptimizedDialogTitle className="text-2xl font-bold">
            {app.id === 'mcp-generic' ? 'Your Universal MCP Link' : 
             app.id === 'chatgpt' ? 'Connect to ChatGPT Deep Research' :
             app.id === 'sms' ? 'Text Jean Memory' :
             `Connect to ${app.name}`}
          </MobileOptimizedDialogTitle>
          <MobileOptimizedDialogDescription className="text-muted-foreground pt-1">
            {app.id === 'mcp-generic'
                ? 'Use this URL for any MCP-compatible application.'
                : app.id === 'chatgpt'
                ? 'Add Jean Memory to ChatGPT Deep Research. Enterprise account required.'
                : app.id === 'substack' || app.id === 'twitter'
                ? `Provide your ${app.name} details to sync your content.`
                : app.id === 'sms'
                ? 'Add your phone number to interact with your memories via text message.'
                : `Jean Memory tracks your projects and builds a working memory.`
            }
          </MobileOptimizedDialogDescription>
        </MobileOptimizedDialogHeader>

        {app.id === 'mcp-generic' ? (
            <div className="py-2 text-center">
                <p className="text-muted-foreground text-sm mb-4">
                    Copy this URL and paste it into any MCP-compatible application to connect it with Jean Memory.
                </p>
                <div className="relative group bg-background border rounded-md p-3 font-mono text-xs text-foreground flex items-center justify-between">
                    <code style={{ wordBreak: 'break-all' }}>{mcpLink}</code>
                    <Button variant="ghost" className="ml-4 text-muted-foreground hover:text-foreground" onClick={() => handleCopy(mcpLink)}>
                        {copied ? (
                            <>
                                <Check className="h-4 w-4 mr-2 text-green-400" />
                                Copied!
                            </>
                        ) : (
                             <>
                                <Copy className="h-4 w-4 mr-2" />
                                Copy
                            </>
                        )}
                    </Button>
                </div>
            </div>
        ) : app.id === 'chatgpt' ? (
            <div className="py-2 text-center space-y-4">
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700/50 rounded-md p-3 mb-4">
                    <p className="text-yellow-800 dark:text-yellow-300 text-sm font-medium mb-1">⚠️ Admin Setup Required</p>
                    <p className="text-yellow-700 dark:text-yellow-200/80 text-xs">
                        A workspace admin needs to add this connector in ChatGPT settings.
                    </p>
                </div>
                <p className="text-muted-foreground text-sm mb-4">
                    Copy this MCP Server URL for your admin to add in ChatGPT workspace settings.
                </p>
                <div className="relative group bg-background border rounded-md p-3 font-mono text-xs text-foreground flex items-center justify-between">
                    <code style={{ wordBreak: 'break-all' }}>{chatgptLink}</code>
                    <Button variant="ghost" className="ml-4 text-muted-foreground hover:text-foreground" onClick={() => handleCopy(chatgptLink)}>
                        {copied ? (
                            <>
                                <Check className="h-4 w-4 mr-2 text-green-400" />
                                Copied!
                            </>
                        ) : (
                             <>
                                <Copy className="h-4 w-4 mr-2" />
                                Copy
                            </>
                        )}
                    </Button>
                </div>
                <div className="text-left mt-4 space-y-2">
                    <p className="text-foreground text-sm font-medium">For your admin:</p>
                    <ol className="text-muted-foreground text-xs space-y-1 ml-4">
                        <li>1. Go to ChatGPT workspace settings</li>
                        <li>2. Navigate to "Deep Research" or "Connectors"</li>
                        <li>3. Click "Add new connector"</li>
                        <li>4. Paste the MCP Server URL above</li>
                        <li>5. Set Authentication to "No authentication"</li>
                        <li>6. Save the connector</li>
                    </ol>
                </div>
            </div>
        ) : app.id === 'cursor' ? (
            <div className="py-2 space-y-6">
                {/* One-Click Install Button */}
                <Button 
                    onClick={() => {
                        const mcpConfig = {
                            "url": `https://jean-memory-api-virginia.onrender.com/mcp/v2/cursor/${user?.id}`,
                            "env": {}
                        };
                        const encodedConfig = btoa(JSON.stringify(mcpConfig));
                        const deepLink = `cursor://anysphere.cursor-deeplink/mcp/install?name=jean-memory&config=${encodedConfig}`;
                        window.open(deepLink, '_blank');
                        
                        toast({
                            title: "Opening Cursor", 
                            description: "Cursor should now prompt you to install Jean Memory.",
                        });
                    }}
                    className="w-full"
                    variant="default"
                >
                    <Download className="mr-2 h-4 w-4" />
                    Add Jean Memory to Cursor
                </Button>
                
                <div className="text-center">
                    <p className="text-xs text-muted-foreground mb-2">
                        One-click install for Cursor IDE
                    </p>
                </div>
                
                {/* Jean Memory Benefits */}
                <div className="bg-muted/50 rounded-lg p-4 space-y-2">
                    <h4 className="text-sm font-medium text-foreground">💭 Memory Across Sessions</h4>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                        Jean Memory tracks your projects and builds a working memory that persists across chat sessions. 
                        Your AI assistant will remember context from previous conversations, making each interaction more intelligent and productive.
                    </p>
                    <div className="flex items-start gap-2 mt-3">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                        <p className="text-xs text-muted-foreground">Ask questions about your codebase from weeks ago</p>
                    </div>
                    <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                        <p className="text-xs text-muted-foreground">Get contextual suggestions based on your project history</p>
                    </div>
                    <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 flex-shrink-0"></div>
                        <p className="text-xs text-muted-foreground">Build up knowledge that improves over time</p>
                    </div>
                </div>
            </div>
        ) : app.id === 'claude' ? (
            <div className="py-2 space-y-6">
                {/* OAuth Connection Button */}
                <Button 
                    onClick={() => window.open('https://jean-memory-api-dev.onrender.com/oauth/authorize?client_id=unknown_oRV4P34GULT7dfs1eI3Qqw&response_type=code&redirect_uri=https%3A%2F%2Fclaude.ai%2Fapi%2Fmcp%2Fauth_callback&scope=read+write&state=claude-connection', '_blank')}
                    className="w-full"
                    variant="default"
                >
                    <Shield className="mr-2 h-4 w-4" />
                    Connect to Claude
                </Button>
                
                {/* Connection Instructions */}
                <div className="space-y-2">
                    <h3 className="font-medium text-foreground">OAuth Connection</h3>
                    <p className="text-sm text-muted-foreground">Click the button above to authorize Claude to access your Jean Memory data securely.</p>
                </div>
                
                {/* Simple Steps */}
                <div className="space-y-2">
                    <h3 className="font-medium text-foreground">Setup Steps</h3>
                    <ol className="text-sm text-muted-foreground space-y-1">
                        <li>1. Click "Connect to Claude" above</li>
                        <li>2. Sign in with your Jean Memory account</li>
                        <li>3. Authorize Claude to access your memories</li>
                        <li>4. Start using Jean Memory in Claude!</li>
                    </ol>
                </div>
                
                {/* Manual Setup Option */}
                <details className="group">
                    <summary className="text-sm text-muted-foreground cursor-pointer hover:text-foreground">
                        Need manual terminal setup instead?
                    </summary>
                    <div className="mt-3 space-y-3">
                        <div className="relative bg-background border rounded-md p-3 font-mono text-xs break-all">
                            <div className="pr-12">{installCommand}</div>
                            <Button 
                                variant="ghost" 
                                size="sm"
                                className="absolute right-1 top-1/2 -translate-y-1/2" 
                                onClick={() => handleCopy(installCommand)}
                            >
                                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                            </Button>
                        </div>
                        <p className="text-xs text-muted-foreground">Run this command in terminal, then restart Claude Desktop.</p>
                    </div>
                </details>
            </div>
        ) : app.id === 'vscode' ? (
            <div className="py-2 space-y-4 text-left">
                <p className="text-muted-foreground text-sm mb-4">
                    VS Code has native MCP support. Just add a configuration file and enable MCP.
                </p>
                
                <div className="space-y-3">
                    <div>
                        <h3 className="font-medium text-foreground mb-2">1. Enable MCP in Settings</h3>
                        <p className="text-xs text-muted-foreground mb-2">Add to your settings.json:</p>
                        <div className="relative bg-background border rounded-md overflow-hidden">
                            <div className="overflow-x-auto">
                                <pre className="p-3 pr-12 font-mono text-xs text-foreground min-w-0"><code className="whitespace-pre-wrap break-words">{JSON.stringify(vscodeEnableSettings, null, 2)}</code></pre>
                            </div>
                            <Button 
                                variant="ghost" 
                                size="sm"
                                className="absolute right-1 top-1 bg-background/80 backdrop-blur-sm border" 
                                onClick={() => handleCopy(JSON.stringify(vscodeEnableSettings, null, 2))}
                            >
                                {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>

                    <div>
                        <h3 className="font-medium text-foreground mb-2">2. Create .vscode/mcp.json</h3>
                        <p className="text-xs text-muted-foreground mb-2">Add this file to your project root:</p>
                        <div className="relative bg-background border rounded-md overflow-hidden">
                            <div className="overflow-x-auto">
                                <pre className="p-3 pr-12 font-mono text-xs text-foreground min-w-0"><code className="whitespace-pre-wrap break-words">{JSON.stringify(vscodeMcpConfig, null, 2)}</code></pre>
                            </div>
                            <Button 
                                variant="ghost" 
                                size="sm"
                                className="absolute right-1 top-1 bg-background/80 backdrop-blur-sm border" 
                                onClick={() => handleCopy(JSON.stringify(vscodeMcpConfig, null, 2))}
                            >
                                {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>
                </div>

                <div className="bg-muted border rounded-md p-3 mt-4">
                    <div className="flex items-start">
                        <Info className="h-4 w-4 text-muted-foreground mt-0.5 mr-2 flex-shrink-0"/>
                        <div>
                            <p className="font-medium text-foreground mb-2">Next Steps</p>
                            <ol className="text-muted-foreground text-xs space-y-1 ml-4">
                                <li>1. Restart VS Code completely</li>
                                <li>2. Open Chat (Ctrl/Cmd + Alt + I) → Agent mode</li>
                                <li>3. Click "Trust" when prompted</li>
                                <li>4. Click "Tools" to see Jean Memory</li>
                            </ol>
                        </div>
                    </div>
                </div>
            </div>
        ) : app.id === 'substack' || app.id === 'twitter' ? (
            <div className="py-2 space-y-4">
                <p className="text-muted-foreground text-center text-sm">
                    Enter your {app.name === 'X' ? 'username' : 'URL'} below. This allows Jean Memory to find and sync your content.
                </p>
                <div className="flex items-center gap-4">
                  <Input
                    type="text"
                    placeholder={app.id === 'twitter' ? '@username' : 'your.substack.com'}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    className="bg-background"
                    disabled={isLoading}
                  />
                </div>
                <Button
                  onClick={handleSync}
                  disabled={isLoading || !inputValue}
                  className="w-full"
                  variant="secondary"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Syncing...
                    </>
                  ) : (
                    "Connect and Sync"
                  )}
                </Button>
            </div>
        ) : app.id === 'sms' ? (
            <div className="sm:contents max-sm:space-y-4">
              <div className="py-2 space-y-4 text-left">
                {status !== 'sent' && status !== 'verifying' ? (
                  <>
                    <div className="space-y-1">
                        <Label htmlFor="phone-number" className="text-sm font-medium text-foreground">Phone Number *</Label>
                        <Input
                          id="phone-number"
                          type="tel"
                          placeholder="(555) 123-4567"
                          value={phoneNumber}
                          onChange={(e) => setPhoneNumber(e.target.value)}
                          className="bg-background"
                          disabled={status === 'sending'}
                        />
                        <p className="text-xs text-muted-foreground pt-1">US phone numbers only. Message & data rates may apply.</p>
                    </div>

                    <div className="bg-muted border rounded-lg p-3 text-sm mt-4">
                      <div className="flex items-start">
                        <Info className="h-4 w-4 text-muted-foreground mt-0.5 mr-2 flex-shrink-0"/>
                        <div>
                          <p className="font-semibold text-foreground mb-2">Text Your Memory Assistant:</p>
                          <ul className="list-disc list-inside text-muted-foreground space-y-1 text-xs">
                              <li>Text like talking to a trusted friend who remembers everything!</li>
                              <li>"Remember I had a great meeting with Sarah today"</li>
                              <li>"What do I remember about my anxiety triggers?"</li>
                              <li>"How do my work meetings usually go?"</li>
                              <li>"Analyze patterns in my mood over time"</li>
                              <li>Text "help" anytime for more examples.</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    <div className="items-top flex space-x-3 pt-4">
                        <Checkbox
                            id="terms-sms"
                            checked={hasConsented}
                            onCheckedChange={(checked) => setHasConsented(checked as boolean)}
                            className="data-[state=checked]:bg-primary border-border mt-0.5"
                            disabled={status === 'sending'}
                        />
                        <div className="grid gap-1.5 leading-none">
                            <label
                              htmlFor="terms-sms"
                              className="text-xs text-muted-foreground font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                            >
                              I accept the <a href="/sms-terms" target="_blank" rel="noopener noreferrer" className="underline hover:text-primary">SMS Terms of Service</a> & <a href="https://jonathan-politzki.github.io/jean-privacy-policy/" target="_blank" rel="noopener noreferrer" className="underline hover:text-primary">Privacy Policy</a>.
                            </label>
                        </div>
                    </div>

                    <p className="text-xs text-muted-foreground pt-3">
                      By providing your phone number, you agree to receive informational text messages from Jean Memory. Consent is not a condition of purchase. Messages Frequency will vary. Msg & data rates may apply. Reply HELP for help or STOP to cancel.
                    </p>
                  </>
                ) : (
                  <div className="space-y-2 pt-2 text-center">
                      <Label htmlFor="verification-code" className="text-sm font-medium text-foreground">Enter Verification Code</Label>
                      <p className="text-xs text-muted-foreground pb-2">A 6-digit code was sent to {phoneNumber}.</p>
                      <Input
                        id="verification-code"
                        type="text"
                        placeholder="123456"
                        value={verificationCode}
                        onChange={(e) => setVerificationCode(e.target.value)}
                        className="bg-background text-center text-lg tracking-widest"
                        maxLength={6}
                        disabled={['verifying', 'verified'].includes(status)}
                      />
                  </div>
                )}
                
                {errorMessage && (
                  <div className="text-center text-sm text-red-500 bg-red-500/10 p-2 rounded-md">
                      {errorMessage}
                  </div>
                )}

                {status === 'verified' && (
                  <div className="text-center text-sm text-green-500 font-semibold pt-2">
                      ✓ Verified! You can now use SMS.
                  </div>
                )}
              </div>
            </div>
        ) : app.id === 'claude code' ? (
            <div className="py-2 space-y-4 text-left">
                <p className="text-muted-foreground text-sm mb-4">
                    Add Jean Memory as an MCP server to Claude Code for persistent memory across all your coding sessions.
                </p>
                
                <div className="space-y-4">
                    <div>
                        <h3 className="font-medium text-foreground mb-2">1. Add MCP Server</h3>
                        <p className="text-xs text-muted-foreground mb-2">Run this command in your terminal:</p>
                        <div className="relative bg-background border rounded-md">
                            <div className="overflow-x-auto p-3 pr-12 font-mono text-xs text-foreground">
                                <code className="whitespace-pre-wrap break-words">{installCommand}</code>
                            </div>
                            <Button 
                                variant="ghost" 
                                size="sm"
                                className="absolute right-1 top-1/2 -translate-y-1/2" 
                                onClick={() => handleCopy(installCommand)}
                            >
                                {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
                            </Button>
                        </div>
                    </div>

                    <div>
                        <h3 className="font-medium text-foreground mb-2">2. Verify Installation</h3>
                        <p className="text-xs text-muted-foreground mb-2">Check that the server is active:</p>
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
                    </div>
                </div>

                <div className="bg-muted rounded-md p-3">
                    <p className="text-foreground text-xs font-medium mb-2">Continuous Memory Mode</p>
                    <p className="text-muted-foreground text-xs mb-3">
                        For automatic memory saving, start each Claude Code conversation by pasting this prompt:
                    </p>
                    <div className="relative bg-background border rounded-md">
                        <div className="overflow-x-auto p-2 pr-10 font-mono text-xs text-foreground">
                            <code className="whitespace-pre-wrap break-words">ALWAYS use the @add_memories tool FIRST for every single message I send to save our conversation, then provide your response.</code>
                        </div>
                        <Button 
                            variant="ghost" 
                            size="sm"
                            className="absolute right-1 top-1/2 -translate-y-1/2" 
                            onClick={() => handleCopy("ALWAYS use the @add_memories tool FIRST for every single message I send to save our conversation, then provide your response.")}
                        >
                            <Copy className="h-3 w-3" />
                        </Button>
                    </div>
                    <p className="text-muted-foreground text-xs mt-2">
                        <strong>Note:</strong> Copy and paste this at the start of each new conversation. Claude Code doesn't currently support persistent system prompts.
                    </p>
                </div>

                <div className="bg-muted border rounded-md p-3 mt-4">
                    <div className="flex items-start">
                        <Info className="h-4 w-4 text-muted-foreground mt-0.5 mr-2 flex-shrink-0"/>
                        <div>
                            <p className="font-medium text-foreground mb-2">Available Tools</p>
                            <ul className="text-muted-foreground text-xs space-y-1">
                                <li>• @jean_memory - Smart context with auto-save</li>
                                <li>• @search_memory - Find past conversations</li>
                                <li>• @ask_memory - Query your knowledge</li>
                                <li>• @store_document - Save large files</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        ) : app.id === 'chorus' ? (
          <div className="space-y-4 py-2">
            <ol className="list-decimal list-inside space-y-3 text-muted-foreground text-sm">
              <li>{app.modalContent}</li>
              <li>
                In the <code className="bg-muted px-1.5 py-0.5 rounded-md font-mono text-xs border">Command</code> field, enter: <code className="bg-muted px-1.5 py-0.5 rounded-md font-mono text-xs border">npx</code>
              </li>
              <li>
                In the <code className="bg-muted px-1.5 py-0.5 rounded-md font-mono text-xs border">Arguments</code> field, paste the following:
                <div className="relative mt-2">
                  <Input
                    id="chorus-args"
                    readOnly
                    value={installCommand}
                    className="bg-background border-border text-foreground font-mono text-xs pr-10"
                  />
                  <Button variant="ghost" size="icon" className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 text-muted-foreground hover:text-foreground" onClick={() => handleCopy(installCommand)}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </li>
            </ol>
          </div>
        ) : (
            <div className="space-y-6 py-2">
                <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <Key className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                    <h3 className="font-semibold text-md text-foreground">1. Run Install Command</h3>
                    <p className="text-muted-foreground text-sm mb-3">
                        Open your terminal and paste this command:
                    </p>
                    <div className="relative group bg-background border rounded-md p-3 font-mono text-xs text-foreground flex items-center justify-between">
                        <code style={{ wordBreak: 'break-all' }}>{installCommand}</code>
                        <Button variant="ghost" className="ml-4 text-muted-foreground hover:text-foreground" onClick={() => handleCopy(installCommand)}>
                           {copied ? (
                            <>
                                <Check className="h-4 w-4 mr-2 text-green-400" />
                                Copied!
                            </>
                        ) : (
                             <>
                                <Copy className="h-4 w-4 mr-2" />
                                Copy
                            </>
                        )}
                        </Button>
                    </div>
                    </div>
                </div>
                
                <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <Shield className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-md text-foreground">2. Restart {app.name}</h3>
                        <p className="text-muted-foreground text-sm">
                        After the command completes, restart the {app.name} application. Jean Memory will be active.
                        </p>
                    </div>
                </div>
            </div>
        )}
        
        {app.id === 'sms' ? (
            <div className="mt-6 flex justify-end gap-3 max-sm:flex-col max-sm:space-y-2 max-sm:px-4 max-sm:pb-4 max-sm:bg-background max-sm:border-t max-sm:border-border max-sm:-mx-4 max-sm:-mb-4 max-sm:mt-4">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                    Cancel
                </Button>
                {status !== 'sent' && status !== 'verifying' ? (
                  <Button
                    onClick={handleSendCode}
                    disabled={!phoneNumber || !hasConsented || status === 'sending'}
                    variant="secondary"
                  >
                    {status === 'sending' ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending...</> : 'Send Code'}
                  </Button>
                ) : (
                  <Button
                    onClick={handleVerifyCode}
                    disabled={verificationCode.length !== 6 || ['verifying', 'verified'].includes(status)}
                    variant="secondary"
                  >
                    {status === 'verifying' ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Verifying...</> : 'Verify'}
                  </Button>
                )}
            </div>
        ) : (
          <div className="mt-6 text-center">
              <Button
                  variant="secondary"
                  onClick={() => onOpenChange(false)}
                  className="w-full sm:w-auto"
              >
                  Done
              </Button>
          </div>
        )}
      </MobileOptimizedDialogContent>
    </MobileOptimizedDialog>
  );
} 