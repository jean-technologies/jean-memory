"use client";
import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, Settings, ExternalLink } from "lucide-react";
import apiClient from "@/lib/apiClient";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

export function NotionIntegration() {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [workspaceName, setWorkspaceName] = useState("");
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Check Notion connection status on load
    const checkStatus = async () => {
      if (!user) return;
      setIsLoading(true);
      try {
        const response = await apiClient.get("/api/v1/integrations/notion/status");
        if (response.data.connected) {
          setIsConnected(true);
          setWorkspaceName(response.data.workspace?.workspace_name || "Connected Workspace");
        }
      } catch (error) {
        console.error("Error checking Notion status:", error);
      } finally {
        setIsLoading(false);
      }
    };
    checkStatus();
  }, [user]);

  const handleConnect = async () => {
    // Redirect to Notion OAuth flow
    try {
      const response = await apiClient.get("/api/v1/integrations/notion/auth");
      window.location.href = response.data.oauth_url;
    } catch (error) {
      console.error("Error starting Notion auth:", error);
    }
  };

  const handleDisconnect = async () => {
    // Disconnect Notion
    setIsLoading(true);
    try {
      await apiClient.delete("/api/v1/integrations/notion/disconnect");
      setIsConnected(false);
      setWorkspaceName("");
    } catch (error) {
      console.error("Error disconnecting Notion:", error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleManage = () => {
    router.push('/onboarding');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Notion Integration</span>
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : isConnected ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <p>Checking connection status...</p>
        ) : isConnected ? (
          <div className="space-y-4">
            <p>
              Connected to: <strong>{workspaceName}</strong>
            </p>
            <div className="flex space-x-2">
              <Button onClick={handleManage} variant="outline">
                <Settings className="mr-2 h-4 w-4" />
                Manage Pages
              </Button>
              <Button onClick={handleDisconnect} variant="destructive">
                Disconnect
              </Button>
            </div>
          </div>
        ) : (
          <div>
            <p className="mb-4">
              Connect your Notion workspace to sync your pages and notes into your memory.
            </p>
            <Button onClick={handleConnect}>
              <ExternalLink className="mr-2 h-4 w-4" />
              Connect to Notion
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
