import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Category, Client } from "../../../components/types";
import { MemoryTable } from "./MemoryTable";
import { CreateMemoryDialog } from "./CreateMemoryDialog";
import { useMemoriesApi } from "@/hooks/useMemoriesApi";
import { useRouter, useSearchParams } from "next/navigation";
import { MemoryTableSkeleton } from "@/skeleton/MemoryTableSkeleton";

interface MemoriesSectionProps {
  memories: any[];
  totalItems: number;
  isLoading: boolean;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
}

export function MemoriesSection({
  memories,
  totalItems,
  isLoading,
  onClearFilters,
  hasActiveFilters,
}: MemoriesSectionProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { fetchMemories } = useMemoriesApi();

  const [selectedCategory, setSelectedCategory] = useState<Category | "all">(
    "all"
  );
  const [selectedClient, setSelectedClient] = useState<Client | "all">("all");

  if (isLoading) {
    return (
      <div className="w-full bg-transparent">
        <MemoryTableSkeleton />
        <div className="flex items-center justify-between mt-4">
          <div className="h-8 w-32 bg-muted rounded animate-pulse" />
          <div className="h-8 w-48 bg-muted rounded animate-pulse" />
          <div className="h-8 w-32 bg-muted rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-transparent">
      <div>
        {memories.length > 0 ? (
          <>
            <MemoryTable memories={memories} />
            <div className="flex items-center justify-end mt-4">
              <div className="text-sm text-zinc-500">
                Total: {totalItems} memories
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="relative mb-6">
              <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
              <div className="relative rounded-full bg-card border border-border p-6">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-primary"
                >
                  <path d="M12 2v20M2 12h20M8 8l8 8M16 8l-8 8" opacity="0.3"/>
                  <circle cx="12" cy="12" r="3"/>
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" opacity="0.2"/>
                </svg>
              </div>
            </div>
            <h3 className="text-xl font-semibold text-foreground mb-2">
              {hasActiveFilters
                ? "No memories match your filters"
                : "Start Building Your Memory Bank"}
            </h3>
            <p className="text-muted-foreground mb-6 max-w-md">
              {hasActiveFilters
                ? "Try adjusting your filters to see more memories"
                : "Your AI conversations will appear here. Connect an app above and start chatting to create your first memory!"}
            </p>
            {hasActiveFilters ? (
              <Button
                variant="outline"
                onClick={onClearFilters}
              >
                Clear Filters
              </Button>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <CreateMemoryDialog />
                <p className="text-xs text-muted-foreground">
                  Or start chatting with Claude, Cursor, or any connected app
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
