"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, X } from "lucide-react";
import { toast } from "sonner";
import { Session } from "./SessionManager";

interface CreateSessionDialogProps {
  open: boolean;
  onClose: () => void;
  onSessionCreated: (session: Session) => void;
}

interface AgentFormData {
  name: string;
  role: string;
}

export function CreateSessionDialog({ open, onClose, onSessionCreated }: CreateSessionDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    agents: [{ name: '', role: '' }] as AgentFormData[]
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const addAgent = () => {
    if (formData.agents.length < 3) {
      setFormData({
        ...formData,
        agents: [...formData.agents, { name: '', role: '' }]
      });
    }
  };

  const removeAgent = (index: number) => {
    if (formData.agents.length > 1) {
      setFormData({
        ...formData,
        agents: formData.agents.filter((_, i) => i !== index)
      });
    }
  };

  const updateAgent = (index: number, field: keyof AgentFormData, value: string) => {
    const newAgents = [...formData.agents];
    newAgents[index][field] = value;
    setFormData({ ...formData, agents: newAgents });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.name.trim()) {
      toast.error('Session name is required');
      return;
    }

    const validAgents = formData.agents.filter(agent => agent.name.trim());
    if (validAgents.length === 0) {
      toast.error('At least one agent is required');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/v1/claude-code/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name.trim(),
          description: formData.description.trim(),
          agents: validAgents.map(agent => ({
            name: agent.name.trim(),
            role: agent.role.trim()
          }))
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const session = await response.json();
      onSessionCreated(session);
      toast.success('Session created successfully');
      
      // Reset form
      setFormData({
        name: '',
        description: '',
        agents: [{ name: '', role: '' }]
      });
      
    } catch (error) {
      console.error('Failed to create session:', error);
      toast.error('Failed to create session');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Multi-Agent Session</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Set up a collaborative session for multiple Claude Code agents
          </p>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Session Name *</Label>
              <Input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="e.g., WebScraper Development"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Brief description of the project or collaboration"
                rows={3}
              />
            </div>
            
            <div className="agents-section space-y-4">
              <div className="flex justify-between items-center">
                <Label>Agents ({formData.agents.length}/3)</Label>
                {formData.agents.length < 3 && (
                  <Button type="button" variant="outline" size="sm" onClick={addAgent}>
                    <Plus className="w-4 h-4 mr-1" />
                    Add Agent
                  </Button>
                )}
              </div>
              
              <div className="space-y-3">
                {formData.agents.map((agent, index) => (
                  <div key={index} className="agent-form border rounded-lg p-4 space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Agent {index + 1}</span>
                      {formData.agents.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeAgent(index)}
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <Label className="text-xs">Agent Name *</Label>
                        <Input
                          type="text"
                          placeholder="e.g., researcher, implementer"
                          value={agent.name}
                          onChange={(e) => updateAgent(index, 'name', e.target.value)}
                          required
                        />
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Role (Optional)</Label>
                        <Input
                          type="text"
                          placeholder="e.g., data analysis, frontend"
                          value={agent.role}
                          onChange={(e) => updateAgent(index, 'role', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <DialogFooter className="mt-6">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Session'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}