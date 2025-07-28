"use client";

import { useState } from "react";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Users, 
  Calendar, 
  Eye, 
  EyeOff, 
  Copy,
  Settings,
  ExternalLink
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { Session } from "./SessionManager";
import { SessionDetailView } from "./SessionDetailView";

interface SessionListProps {
  sessions: Session[];
  onSessionUpdate: () => void;
}

export function SessionList({ sessions, onSessionUpdate }: SessionListProps) {
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  if (sessions.length === 0) {
    return (
      <div className="text-center py-8 bg-muted/20 rounded-lg border-2 border-dashed">
        <Users className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
        <h3 className="text-lg font-medium mb-2">No sessions yet</h3>
        <p className="text-muted-foreground mb-4">
          Create your first multi-agent session to start collaborating
        </p>
      </div>
    );
  }

  if (selectedSession) {
    return (
      <SessionDetailView 
        session={selectedSession} 
        onBack={() => setSelectedSession(null)}
        onSessionUpdate={onSessionUpdate}
      />
    );
  }

  return (
    <div className="sessions-grid space-y-4">
      {sessions.map(session => (
        <SessionCard 
          key={session.id} 
          session={session} 
          onSelect={() => setSelectedSession(session)}
        />
      ))}
    </div>
  );
}

interface SessionCardProps {
  session: Session;
  onSelect: () => void;
}

function SessionCard({ session, onSelect }: SessionCardProps) {
  const connectedAgents = session.agents.filter(agent => agent.status === 'connected').length;

  return (
    <Card className="session-card hover:shadow-md transition-shadow cursor-pointer">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-lg">{session.name}</h3>
              <Badge variant={session.status === 'active' ? 'default' : 'secondary'}>
                {session.status}
              </Badge>
            </div>
            {session.description && (
              <p className="text-sm text-muted-foreground">{session.description}</p>
            )}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Users className="w-3 h-3" />
            <span>{connectedAgents}/{session.agents.length}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-3">
          <div className="agents-preview">
            <div className="flex gap-2 flex-wrap">
              {session.agents.slice(0, 3).map(agent => (
                <div key={agent.id} className="flex items-center gap-1">
                  <div className={`w-2 h-2 rounded-full ${
                    agent.status === 'connected' ? 'bg-green-500' : 'bg-gray-400'
                  }`} />
                  <span className="text-xs text-muted-foreground">{agent.name}</span>
                  {agent.role && (
                    <span className="text-xs text-muted-foreground/60">({agent.role})</span>
                  )}
                </div>
              ))}
              {session.agents.length > 3 && (
                <span className="text-xs text-muted-foreground">
                  +{session.agents.length - 3} more
                </span>
              )}
            </div>
          </div>
          
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="w-3 h-3" />
              <span>Created {formatDistanceToNow(new Date(session.created_at))} ago</span>
            </div>
            
            <Button variant="outline" size="sm" onClick={onSelect}>
              <Settings className="w-3 h-3 mr-1" />
              Manage
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}