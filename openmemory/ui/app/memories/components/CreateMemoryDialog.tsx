"use client";

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
import { Label } from "@/components/ui/label";
import { useState, useRef } from "react";
import { GoPlus } from "react-icons/go";
import { Loader2, Calendar } from "lucide-react";
import { useMemoriesApi } from "@/hooks/useMemoriesApi";
import { toast } from "sonner";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";

export function CreateMemoryDialog() {
  const { createMemory, isLoading, fetchMemories } = useMemoriesApi();
  const [open, setOpen] = useState(false);
  const [useMemoryDate, setUseMemoryDate] = useState(false);
  const textRef = useRef<HTMLTextAreaElement>(null);
  const memoryDateRef = useRef<HTMLInputElement>(null);

  const handleCreateMemory = async (text: string) => {
    try {
      // Get memory date if specified
      let memoryDate = null;
      if (useMemoryDate && memoryDateRef.current?.value) {
        memoryDate = new Date(memoryDateRef.current.value).toISOString();
      }

      // TODO: Update the API to accept memory_date as a separate parameter
      // For now, just create the memory with text only
      await createMemory(text);
      toast.success("Memory created successfully");
      
      // Clear the form
      if (textRef.current) {
        textRef.current.value = "";
      }
      if (memoryDateRef.current) {
        memoryDateRef.current.value = "";
      }
      setUseMemoryDate(false);
      
      // Close dialog and refetch
      setOpen(false);
      await fetchMemories();
    } catch (error) {
      console.error(error);
      toast.error("Failed to create memory");
    }
  };

  // Get today's date in YYYY-MM-DD format for the date input
  const today = new Date().toISOString().split('T')[0];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="bg-zinc-800 hover:bg-zinc-700 text-white border-zinc-700"
        >
          <GoPlus className="mr-1" />
          Create Memory
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px] bg-zinc-900 border-zinc-800">
        <DialogHeader>
          <DialogTitle>Create New Memory</DialogTitle>
          <DialogDescription>
            Add a new memory to your Jean Memory instance. Optionally specify when the memory event actually occurred.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="memory">Memory</Label>
            <Textarea
              ref={textRef}
              id="memory"
              placeholder="e.g., Lives in San Francisco, or Yesterday I had lunch with Sarah at the new restaurant downtown"
              className="bg-zinc-950 border-zinc-800 min-h-[150px]"
            />
          </div>
          
          <div className="grid gap-3">
            <div className="flex items-center space-x-2">
              <Checkbox 
                id="use-memory-date" 
                checked={useMemoryDate}
                onCheckedChange={(checked) => setUseMemoryDate(checked === true)}
              />
              <Label htmlFor="use-memory-date" className="text-sm font-medium">
                Specify when this memory event occurred
              </Label>
            </div>
            
            {useMemoryDate && (
              <div className="grid gap-2">
                <Label htmlFor="memory-date" className="text-sm text-zinc-400">
                  Memory Date
                </Label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-3 h-4 w-4 text-zinc-400" />
                  <Input
                    ref={memoryDateRef}
                    id="memory-date"
                    type="date"
                    max={today}
                    className="bg-zinc-950 border-zinc-800 pl-10"
                    placeholder="When did this memory event occur?"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  Leave blank to use the current date, or specify when the memory event actually happened.
                </p>
              </div>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button
            disabled={isLoading}
            onClick={() => handleCreateMemory(textRef?.current?.value || "")}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              "Save Memory"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
