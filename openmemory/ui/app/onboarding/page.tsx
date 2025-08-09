"use client";

import React, { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Loader2, CheckCircle, AlertCircle, BookOpen, ArrowRight, ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/components/ui/use-toast";
import apiClient from "@/lib/apiClient";
import { useAuth } from "@/contexts/AuthContext";
import { motion, AnimatePresence } from "framer-motion";

interface NotionPage {
  id: string;
  title: string;
  url: string;
  created_time: string;
  last_edited_time: string;
}

interface NotionWorkspace {
  workspace_name?: string;
  workspace_icon?: string;
  bot_id?: string;
}

type OnboardingStep = 'connect' | 'select_pages' | 'sync' | 'complete';

export default function OnboardingPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();
  const { toast } = useToast();

  // State management
  const [currentStep, setCurrentStep] = useState<OnboardingStep>('connect');
  const [isConnected, setIsConnected] = useState(false);
  const [workspace, setWorkspace] = useState<NotionWorkspace>({});
  const [pages, setPages] = useState<NotionPage[]>([]);
  const [selectedPages, setSelectedPages] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [syncProgress, setSyncProgress] = useState(0);
  const [syncMessage, setSyncMessage] = useState('');
  const [taskId, setTaskId] = useState<string | null>(null);

  // Check for OAuth callback or redirect from backend
  useEffect(() => {
    const success = searchParams.get('success');
    const error = searchParams.get('error');
    const data = searchParams.get('data');
    
    if (success === 'true' && data) {
      // Successfully connected via OAuth
      try {
        const decodedData = JSON.parse(atob(data));
        setIsConnected(true);
        setWorkspace(decodedData);
        setCurrentStep('select_pages');
        toast({
          title: "Connected!",
          description: `Successfully connected to ${decodedData.workspace_name || 'Notion workspace'}.`,
        });
        // Clean URL
        router.replace('/onboarding');
        // Load pages
        loadPages();
      } catch (e) {
        console.error('Error parsing callback data:', e);
      }
    } else if (error) {
      // Handle error from OAuth callback
      toast({
        title: "Connection Failed",
        description: error === 'oauth_failed' ? "Failed to connect to Notion." : error,
        variant: "destructive",
      });
      setCurrentStep('connect');
      // Clean URL
      router.replace('/onboarding');
    } else {
      // Check if user already has Notion connected
      checkNotionStatus();
    }
  }, [searchParams]);

  // Check current Notion connection status
  const checkNotionStatus = async () => {
    if (!user) return;
    
    try {
      const response = await apiClient.get('/api/v1/integrations/notion/status');
      if (response.data.connected) {
        setIsConnected(true);
        setWorkspace(response.data.workspace || {});
        setCurrentStep('select_pages');
        await loadPages();
      }
    } catch (error) {
      console.error('Error checking Notion status:', error);
    }
  };


  // Start OAuth flow
  const startOAuthFlow = async () => {
    if (!user) return;
    
    setIsLoading(true);
    setLoadingMessage('Redirecting to Notion...');

    try {
      const response = await apiClient.get('/api/v1/integrations/notion/auth');
      window.location.href = response.data.oauth_url;
    } catch (error: any) {
      console.error('Error starting OAuth:', error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to start Notion authorization.",
        variant: "destructive",
      });
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Load pages from Notion
  const loadPages = async () => {
    setIsLoading(true);
    setLoadingMessage('Loading your Notion pages...');

    try {
      const response = await apiClient.get('/api/v1/integrations/notion/pages');
      setPages(response.data.pages || []);
    } catch (error: any) {
      console.error('Error loading pages:', error);
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to load Notion pages.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setLoadingMessage('');
    }
  };

  // Toggle page selection
  const togglePageSelection = (pageId: string) => {
    setSelectedPages(prev => 
      prev.includes(pageId) 
        ? prev.filter(id => id !== pageId)
        : [...prev, pageId]
    );
  };

  // Select all pages
  const selectAllPages = () => {
    setSelectedPages(pages.map(p => p.id));
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedPages([]);
  };

  // Start sync process
  const startSync = async () => {
    if (selectedPages.length === 0) {
      toast({
        title: "No Pages Selected",
        description: "Please select at least one page to sync.",
        variant: "destructive",
      });
      return;
    }

    setCurrentStep('sync');
    setIsLoading(true);
    setSyncProgress(0);
    setSyncMessage('Starting sync...');

    try {
      const response = await apiClient.post('/api/v1/integrations/notion/sync', null, {
        params: {
          page_ids: selectedPages
        }
      });

      setTaskId(response.data.task_id);
      toast({
        title: "Sync Started",
        description: `Started syncing ${selectedPages.length} pages.`,
      });

      // Start polling for progress
      pollSyncProgress(response.data.task_id);

    } catch (error: any) {
      console.error('Error starting sync:', error);
      toast({
        title: "Sync Failed",
        description: error.response?.data?.detail || "Failed to start sync.",
        variant: "destructive",
      });
      setCurrentStep('select_pages');
      setIsLoading(false);
    }
  };

  // Poll sync progress
  const pollSyncProgress = async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await apiClient.get(`/api/v1/integrations/tasks/${taskId}`);
        const task = response.data;

        setSyncProgress(task.progress || 0);
        setSyncMessage(task.progress_message || 'Processing...');

        if (task.status === 'completed') {
          setSyncProgress(100);
          setSyncMessage('Sync completed successfully!');
          setIsLoading(false);
          setCurrentStep('complete');
          
          toast({
            title: "Sync Complete!",
            description: `Successfully synced your Notion pages to memory.`,
          });
          
          return;
        } else if (task.status === 'failed') {
          setIsLoading(false);
          toast({
            title: "Sync Failed",
            description: task.error || "An error occurred during sync.",
            variant: "destructive",
          });
          setCurrentStep('select_pages');
          return;
        }

        // Continue polling
        setTimeout(poll, 2000);
      } catch (error) {
        console.error('Error polling task:', error);
        setTimeout(poll, 5000); // Retry with longer delay
      }
    };

    poll();
  };

  // Render connection step
  const renderConnectStep = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="text-center space-y-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-black to-gray-700 rounded-xl flex items-center justify-center">
          <BookOpen className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Connect Your Notion Workspace</h1>
          <p className="text-muted-foreground mt-2">
            Import your Notion pages into Jean Memory to make them searchable and accessible through AI.
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-4 h-4 text-green-600" />
              </div>
              <span>Secure OAuth 2.0 authentication</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-4 h-4 text-green-600" />
              </div>
              <span>Read-only access to your selected pages</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-4 h-4 text-green-600" />
              </div>
              <span>No data stored on external servers</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button 
        onClick={startOAuthFlow} 
        disabled={isLoading}
        className="w-full"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            {loadingMessage}
          </>
        ) : (
          <>
            Connect to Notion
            <ExternalLink className="ml-2 h-4 w-4" />
          </>
        )}
      </Button>
    </motion.div>
  );

  // Render page selection step
  const renderSelectPagesStep = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="text-center space-y-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-black to-gray-700 rounded-xl flex items-center justify-center">
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Select Pages to Import</h1>
          <p className="text-muted-foreground mt-2">
            Choose which pages from {workspace.workspace_name || 'your workspace'} you'd like to add to your memory.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p>{loadingMessage}</p>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-center">
            <div className="text-sm text-muted-foreground">
              {pages.length} pages found • {selectedPages.length} selected
            </div>
            <div className="space-x-2">
              <Button variant="outline" size="sm" onClick={clearSelection}>
                Clear All
              </Button>
              <Button variant="outline" size="sm" onClick={selectAllPages}>
                Select All
              </Button>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto space-y-2">
            {pages.map((page) => (
              <Card 
                key={page.id}
                className={`cursor-pointer transition-all ${
                  selectedPages.includes(page.id) 
                    ? 'ring-2 ring-primary bg-primary/5' 
                    : 'hover:bg-accent'
                }`}
                onClick={() => togglePageSelection(page.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                      selectedPages.includes(page.id)
                        ? 'bg-primary border-primary'
                        : 'border-gray-300'
                    }`}>
                      {selectedPages.includes(page.id) && (
                        <CheckCircle className="w-3 h-3 text-primary-foreground" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium truncate">{page.title}</h3>
                      <p className="text-sm text-muted-foreground">
                        Last edited: {new Date(page.last_edited_time).toLocaleDateString()}
                      </p>
                    </div>
                    <ExternalLink 
                      className="w-4 h-4 text-muted-foreground hover:text-foreground"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(page.url, '_blank');
                      }}
                    />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setCurrentStep('connect')}>
              Back
            </Button>
            <Button 
              onClick={startSync}
              disabled={selectedPages.length === 0}
              className="flex-1"
            >
              Import {selectedPages.length} Page{selectedPages.length !== 1 ? 's' : ''}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </>
      )}
    </motion.div>
  );

  // Render sync step
  const renderSyncStep = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="text-center space-y-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-white animate-spin" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">Importing Your Pages</h1>
          <p className="text-muted-foreground mt-2">
            We're processing your selected pages and adding them to your memory...
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{Math.round(syncProgress)}%</span>
              </div>
              <Progress value={syncProgress} className="h-2" />
            </div>
            <div className="text-sm text-muted-foreground text-center">
              {syncMessage}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="text-center text-sm text-muted-foreground">
        This may take a few minutes depending on the size of your pages...
      </div>
    </motion.div>
  );

  // Render complete step
  const renderCompleteStep = () => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      <div className="text-center space-y-4">
        <div className="w-16 h-16 mx-auto bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
          <CheckCircle className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">All Set! 🎉</h1>
          <p className="text-muted-foreground mt-2">
            Your Notion pages have been successfully imported into Jean Memory.
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="text-center">
              <Badge variant="secondary" className="text-lg px-4 py-2">
                {selectedPages.length} Pages Imported
              </Badge>
            </div>
            <Separator />
            <div className="space-y-3">
              <h3 className="font-medium">What's next?</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Your pages are now searchable in the Memories section</li>
                <li>• Ask questions about your imported content using AI</li>
                <li>• Connect more apps to build your comprehensive memory</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        <Button variant="outline" onClick={() => router.push('/memories')}>
          View Memories
        </Button>
        <Button onClick={() => router.push('/dashboard')} className="flex-1">
          Go to Dashboard
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </motion.div>
  );

  // Show loading if no user
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container max-w-2xl mx-auto py-8 px-4">
        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {['connect', 'select_pages', 'sync', 'complete'].map((step, index) => {
              const isActive = currentStep === step;
              const isCompleted = ['connect', 'select_pages', 'sync', 'complete'].indexOf(currentStep) > index;
              
              return (
                <div key={step} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    isCompleted ? 'bg-green-500 text-white' : 
                    isActive ? 'bg-primary text-primary-foreground' : 
                    'bg-gray-200 text-gray-500'
                  }`}>
                    {isCompleted ? <CheckCircle className="w-4 h-4" /> : index + 1}
                  </div>
                  {index < 3 && (
                    <div className={`w-16 h-px mx-2 ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-200'
                    }`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step content */}
        <AnimatePresence mode="wait">
          {currentStep === 'connect' && renderConnectStep()}
          {currentStep === 'select_pages' && renderSelectPagesStep()}
          {currentStep === 'sync' && renderSyncStep()}
          {currentStep === 'complete' && renderCompleteStep()}
        </AnimatePresence>
      </div>
    </div>
  );
}