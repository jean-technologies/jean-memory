# Initiative 3: Onboarding Frontend Flow

## Overview

This initiative creates a comprehensive onboarding experience that:
1. Guides new users through Jean Memory's features
2. Prompts immediate integration setup (Notion as primary)
3. Enables instant document ingestion into short-term memory
4. Provides immediate search capabilities while long-term sync happens in background
5. Creates a delightful first-use experience

## User Journey Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Onboarding Journey                       │
│                                                                  │
│  Step 1: Welcome       Step 2: Integration   Step 3: Ingestion   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │• Product intro   │  │• Connect Notion │  │• Select docs   │  │
│  │• Key benefits    │  │• OAuth flow     │  │• Start ingestion│  │
│  │• How it works    │  │• Workspace scan │  │• Show progress  │  │
│  │• Demo video      │  │• Success state  │  │• Enable search  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                              │                                    │
│  Step 4: First Search   Step 5: AI Setup     Step 6: Complete    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │• Guided search   │  │• Claude setup   │  │• Success screen │  │
│  │• Show results    │  │• ChatGPT option │  │• Next steps     │  │
│  │• Explain magic   │  │• Extension guide│  │• Resources      │  │
│  │• Memory power    │  │• Optional step  │  │• Dashboard      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

**Depends on**: [INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md)

Before implementing the onboarding flow, ensure:
- Local development environment is running
- UI development server is configured with hot reload
- Test user authentication is set up
- Integration tutorial mocking is available

## Implementation Architecture

Builds on [JEAN_MEMORY_FRONTEND.md](./JEAN_MEMORY_FRONTEND.md) frontend architecture.

### State Management

```typescript
// store/onboardingSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface OnboardingState {
  isActive: boolean;
  currentStep: number;
  totalSteps: number;
  completedSteps: Set<number>;
  userData: {
    name?: string;
    useCase?: string;
    integrationType?: 'notion' | 'other';
  };
  integrationData: {
    connected: boolean;
    workspaceName?: string;
    selectedDocuments: string[];
    processingJobs: string[];
  };
  searchDemo: {
    completed: boolean;
    query?: string;
    results?: any[];
  };
  aiSetup: {
    selectedClient?: 'claude' | 'chatgpt' | 'skip';
    installationGuideShown: boolean;
  };
}

const initialState: OnboardingState = {
  isActive: true,
  currentStep: 1,
  totalSteps: 6,
  completedSteps: new Set(),
  userData: {},
  integrationData: {
    connected: false,
    selectedDocuments: [],
    processingJobs: []
  },
  searchDemo: {
    completed: false
  },
  aiSetup: {
    installationGuideShown: false
  }
};

const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState,
  reducers: {
    nextStep: (state) => {
      state.completedSteps.add(state.currentStep);
      if (state.currentStep < state.totalSteps) {
        state.currentStep += 1;
      }
    },
    goToStep: (state, action: PayloadAction<number>) => {
      state.currentStep = action.payload;
    },
    completeOnboarding: (state) => {
      state.isActive = false;
      state.completedSteps.add(state.currentStep);
    },
    updateUserData: (state, action: PayloadAction<Partial<OnboardingState['userData']>>) => {
      state.userData = { ...state.userData, ...action.payload };
    },
    updateIntegrationData: (state, action: PayloadAction<Partial<OnboardingState['integrationData']>>) => {
      state.integrationData = { ...state.integrationData, ...action.payload };
    }
  }
});

export const { 
  nextStep, 
  goToStep, 
  completeOnboarding, 
  updateUserData, 
  updateIntegrationData 
} = onboardingSlice.actions;
export default onboardingSlice.reducer;
```

### Main Onboarding Component

```typescript
// app/onboarding/page.tsx
"use client";

import { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { motion, AnimatePresence } from 'framer-motion';
import { RootState } from '@/store/store';
import { nextStep, goToStep, completeOnboarding } from '@/store/onboardingSlice';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

// Step Components
import { WelcomeStep } from '@/components/onboarding/WelcomeStep';
import { IntegrationStep } from '@/components/onboarding/IntegrationStep';
import { IngestionStep } from '@/components/onboarding/IngestionStep';
import { SearchDemoStep } from '@/components/onboarding/SearchDemoStep';
import { AISetupStep } from '@/components/onboarding/AISetupStep';
import { CompletionStep } from '@/components/onboarding/CompletionStep';

const stepComponents = {
  1: WelcomeStep,
  2: IntegrationStep,
  3: IngestionStep,
  4: SearchDemoStep,
  5: AISetupStep,
  6: CompletionStep
};

const stepTitles = {
  1: "Welcome to Jean Memory",
  2: "Connect Your Knowledge",
  3: "Ingest Your Documents",
  4: "Experience the Magic",
  5: "Setup AI Integration",
  6: "You're All Set!"
};

export default function OnboardingPage() {
  const dispatch = useDispatch();
  const onboarding = useSelector((state: RootState) => state.onboarding);
  const [canProceed, setCanProceed] = useState(false);
  
  const CurrentStepComponent = stepComponents[onboarding.currentStep as keyof typeof stepComponents];
  
  const handleNext = () => {
    if (onboarding.currentStep === onboarding.totalSteps) {
      dispatch(completeOnboarding());
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } else {
      dispatch(nextStep());
      setCanProceed(false); // Reset for next step
    }
  };
  
  const handleSkip = () => {
    dispatch(completeOnboarding());
    window.location.href = '/dashboard';
  };
  
  const progressPercentage = ((onboarding.currentStep - 1) / (onboarding.totalSteps - 1)) * 100;
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src="/images/jean-logo.png" alt="Jean Memory" className="w-8 h-8" />
              <div>
                <h1 className="text-xl font-bold">
                  {stepTitles[onboarding.currentStep as keyof typeof stepTitles]}
                </h1>
                <p className="text-sm text-muted-foreground">
                  Step {onboarding.currentStep} of {onboarding.totalSteps}
                </p>
              </div>
            </div>
            
            <Button 
              variant="ghost" 
              onClick={handleSkip}
              className="text-muted-foreground hover:text-foreground"
            >
              Skip Onboarding
            </Button>
          </div>
          
          <Progress value={progressPercentage} className="mt-4" />
        </div>
      </div>
      
      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={onboarding.currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="max-w-4xl mx-auto"
          >
            <CurrentStepComponent 
              onCanProceed={setCanProceed}
              onNext={handleNext}
            />
          </motion.div>
        </AnimatePresence>
      </div>
      
      {/* Footer Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t p-4">
        <div className="container mx-auto flex justify-between items-center">
          <Button 
            variant="outline" 
            onClick={() => dispatch(goToStep(Math.max(1, onboarding.currentStep - 1)))}
            disabled={onboarding.currentStep === 1}
          >
            Previous
          </Button>
          
          <div className="flex items-center gap-2">
            {Array.from({ length: onboarding.totalSteps }, (_, i) => i + 1).map((step) => (
              <div
                key={step}
                className={`w-2 h-2 rounded-full transition-colors ${
                  step === onboarding.currentStep
                    ? 'bg-primary'
                    : onboarding.completedSteps.has(step)
                    ? 'bg-green-500'
                    : 'bg-muted'
                }`}
              />
            ))}
          </div>
          
          <Button 
            onClick={handleNext}
            disabled={!canProceed}
            className="min-w-[100px]"
          >
            {onboarding.currentStep === onboarding.totalSteps ? 'Complete' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  );
}
```

### Step 1: Welcome Component

```typescript
// components/onboarding/WelcomeStep.tsx
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Button } from '@/components/ui/button';
import { Play, Brain, Search, Zap, Users } from 'lucide-react';
import { useDispatch } from 'react-redux';
import { updateUserData } from '@/store/onboardingSlice';

interface WelcomeStepProps {
  onCanProceed: (canProceed: boolean) => void;
  onNext: () => void;
}

const benefits = [
  {
    icon: Brain,
    title: "Never Forget",
    description: "AI-powered memory that remembers everything you've learned"
  },
  {
    icon: Search,
    title: "Instant Recall",
    description: "Find any information from your documents in milliseconds"
  },
  {
    icon: Zap,
    title: "Smart Connections",
    description: "Discover relationships between ideas across all your content"
  },
  {
    icon: Users,
    title: "AI Integration",
    description: "Works with Claude, ChatGPT, and your favorite AI tools"
  }
];

const useCases = [
  { id: 'research', label: 'Research & Writing' },
  { id: 'learning', label: 'Learning & Education' },
  { id: 'work', label: 'Work & Productivity' },
  { id: 'personal', label: 'Personal Knowledge' },
  { id: 'other', label: 'Other' }
];

export function WelcomeStep({ onCanProceed, onNext }: WelcomeStepProps) {
  const dispatch = useDispatch();
  const [name, setName] = useState('');
  const [useCase, setUseCase] = useState('');
  const [showVideo, setShowVideo] = useState(false);
  
  useEffect(() => {
    onCanProceed(name.length > 0 && useCase.length > 0);
  }, [name, useCase, onCanProceed]);
  
  const handleSubmit = () => {
    dispatch(updateUserData({ name, useCase }));
    onNext();
  };
  
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <img 
            src="/images/jean-logo.png" 
            alt="Jean Memory" 
            className="w-24 h-24 mx-auto mb-4"
          />
        </motion.div>
        
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Welcome to Jean Memory
        </h1>
        
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Your personal AI memory layer that makes every document, note, and idea instantly searchable and connected.
        </p>
        
        <Button
          variant="outline"
          onClick={() => setShowVideo(true)}
          className="gap-2"
        >
          <Play className="w-4 h-4" />
          Watch 2-minute Demo
        </Button>
      </div>
      
      {/* Benefits Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {benefits.map((benefit, index) => {
          const Icon = benefit.icon;
          return (
            <motion.div
              key={benefit.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="text-center h-full">
                <CardContent className="p-6">
                  <Icon className="w-8 h-8 mx-auto mb-3 text-primary" />
                  <h3 className="font-semibold mb-2">{benefit.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {benefit.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
      
      {/* User Info Form */}
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Let's personalize your experience</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">What should we call you?</Label>
            <Input
              id="name"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          
          <div className="space-y-3">
            <Label>What will you primarily use Jean Memory for?</Label>
            <RadioGroup value={useCase} onValueChange={setUseCase}>
              {useCases.map((option) => (
                <div key={option.id} className="flex items-center space-x-2">
                  <RadioGroupItem value={option.id} id={option.id} />
                  <Label htmlFor={option.id}>{option.label}</Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        </CardContent>
      </Card>
      
      {/* Video Modal */}
      {showVideo && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-900 rounded-lg max-w-4xl w-full">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="text-lg font-semibold">Jean Memory Demo</h3>
              <Button variant="ghost" onClick={() => setShowVideo(false)}>
                ×
              </Button>
            </div>
            <div className="aspect-video">
              <iframe
                src="https://www.youtube.com/embed/demo-video-id"
                className="w-full h-full"
                allowFullScreen
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Step 2: Integration Component

```typescript
// components/onboarding/IntegrationStep.tsx
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, ExternalLink, Loader2 } from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';
import { updateIntegrationData } from '@/store/onboardingSlice';
import { RootState } from '@/store/store';

interface IntegrationStepProps {
  onCanProceed: (canProceed: boolean) => void;
  onNext: () => void;
}

const integrationOptions = [
  {
    id: 'notion',
    name: 'Notion',
    description: 'Connect your Notion workspace to import pages and databases',
    icon: '/images/notion.svg',
    primary: true,
    comingSoon: false
  },
  {
    id: 'obsidian',
    name: 'Obsidian',
    description: 'Import your Obsidian vault and knowledge graphs',
    icon: '/images/obsidian.svg',
    primary: false,
    comingSoon: true
  },
  {
    id: 'google-drive',
    name: 'Google Drive',
    description: 'Access documents from your Google Drive',
    icon: '/images/google-drive.svg',
    primary: false,
    comingSoon: true
  },
  {
    id: 'dropbox',
    name: 'Dropbox',
    description: 'Import files from your Dropbox account',
    icon: '/images/dropbox.svg',
    primary: false,
    comingSoon: true
  }
];

export function IntegrationStep({ onCanProceed, onNext }: IntegrationStepProps) {
  const dispatch = useDispatch();
  const { integrationData } = useSelector((state: RootState) => state.onboarding);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'connected' | 'error'>('idle');
  
  useEffect(() => {
    onCanProceed(integrationData.connected);
  }, [integrationData.connected, onCanProceed]);
  
  const handleConnect = async (integrationId: string) => {
    if (integrationId !== 'notion') return;
    
    setIsConnecting(true);
    setConnectionStatus('connecting');
    
    try {
      // Initiate OAuth flow
      const response = await fetch('/api/v1/integrations/notion/connect', {
        method: 'GET',
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        // Redirect to OAuth
        window.location.href = data.oauth_url;
      } else {
        throw new Error('Failed to initiate connection');
      }
    } catch (error) {
      console.error('Connection failed:', error);
      setConnectionStatus('error');
    } finally {
      setIsConnecting(false);
    }
  };
  
  const handleSkipIntegration = () => {
    dispatch(updateIntegrationData({ connected: true }));
    onNext();
  };
  
  // Check for OAuth callback completion
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('integration') === 'notion' && urlParams.get('status') === 'success') {
      setConnectionStatus('connected');
      dispatch(updateIntegrationData({ 
        connected: true, 
        workspaceName: urlParams.get('workspace') || 'Notion Workspace'
      }));
      
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [dispatch]);
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold">Connect Your Knowledge Source</h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Choose where your knowledge lives. We'll import your documents and make them instantly searchable.
        </p>
      </div>
      
      {/* Integration Options */}
      <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
        {integrationOptions.map((integration) => (
          <motion.div
            key={integration.id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Card className={`relative cursor-pointer transition-all hover:shadow-lg ${
              integration.primary ? 'ring-2 ring-primary' : ''
            } ${
              connectionStatus === 'connected' && integration.id === 'notion' 
                ? 'ring-2 ring-green-500 bg-green-50 dark:bg-green-900/20' 
                : ''
            }`}>
              {integration.primary && (
                <Badge className="absolute -top-2 left-4 bg-primary">
                  Recommended
                </Badge>
              )}
              
              {integration.comingSoon && (
                <Badge variant="secondary" className="absolute -top-2 right-4">
                  Coming Soon
                </Badge>
              )}
              
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3">
                  <img 
                    src={integration.icon} 
                    alt={integration.name}
                    className="w-8 h-8"
                  />
                  <CardTitle className="text-xl">{integration.name}</CardTitle>
                  
                  {connectionStatus === 'connected' && integration.id === 'notion' && (
                    <CheckCircle className="w-5 h-5 text-green-500 ml-auto" />
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                <p className="text-muted-foreground mb-4">
                  {integration.description}
                </p>
                
                <Button
                  className="w-full"
                  onClick={() => handleConnect(integration.id)}
                  disabled={integration.comingSoon || isConnecting || connectionStatus === 'connected'}
                  variant={integration.primary ? 'default' : 'outline'}
                >
                  {isConnecting && integration.id === 'notion' ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Connecting...
                    </>
                  ) : connectionStatus === 'connected' && integration.id === 'notion' ? (
                    'Connected'
                  ) : integration.comingSoon ? (
                    'Coming Soon'
                  ) : (
                    <>
                      Connect {integration.name}
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
      
      {/* Success State */}
      {connectionStatus === 'connected' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-4"
        >
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
          <h3 className="text-2xl font-semibold text-green-700 dark:text-green-400">
            Successfully Connected!
          </h3>
          <p className="text-muted-foreground">
            Connected to {integrationData.workspaceName}. Ready to import your documents.
          </p>
        </motion.div>
      )}
      
      {/* Skip Option */}
      <div className="text-center">
        <Button
          variant="ghost"
          onClick={handleSkipIntegration}
          className="text-muted-foreground"
        >
          Skip for now, I'll connect later
        </Button>
      </div>
    </div>
  );
}
```

### Step 3: Document Ingestion Component

Builds on [INITIATIVE_2_NOTION_INTEGRATION.md](./INITIATIVE_2_NOTION_INTEGRATION.md).

```typescript
// components/onboarding/IngestionStep.tsx
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { FileText, Database, Folder, CheckCircle, Loader2, Zap } from 'lucide-react';
import { useDispatch, useSelector } from 'react-redux';
import { updateIntegrationData } from '@/store/onboardingSlice';
import { RootState } from '@/store/store';

interface IngestionStepProps {
  onCanProceed: (canProceed: boolean) => void;
  onNext: () => void;
}

interface NotionPage {
  id: string;
  title: string;
  parent_type: string;
  last_edited_time: string;
  url: string;
}

interface ProcessingJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  document_title: string;
}

export function IngestionStep({ onCanProceed, onNext }: IngestionStepProps) {
  const dispatch = useDispatch();
  const { integrationData } = useSelector((state: RootState) => state.onboarding);
  const [pages, setPages] = useState<NotionPage[]>([]);
  const [selectedPages, setSelectedPages] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingJobs, setProcessingJobs] = useState<ProcessingJob[]>([]);
  const [processingComplete, setProcessingComplete] = useState(false);
  
  // Load Notion pages
  useEffect(() => {
    loadNotionPages();
  }, []);
  
  // Auto-select some popular pages
  useEffect(() => {
    if (pages.length > 0) {
      // Auto-select first 3 pages that are not databases
      const autoSelected = pages
        .filter(p => p.parent_type !== 'database')
        .slice(0, 3)
        .map(p => p.id);
      setSelectedPages(new Set(autoSelected));
    }
  }, [pages]);
  
  // Update can proceed based on processing status
  useEffect(() => {
    onCanProceed(processingComplete || selectedPages.size > 0);
  }, [processingComplete, selectedPages.size, onCanProceed]);
  
  const loadNotionPages = async () => {
    try {
      const response = await fetch('/api/v1/integrations/notion/pages');
      const data = await response.json();
      setPages(data.pages || []);
    } catch (error) {
      console.error('Failed to load pages:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSelectPage = (pageId: string, checked: boolean) => {
    const newSelected = new Set(selectedPages);
    if (checked) {
      newSelected.add(pageId);
    } else {
      newSelected.delete(pageId);
    }
    setSelectedPages(newSelected);
  };
  
  const handleStartProcessing = async () => {
    if (selectedPages.size === 0) return;
    
    setIsProcessing(true);
    
    try {
      const response = await fetch('/api/v1/integrations/notion/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page_ids: Array.from(selectedPages)
        })
      });
      
      const result = await response.json();
      
      // Start polling for job status
      dispatch(updateIntegrationData({ 
        processingJobs: result.job_ids,
        selectedDocuments: Array.from(selectedPages)
      }));
      
      pollJobStatus(result.job_ids);
      
    } catch (error) {
      console.error('Failed to start processing:', error);
      setIsProcessing(false);
    }
  };
  
  const pollJobStatus = async (jobIds: string[]) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/v1/integrations/notion/processing-status');
        const data = await response.json();
        
        const relevantJobs = data.jobs.filter((job: ProcessingJob) => 
          jobIds.includes(job.id)
        );
        
        setProcessingJobs(relevantJobs);
        
        // Check if all jobs are complete
        const allComplete = relevantJobs.every((job: ProcessingJob) => 
          job.status === 'completed' || job.status === 'failed'
        );
        
        if (allComplete) {
          clearInterval(interval);
          setIsProcessing(false);
          setProcessingComplete(true);
        }
        
      } catch (error) {
        console.error('Failed to poll job status:', error);
      }
    }, 2000); // Poll every 2 seconds
  };
  
  const getPageIcon = (parentType: string) => {
    switch (parentType) {
      case 'database': return <Database className="w-4 h-4" />;
      case 'page': return <FileText className="w-4 h-4" />;
      default: return <Folder className="w-4 h-4" />;
    }
  };
  
  const completedJobs = processingJobs.filter(job => job.status === 'completed').length;
  const totalJobs = processingJobs.length;
  const overallProgress = totalJobs > 0 ? (completedJobs / totalJobs) * 100 : 0;
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading your Notion pages...</span>
      </div>
    );
  }
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold">Choose Documents to Import</h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Select documents from your Notion workspace. We'll process them and make them instantly searchable.
        </p>
        
        {!isProcessing && !processingComplete && (
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Zap className="w-4 h-4 text-amber-500" />
            Documents will be available for search immediately via our short-term memory layer
          </div>
        )}
      </div>
      
      {/* Document Selection */}
      {!isProcessing && !processingComplete && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-6"
        >
          {/* Quick Actions */}
          <div className="flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              {pages.length} documents found • {selectedPages.size} selected
            </p>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedPages(new Set(pages.slice(0, 5).map(p => p.id)))}
              >
                Select Top 5
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedPages(new Set())}
              >
                Clear All
              </Button>
            </div>
          </div>
          
          {/* Pages List */}
          <div className="grid gap-3 max-h-96 overflow-y-auto">
            {pages.slice(0, 20).map((page) => (
              <Card key={page.id} className="transition-colors hover:bg-muted/50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Checkbox
                      checked={selectedPages.has(page.id)}
                      onCheckedChange={(checked) => 
                        handleSelectPage(page.id, checked as boolean)
                      }
                    />
                    
                    <div className="flex items-center gap-2 flex-1">
                      {getPageIcon(page.parent_type)}
                      <span className="font-medium truncate">{page.title}</span>
                    </div>
                    
                    <Badge variant="outline" className="text-xs">
                      {new Date(page.last_edited_time).toLocaleDateString()}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          {/* Process Button */}
          <div className="text-center">
            <Button
              size="lg"
              onClick={handleStartProcessing}
              disabled={selectedPages.size === 0}
              className="px-8"
            >
              Import {selectedPages.size} Document{selectedPages.size !== 1 ? 's' : ''}
            </Button>
          </div>
        </motion.div>
      )}
      
      {/* Processing Status */}
      {isProcessing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <div className="text-center space-y-4">
            <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
            <div>
              <h3 className="text-xl font-semibold">Processing Your Documents</h3>
              <p className="text-muted-foreground">
                {completedJobs} of {totalJobs} documents processed
              </p>
            </div>
            <Progress value={overallProgress} className="w-full max-w-md mx-auto" />
          </div>
          
          {/* Job Details */}
          <div className="grid gap-3 max-w-2xl mx-auto">
            {processingJobs.map((job) => (
              <Card key={job.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium truncate">{job.document_title}</span>
                    <div className="flex items-center gap-2">
                      {job.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      ) : job.status === 'failed' ? (
                        <span className="text-red-500 text-sm">Failed</span>
                      ) : (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      )}
                      <Badge variant={job.status === 'completed' ? 'default' : 'secondary'}>
                        {job.status}
                      </Badge>
                    </div>
                  </div>
                  {job.status === 'processing' && (
                    <Progress value={job.progress} className="mt-2" />
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Completion State */}
      {processingComplete && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center space-y-6"
        >
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto" />
          
          <div>
            <h3 className="text-2xl font-semibold text-green-700 dark:text-green-400">
              Documents Ready!
            </h3>
            <p className="text-muted-foreground mt-2">
              Successfully processed {completedJobs} documents. They're now searchable in your memory.
            </p>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg max-w-md mx-auto">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <Zap className="w-4 h-4" />
              <span className="text-sm font-medium">Ready for immediate search!</span>
            </div>
            <p className="text-xs text-green-600 dark:text-green-500 mt-1">
              Your documents are now in short-term memory for instant access.
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
```

### Step 4: Search Demo Component

Builds on short-term memory system from [INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md).

```typescript
// components/onboarding/SearchDemoStep.tsx
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, Sparkles, Clock, FileText, Lightbulb } from 'lucide-react';
import { useDispatch } from 'react-redux';

interface SearchDemoStepProps {
  onCanProceed: (canProceed: boolean) => void;
  onNext: () => void;
}

const suggestedQueries = [
  "What are my main interests?",
  "What projects am I working on?",
  "What did I learn recently?",
  "What are my goals?",
  "Show me my notes about productivity"
];

export function SearchDemoStep({ onCanProceed, onNext }: SearchDemoStepProps) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchTime, setSearchTime] = useState<number>(0);
  
  useEffect(() => {
    onCanProceed(hasSearched);
  }, [hasSearched, onCanProceed]);
  
  const handleSearch = async (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    if (!finalQuery.trim()) return;
    
    setIsSearching(true);
    const startTime = Date.now();
    
    try {
      const response = await fetch('/api/v2/memories/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: finalQuery,
          layer: 'short',  // Use short-term memory for demo
          limit: 5
        })
      });
      
      const data = await response.json();
      const endTime = Date.now();
      
      setSearchResults(data.results || []);
      setSearchTime(endTime - startTime);
      setHasSearched(true);
      
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };
  
  const handleSuggestedQuery = (suggestedQuery: string) => {
    setQuery(suggestedQuery);
    handleSearch(suggestedQuery);
  };
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold">Experience the Magic</h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Try searching through your newly imported documents. Watch how Jean Memory instantly finds and connects relevant information.
        </p>
      </div>
      
      {/* Search Interface */}
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Search Your Memory
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Ask anything about your documents..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="flex-1"
            />
            <Button 
              onClick={() => handleSearch()}
              disabled={!query.trim() || isSearching}
              loading={isSearching}
            >
              Search
            </Button>
          </div>
          
          {/* Suggested Queries */}
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">Try these example searches:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQueries.map((suggestion) => (
                <Button
                  key={suggestion}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestedQuery(suggestion)}
                  disabled={isSearching}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Search Results */}
      {searchResults.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Performance Stats */}
          <div className="flex justify-center">
            <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
              <Clock className="w-3 h-3 mr-1" />
              Found {searchResults.length} results in {searchTime}ms
            </Badge>
          </div>
          
          {/* Results */}
          <div className="grid gap-4 max-w-4xl mx-auto">
            {searchResults.map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <FileText className="w-5 h-5 text-primary mt-1" />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium">
                            {result.metadata?.title || 'Document Result'}
                          </h4>
                          <Badge variant="secondary">
                            {Math.round(result.score * 100)}% match
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground line-clamp-3">
                          {result.content}
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs">
                            {result.metadata?.source || 'notion'}
                          </Badge>
                          {result.metadata?.created_at && (
                            <span className="text-xs text-muted-foreground">
                              {new Date(result.metadata.created_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
          
          {/* Magic Explanation */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 p-6 rounded-lg max-w-2xl mx-auto"
          >
            <div className="flex items-center gap-3 mb-3">
              <Sparkles className="w-6 h-6 text-purple-600" />
              <h3 className="text-lg font-semibold">How Jean Memory Works</h3>
            </div>
            <div className="space-y-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                <span>AI understands the meaning of your query, not just keywords</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                <span>Short-term memory provides instant results (&lt;50ms)</span>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                <span>Results ranked by semantic similarity to your question</span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
      
      {/* No Results State */}
      {hasSearched && searchResults.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-8"
        >
          <p className="text-muted-foreground">
            No results found. Try a different search term or import more documents.
          </p>
        </motion.div>
      )}
    </div>
  );
}
```

## Integration with Memory Systems

Builds on:
- [INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md) - For immediate search capabilities
- [INITIATIVE_2_NOTION_INTEGRATION.md](./INITIATIVE_2_NOTION_INTEGRATION.md) - For document processing
- [JEAN_MEMORY_FRONTEND.md](./JEAN_MEMORY_FRONTEND.md) - For UI architecture
- [JEAN_MEMORY_BACKEND_API.md](./JEAN_MEMORY_BACKEND_API.md) - For API endpoints

## Performance Targets

- **Onboarding completion**: <10 minutes total
- **Integration connection**: <30 seconds
- **Document processing**: Real-time progress updates
- **First search**: <3 seconds after processing
- **Search results**: <100ms from short-term memory

## References

- [Local Development Setup](./INITIATIVE_0_LOCAL_DEVELOPMENT_SETUP.md) - **Required prerequisite**
- [Frontend Architecture](./JEAN_MEMORY_FRONTEND.md)
- [Short-term Memory System](./INITIATIVE_1_SHORT_TERM_MEMORY_SYSTEM.md)
- [Notion Integration](./INITIATIVE_2_NOTION_INTEGRATION.md)
- [Backend API](./JEAN_MEMORY_BACKEND_API.md)