"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ArrowLeft, 
  Copy, 
  Eye, 
  EyeOff, 
  ExternalLink,
  Activity,
  Settings,
  Users
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { Session, Agent } from "./SessionManager";

interface SessionDetailViewProps {
  session: Session;
  onBack: () => void;
  onSessionUpdate: () => void;
}

export function SessionDetailView({ session, onBack, onSessionUpdate }: SessionDetailViewProps) {
  const [activeTab, setActiveTab] = useState<'agents' | 'activity' | 'settings'>('agents');

  return (
    <div className="session-detail space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Sessions
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">{session.name}</h2>
            <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
              {session.status}
            </Badge>
          </div>
          {session.description && (
            <p className="text-muted-foreground mt-1">{session.description}</p>
          )}
        </div>
      </div>
      
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="agents" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Agents
          </TabsTrigger>
          <TabsTrigger value="activity" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Activity
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="w-4 h-4" />
            Settings
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="agents" className="mt-6">
          <AgentsPanel session={session} />
        </TabsContent>
        
        <TabsContent value="activity" className="mt-6">
          <ActivityPanel session={session} />
        </TabsContent>
        
        <TabsContent value="settings" className="mt-6">
          <SettingsPanel session={session} onSessionUpdate={onSessionUpdate} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AgentsPanel({ session }: { session: Session }) {
  return (
    <div className="agents-panel space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Agents ({session.agents.length}/3)</h3>
        {session.agents.length < 3 && (
          <Button size="sm" disabled>
            Add Agent (Coming Soon)
          </Button>
        )}
      </div>
      
      <div className="grid gap-4">
        {session.agents.map(agent => (
          <AgentCard key={agent.id} agent={agent} session={session} />
        ))}
      </div>
    </div>
  );
}

function AgentCard({ agent, session }: { agent: Agent; session: Session }) {
  const [showUrl, setShowUrl] = useState(false);
  
  const copyConnectionUrl = () => {
    navigator.clipboard.writeText(agent.connection_url);
    toast.success('Connection URL copied to clipboard');
  };

  const connectionInstructions = `
# Connect ${agent.name} agent to Jean Memory
npx install-mcp ${agent.connection_url} --client claude code

# Verify connection
claude mcp list
`.trim();

  return (
    <Card className="agent-card">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                agent.status === 'connected' ? 'bg-green-500' : 'bg-gray-400'
              }`} />
              <h4 className="font-medium">{agent.name}</h4>
              <Badge variant="outline" className="text-xs">
                {agent.status}
              </Badge>
            </div>
            {agent.role && <p className="text-sm text-muted-foreground">{agent.role}</p>}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="connection-section">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">Connection URL</span>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowUrl(!showUrl)}
            >
              {showUrl ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              {showUrl ? 'Hide' : 'Show'}
            </Button>
          </div>
          
          {showUrl && (
            <div className="space-y-2">
              <div className="bg-muted p-3 rounded-md">
                <code className="text-xs break-all">{agent.connection_url}</code>
              </div>
              <Button size="sm" onClick={copyConnectionUrl} className="w-full">
                <Copy className="w-4 h-4 mr-2" />
                Copy URL
              </Button>
            </div>
          )}
        </div>
        
        <div className="connection-instructions">
          <p className="text-sm font-medium mb-2">Setup Instructions:</p>
          <div className="bg-muted p-3 rounded-md">
            <pre className="text-xs whitespace-pre-wrap">{connectionInstructions}</pre>
          </div>
        </div>
        
        <div className="agent-meta text-xs text-muted-foreground">
          Last activity: {agent.last_activity ? 
            formatDistanceToNow(new Date(agent.last_activity)) + ' ago' : 
            'Never'
          }
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityPanel({ session }: { session: Session }) {
  return (
    <div className="activity-panel">
      <div className="text-center py-8 text-muted-foreground">
        <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <h3 className="font-medium mb-2">Activity tracking coming soon</h3>
        <p className="text-sm">
          View agent coordination messages, file claims, and codebase changes
        </p>
      </div>
    </div>
  );
}

function SettingsPanel({ session, onSessionUpdate }: { 
  session: Session; 
  onSessionUpdate: () => void; 
}) {
  return (
    <div className="settings-panel space-y-6">
      <Card>
        <CardHeader>
          <h4 className="font-medium">Session Information</h4>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Session ID</span>
            <span className="text-sm font-mono">{session.id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Created</span>
            <span className="text-sm">{formatDistanceToNow(new Date(session.created_at))} ago</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Last Updated</span>
            <span className="text-sm">{formatDistanceToNow(new Date(session.updated_at))} ago</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-muted-foreground">Agents</span>
            <span className="text-sm">{session.agents.length}/3</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h4 className="font-medium text-destructive">Danger Zone</h4>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3">
            Session management features will be available in a future update.
          </p>
          <Button variant="destructive" size="sm" disabled>
            Delete Session
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}