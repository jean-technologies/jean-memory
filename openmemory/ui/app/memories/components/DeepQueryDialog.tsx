"use client";

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Sparkles } from "lucide-react";
import { toast } from 'sonner';
import { createClient } from '@supabase/supabase-js';

export function DeepQueryDialog() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState('');


  const handleQuery = async () => {
    if (!query.trim()) return;
    setIsLoading(true);
    setResult('');

    try {
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
      const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      
      if (sessionError || !session?.access_token) {
        throw new Error('Unable to get authentication token');
      }
      
      const accessToken = session.access_token;
      
      // Use the enhanced Jean Memory V2 deep life query endpoint
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://jean-memory-api-virginia.onrender.com';
      const response = await fetch(`${apiUrl}/api/v1/memories/deep-life-query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          query: query
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to get enhanced deep life query response');
      }

      const data = await response.json();
      setResult(data.result || data.response || data.answer);
      toast.success("Query completed!");

    } catch (error: any) {
      console.error("Enhanced deep query failed:", error);
      toast.error(error.message || "Failed to perform enhanced deep query.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      setOpen(isOpen);
      if (!isOpen) {
        setQuery('');
        setResult('');
      }
    }}>
      <DialogTrigger asChild>
        <Button>
          <Sparkles className="mr-2 h-4 w-4" />
          Deep Life Query
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Ask a Deep Life Query</DialogTitle>
          <DialogDescription>
            Ask a complex question about your life. Jean Memory V2 will analyze your comprehensive memory archive using advanced semantic search and ontology-guided insights.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <Textarea
            placeholder="e.g., What are the most significant themes in my life over the past year?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="min-h-[100px]"
          />
          {isLoading && (
            <div className="flex items-center justify-center p-4">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          )}
          {result && !isLoading && (
            <div className="p-4 bg-muted/50 rounded-lg text-sm prose dark:prose-invert max-w-none">
              <p>{result}</p>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
          <Button onClick={handleQuery} disabled={isLoading || !query.trim()}>
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Ask"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 