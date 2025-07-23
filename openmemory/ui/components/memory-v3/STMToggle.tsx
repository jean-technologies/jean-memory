"use client";

import React, { useState } from 'react';
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { 
  Brain, 
  Zap, 
  Cloud, 
  HardDrive, 
  Wifi, 
  WifiOff,
  AlertCircle,
  CheckCircle,
  Loader2,
  Settings,
} from "lucide-react";
import { isSTMSupported } from '@/lib/memory-v3';
import { useMemoriesApiV3 } from '@/hooks/useMemoriesApiV3';

interface STMToggleProps {
  className?: string;
}

export const STMToggle: React.FC<STMToggleProps> = ({ className }) => {
  const {
    isSTMEnabled,
    isSTMReady,
    enableSTM,
    disableSTM,
    getSTMStatus,
    isLoading,
    error,
  } = useMemoriesApiV3();

  const [isEnabling, setIsEnabling] = useState(false);
  const supported = isSTMSupported();
  const status = getSTMStatus();

  const handleToggle = async (enabled: boolean) => {
    if (enabled) {
      setIsEnabling(true);
      try {
        await enableSTM();
      } catch (error) {
        console.error('Failed to enable STM:', error);
      } finally {
        setIsEnabling(false);
      }
    } else {
      disableSTM();
    }
  };

  const getStatusInfo = () => {
    if (!supported) {
      return {
        icon: <AlertCircle className="h-4 w-4 text-red-500" />,
        text: "Not Supported",
        color: "bg-red-100 text-red-800",
      };
    }

    if (isEnabling) {
      return {
        icon: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
        text: "Initializing...",
        color: "bg-blue-100 text-blue-800",
      };
    }

    if (!isSTMEnabled) {
      return {
        icon: <HardDrive className="h-4 w-4 text-gray-500" />,
        text: "Disabled",
        color: "bg-gray-100 text-gray-800",
      };
    }

    if (!isSTMReady) {
      return {
        icon: <Loader2 className="h-4 w-4 animate-spin text-yellow-500" />,
        text: "Loading...",
        color: "bg-yellow-100 text-yellow-800",
      };
    }

    if (error) {
      return {
        icon: <AlertCircle className="h-4 w-4 text-red-500" />,
        text: "Error",
        color: "bg-red-100 text-red-800",
      };
    }

    return {
      icon: <CheckCircle className="h-4 w-4 text-green-500" />,
      text: "Ready",
      color: "bg-green-100 text-green-800",
    };
  };

  const statusInfo = getStatusInfo();

  return (
    <TooltipProvider>
      <div className={`flex items-center space-x-3 ${className}`}>
        {/* STM Toggle Switch */}
        <div className="flex items-center space-x-2">
          <Brain className="h-4 w-4 text-blue-600" />
          <Label htmlFor="stm-toggle" className="text-sm font-medium">
            Smart Memory
          </Label>
          <Switch
            id="stm-toggle"
            checked={isSTMEnabled}
            onCheckedChange={handleToggle}
            disabled={!supported || isEnabling || isLoading}
          />
        </div>

        {/* Status Badge */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge className={`flex items-center space-x-1 ${statusInfo.color}`}>
              {statusInfo.icon}
              <span className="text-xs">{statusInfo.text}</span>
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              <p className="font-medium">Smart Memory Status</p>
              {!supported && (
                <p className="text-sm text-red-600">
                  Your browser doesn't support local memory features
                </p>
              )}
              {supported && !isSTMEnabled && (
                <p className="text-sm">
                  Enable for instant memory access and offline capabilities
                </p>
              )}
              {isSTMEnabled && isSTMReady && status && (
                <div className="text-sm space-y-1">
                  <div className="flex items-center space-x-1">
                    {status.isOnline ? (
                      <Wifi className="h-3 w-3 text-green-500" />
                    ) : (
                      <WifiOff className="h-3 w-3 text-red-500" />
                    )}
                    <span>
                      {status.isOnline ? 'Online' : 'Offline'}
                    </span>
                  </div>
                  <div>Local memories: {status.localMemories}</div>
                  {status.pendingSync > 0 && (
                    <div className="text-yellow-600">
                      Pending sync: {status.pendingSync}
                    </div>
                  )}
                </div>
              )}
              {error && (
                <p className="text-sm text-red-600">Error: {error}</p>
              )}
            </div>
          </TooltipContent>
        </Tooltip>

        {/* Quick Info Icons */}
        {isSTMReady && status && (
          <div className="flex items-center space-x-1">
            {/* Online/Offline Indicator */}
            <Tooltip>
              <TooltipTrigger asChild>
                <div>
                  {status.isOnline ? (
                    <Wifi className="h-3 w-3 text-green-500" />
                  ) : (
                    <WifiOff className="h-3 w-3 text-red-500" />
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{status.isOnline ? 'Online - syncing enabled' : 'Offline - local only'}</p>
              </TooltipContent>
            </Tooltip>

            {/* Speed Indicator */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Zap className="h-3 w-3 text-yellow-500" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Instant local search enabled</p>
              </TooltipContent>
            </Tooltip>

            {/* Local Storage Indicator */}
            <Tooltip>
              <TooltipTrigger asChild>
                <HardDrive className="h-3 w-3 text-blue-500" />
              </TooltipTrigger>
              <TooltipContent>
                <p>{status.localMemories} memories cached locally</p>
              </TooltipContent>
            </Tooltip>

            {/* Sync Indicator */}
            {status.pendingSync > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Cloud className="h-3 w-3 text-orange-500" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{status.pendingSync} memories pending sync</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        )}

        {/* Settings Button */}
        {isSTMEnabled && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm" className="p-1">
                <Settings className="h-3 w-3" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Smart Memory Settings</AlertDialogTitle>
                <AlertDialogDescription>
                  Configure your local memory preferences.
                </AlertDialogDescription>
              </AlertDialogHeader>
              
              <div className="space-y-4">
                {/* Status Display */}
                {status && (
                  <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                    <h4 className="font-medium">Current Status</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Local Memories:</span>
                        <span className="ml-2">{status.localMemories}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Pending Sync:</span>
                        <span className="ml-2">{status.pendingSync}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Storage Used:</span>
                        <span className="ml-2">
                          {Math.round(status.storageUsed / 1024)} KB
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Last Sync:</span>
                        <span className="ml-2">
                          {status.lastSync > 0 
                            ? new Date(status.lastSync).toLocaleTimeString()
                            : 'Never'
                          }
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Feature Info */}
                <div className="space-y-3">
                  <h4 className="font-medium">Features Enabled</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center space-x-2">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      <span>Instant memory creation and search</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Brain className="h-4 w-4 text-blue-500" />
                      <span>Local AI-powered semantic search</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <HardDrive className="h-4 w-4 text-green-500" />
                      <span>Offline memory access</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Cloud className="h-4 w-4 text-purple-500" />
                      <span>Background sync to cloud</span>
                    </div>
                  </div>
                </div>

                {/* Privacy Note */}
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Privacy:</strong> Your memories are processed locally 
                    in your browser and only synced to the cloud when you're online. 
                    No data leaves your device until you choose to sync.
                  </p>
                </div>
              </div>

              <AlertDialogFooter>
                <AlertDialogCancel>Close</AlertDialogCancel>
                <AlertDialogAction onClick={disableSTM}>
                  Disable Smart Memory
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
    </TooltipProvider>
  );
};