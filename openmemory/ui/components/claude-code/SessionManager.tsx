"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { SessionList } from "./SessionList";
import { CreateSessionDialog } from "./CreateSessionDialog";

export interface Agent {
  id: string;
  session_id: string;
  name: string;
  role?: string;
  connection_url: string;
  status: 'connected' | 'disconnected';
  last_activity: string;
}

export interface Session {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  agents: Agent[];
  status: 'active' | 'inactive';
}

export function SessionManager() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/claude-code/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data);
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionCreated = (session: Session) => {
    setSessions([session, ...sessions]);
    setShowCreateDialog(false);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">Multi-Agent Sessions</h2>
          <div className="h-10 w-32 bg-muted animate-pulse rounded"></div>
        </div>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-muted animate-pulse rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="claude-code-sessions space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold">Multi-Agent Sessions</h2>
          <p className="text-sm text-muted-foreground">
            Create and manage collaborative Claude Code sessions
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create New Session
        </Button>
      </div>
      
      <SessionList sessions={sessions} onSessionUpdate={fetchSessions} />
      
      {showCreateDialog && (
        <CreateSessionDialog 
          open={showCreateDialog}
          onClose={() => setShowCreateDialog(false)}
          onSessionCreated={handleSessionCreated}
        />
      )}
    </div>
  );
}