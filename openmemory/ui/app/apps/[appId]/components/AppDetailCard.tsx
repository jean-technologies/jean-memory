import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PauseIcon, Loader2, PlayIcon, Download, Copy } from "lucide-react";
import { BiEdit } from "react-icons/bi";
import { useAppsApi } from "@/hooks/useAppsApi";
import Image from "next/image";
import { useDispatch, useSelector } from "react-redux";
import { setAppDetails } from "@/store/appsSlice";
import { constants } from "@/components/shared/source-app";
import { RootState } from "@/store/store";
import { toast } from "@/components/ui/use-toast";
import { useAuth } from "@/contexts/AuthContext";

const capitalize = (str: string) => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

const AppDetailCard = ({
  appId,
  selectedApp,
}: {
  appId: string;
  selectedApp: any;
}) => {
  const { updateAppDetails } = useAppsApi();
  const [isLoading, setIsLoading] = useState(false);
  const dispatch = useDispatch();
  const apps = useSelector((state: RootState) => state.apps.apps);
  const { user } = useAuth();
  const currentApp = apps.find((app: any) => app.id === appId);
  const appConfig = currentApp
    ? constants[currentApp.name as keyof typeof constants] || constants.default
    : constants.default;

  const handlePauseAccess = async () => {
    setIsLoading(true);
    try {
      await updateAppDetails(appId, {
        is_active: !selectedApp.details.is_active,
      });
      dispatch(
        setAppDetails({ appId, isActive: !selectedApp.details.is_active })
      );
    } catch (error) {
      console.error("Failed to toggle app pause state:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const buttonText = selectedApp.details.is_active
    ? "Pause Access"
    : "Unpause Access";


  const handleDownloadExtension = () => {
    // Download the HTTP v2 extension
    const backendUrl = process.env.NODE_ENV === 'development' 
      ? 'http://localhost:8765' 
      : 'https://jean-memory-api-virginia.onrender.com';
    window.open(`${backendUrl}/download/claude-extension-http`, '_blank');
    
    toast({
      title: "Download Started",
      description: "The Claude Desktop Extension is downloading. Double-click the file to install.",
    });
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied to clipboard",
      description: "Install command copied successfully.",
    });
  };

  return (
    <div>
      <div className="bg-card border w-full sm:w-[320px] border-border rounded-xl mb-6">
        <div className="flex items-center gap-2 mb-4 bg-muted rounded-t-xl p-3">
          <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center overflow-hidden">
            <Image
              src={
                constants[appId as keyof typeof constants]?.iconImage || ""
              }
              alt="Jean Memory"
              width={24}
              height={24}
            />
          </div>
          <p className="text-sm font-semibold text-foreground">
            {constants[appId as keyof typeof constants]?.name}
          </p>
        </div>

        <div className="space-y-4 p-3">
          <div>
            <p className="text-xs text-muted-foreground">Access Status</p>
            <p
              className={`font-medium ${
                selectedApp.details.is_active
                  ? "text-emerald-500"
                  : "text-red-500"
              }`}
            >
              {capitalize(
                selectedApp.details.is_active ? "active" : "inactive"
              )}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">Total Memories Created</p>
            <p className="font-medium text-foreground">
              {selectedApp.details.total_memories_created} Memories
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">Total Memories Accessed</p>
            <p className="font-medium text-foreground">
              {selectedApp.details.total_memories_accessed} Memories
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">First Accessed</p>
            <p className="font-medium text-foreground">
              {selectedApp.details.first_accessed
                ? new Date(
                    selectedApp.details.first_accessed
                  ).toLocaleDateString("en-US", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "numeric",
                    minute: "numeric",
                  })
                : "Never"}
            </p>
          </div>

          <div>
            <p className="text-xs text-muted-foreground">Last Accessed</p>
            <p className="font-medium text-foreground">
              {selectedApp.details.last_accessed
                ? new Date(
                    selectedApp.details.last_accessed
                  ).toLocaleDateString("en-US", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                    hour: "numeric",
                    minute: "numeric",
                  })
                : "Never"}
            </p>
          </div>

          <hr className="border-border" />

          {currentApp?.name?.toLowerCase() === 'claude' ? (
            <div>
              <p className="text-xs text-muted-foreground mb-2">Desktop Extension</p>
              <Button 
                onClick={handleDownloadExtension}
                className="w-full mb-2"
                variant="secondary"
                size="sm"
              >
                <Download className="mr-2 h-4 w-4" />
                Download Extension
              </Button>
              <p className="text-xs text-muted-foreground mb-3">
                One-click install for Claude Desktop
              </p>
              
              {/* Manual Install Command section hidden for Claude Desktop 
              <details className="mt-4">
                <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground transition-colors">
                  Manual Install Command
                </summary>
                <div className="mt-2 space-y-2">
                  <p className="text-xs text-muted-foreground">
                    For advanced users: copy and run this command
                  </p>
                  <div className="flex gap-2">
                    <Input
                      value={`curl -o claude-extension.zip "${process.env.NODE_ENV === 'development' ? 'http://localhost:8765' : 'https://jean-memory-api-virginia.onrender.com'}/download/claude-extension-http" && unzip claude-extension.zip && open claude-extension.mcp`}
                      readOnly
                      className="text-xs font-mono"
                    />
                    <Button
                      onClick={() => handleCopy(`curl -o claude-extension.zip "${process.env.NODE_ENV === 'development' ? 'http://localhost:8765' : 'https://jean-memory-api-virginia.onrender.com'}/download/claude-extension-http" && unzip claude-extension.zip && open claude-extension.mcp`)}
                      size="sm"
                      variant="outline"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </details>
              */}
            </div>
          ) : null}

          {currentApp?.name?.toLowerCase() === 'claude code' ? (
            <div>
              <p className="text-xs text-muted-foreground mb-2">MCP Server Setup</p>
              
              <div className="space-y-3">
                <div>
                  <p className="text-xs font-semibold text-foreground mb-1">Step 1: Add MCP Server</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    Run this command in your terminal:
                  </p>
                  <div className="flex gap-2">
                    <Input
                      value={`claude mcp add jean-memory ${process.env.NODE_ENV === 'development' ? 'http://localhost:8765' : 'https://jean-memory-api-virginia.onrender.com'}/mcp/v2/claude/${user?.user_id || '{user_id}'} --scope local`}
                      readOnly
                      className="text-xs font-mono"
                    />
                    <Button
                      onClick={() => handleCopy(`claude mcp add jean-memory ${process.env.NODE_ENV === 'development' ? 'http://localhost:8765' : 'https://jean-memory-api-virginia.onrender.com'}/mcp/v2/claude/${user?.user_id || '{user_id}'} --scope local`)}
                      size="sm"
                      variant="outline"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                <div>
                  <p className="text-xs font-semibold text-foreground mb-1">Step 2: Verify Connection</p>
                  <p className="text-xs text-muted-foreground mb-2">
                    Check that the server is active:
                  </p>
                  <div className="flex gap-2">
                    <Input
                      value="claude mcp list"
                      readOnly
                      className="text-xs font-mono"
                    />
                    <Button
                      onClick={() => handleCopy("claude mcp list")}
                      size="sm"
                      variant="outline"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                <div className="bg-muted/50 rounded-md p-3">
                  <p className="text-xs font-semibold text-foreground mb-1">Available Tools:</p>
                  <ul className="text-xs text-muted-foreground space-y-0.5">
                    <li>• search_memory - Search your memories</li>
                    <li>• add_memories - Store new information</li>
                    <li>• ask_memory - AI-powered Q&A</li>
                    <li>• list_memories - Browse memories</li>
                    <li>• get_memory_details - Get specific memory info</li>
                  </ul>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
                  <p className="text-xs text-blue-700 dark:text-blue-300">
                    💡 <strong>Tip:</strong> Once connected, use @ mentions to access your memories directly in Claude Code conversations.
                  </p>
                </div>

                <div className="space-y-3 mt-4">
                  <details className="group">
                    <summary className="text-xs font-semibold text-foreground cursor-pointer hover:text-primary transition-colors flex items-center">
                      <span className="mr-2 transform group-open:rotate-90 transition-transform">▶</span>
                      Advanced: Continuous Memory Mode
                    </summary>
                    <div className="mt-3 space-y-3 pl-4">
                      <p className="text-xs text-muted-foreground">
                        To make Jean Memory automatically save everything from your Claude Code sessions, add this system prompt:
                      </p>
                      
                      <div className="bg-background border rounded-md p-2">
                        <div className="flex gap-2">
                          <Input
                            value="ALWAYS use the @add_memories tool FIRST for every single message I send to save our conversation, then provide your response."
                            readOnly
                            className="text-xs font-mono"
                          />
                          <Button
                            onClick={() => handleCopy("ALWAYS use the @add_memories tool FIRST for every single message I send to save our conversation, then provide your response.")}
                            size="sm"
                            variant="outline"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>

                      <div className="bg-muted rounded-md p-2">
                        <p className="text-xs text-muted-foreground">
                          <strong>How to set:</strong> In Claude Code, start your conversation with this prompt, or add it to your default system instructions if supported.
                        </p>
                      </div>

                      <div className="text-xs text-muted-foreground space-y-1">
                        <p><strong>Benefits:</strong></p>
                        <ul className="space-y-0.5 ml-3">
                          <li>• Automatically saves all code discussions</li>
                          <li>• Remembers your project context across sessions</li>
                          <li>• Builds persistent knowledge of your codebase</li>
                          <li>• Learns your coding patterns and preferences</li>
                        </ul>
                      </div>
                    </div>
                  </details>
                </div>
              </div>
            </div>
          ) : null}

          <div className="flex gap-2 justify-end">
            <Button
              onClick={handlePauseAccess}
              className="flex bg-transparent w-[170px] bg-muted border-border hover:bg-accent text-foreground"
              size="sm"
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : buttonText === "Pause Access" ? (
                <PauseIcon className="h-4 w-4" />
              ) : (
                <PlayIcon className="h-4 w-4" />
              )}
              {buttonText}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppDetailCard;
