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
import { Loader2 } from "lucide-react";
import { useMemoriesApi } from "@/hooks/useMemoriesApi";
import { useMemoriesApiV3 } from "@/hooks/useMemoriesApiV3";
import { toast } from "sonner";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Zap } from "lucide-react";

export function CreateMemoryDialog() {
  const { createMemory, isLoading, fetchMemories } = useMemoriesApi();
  const { isSTMEnabled, isSTMReady, createMemory: createMemoryV3 } = useMemoriesApiV3();
  const [open, setOpen] = useState(false);
  const [useSTM, setUseSTM] = useState(isSTMEnabled && isSTMReady);
  const textRef = useRef<HTMLTextAreaElement>(null);

  const handleCreateMemory = async (text: string) => {
    try {
      if (useSTM && isSTMEnabled && isSTMReady) {
        await createMemoryV3(text, true); // Use STM mode
        toast.success("Memory created instantly with Smart Memory");
      } else {
        await createMemory(text);
        toast.success("Memory created successfully");
      }
      
      // clear the textarea
      if (textRef.current) {
        textRef.current.value = "";
      }
      // close the dialog
      setOpen(false);
      // refetch memories
      await fetchMemories();
    } catch (error) {
      console.error(error);
      toast.error("Failed to create memory");
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <GoPlus className="mr-1" />
          Create Memory
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Create New Memory</DialogTitle>
          <DialogDescription>
            Add a new memory to your Jean Memory instance
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="memory">Memory</Label>
            <Textarea
              ref={textRef}
              id="memory"
              placeholder="e.g., Lives in San Francisco"
              className="min-h-[150px]"
            />
          </div>
          
          {/* STM Mode Toggle */}
          {isSTMEnabled && (
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border">
              <div className="flex items-center space-x-2">
                <Zap className="h-4 w-4 text-blue-600" />
                <div>
                  <Label htmlFor="stm-mode" className="text-sm font-medium">
                    Smart Memory Mode
                  </Label>
                  <p className="text-xs text-gray-600">
                    Instant creation and local search
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {isSTMReady && (
                  <Badge variant="secondary" className="text-xs">
                    Ready
                  </Badge>
                )}
                <Switch
                  id="stm-mode"
                  checked={useSTM}
                  onCheckedChange={setUseSTM}
                  disabled={!isSTMReady}
                />
              </div>
            </div>
          )}
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
