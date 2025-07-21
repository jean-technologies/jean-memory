"use client";

import { useEffect, useState } from "react";
import { MemoriesSection } from "@/app/memories/components/MemoriesSection";
import { MemoryFilters } from "@/app/memories/components/MemoryFilters";
import { useRouter, useSearchParams } from "next/navigation";
import "@/styles/animation.css";
import UpdateMemory from "@/components/shared/update-memory";
import { useUI } from "@/hooks/useUI";
import { DeepQueryDialog } from "./components/DeepQueryDialog";
import { useMemoriesApi } from "@/hooks/useMemoriesApi";
import { useSelector } from "react-redux";
import { RootState } from "@/store/store";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { STMToggle } from "@/components/memory-v3/STMToggle";

export default function MemoriesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { updateMemoryDialog, handleCloseUpdateMemoryDialog } = useUI();
  const { fetchMemories } = useMemoriesApi();
  const [memories, setMemories] = useState<any[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const filters = useSelector((state: RootState) => state.filters.apps);

  useEffect(() => {
    loadMemories();
  }, [searchParams, filters]);

  const loadMemories = async () => {
    setIsLoading(true);
    try {
      const searchQuery = searchParams.get("search") || "";
      const result = await fetchMemories(
        searchQuery,
        {
          apps: filters.selectedApps,
          categories: filters.selectedCategories,
          sortColumn: filters.sortColumn,
          sortDirection: filters.sortDirection,
          showArchived: filters.showArchived,
          groupThreads: true, // Enable threading for memories page
        }
      );
      setMemories(result.memories);
      setTotalItems(result.total);
    } catch (error) {
      console.error("Failed to fetch memories:", error);
    }
    setIsLoading(false);
  };

  const handleClearFilters = () => {
    // This will be handled by the FilterComponent's Redux action
  };

  return (
    <ProtectedRoute>
      <div className="">
      <UpdateMemory
        memoryId={updateMemoryDialog.memoryId || ""}
        memoryContent={updateMemoryDialog.memoryContent || ""}
        open={updateMemoryDialog.isOpen}
        onOpenChange={handleCloseUpdateMemoryDialog}
      />
      <main className="flex-1 py-6">
        <div className="container">
          {/* Sticky Header with Search, Filters, and Deep Query */}
          <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border/40 pb-4 mb-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mt-1 pt-4 animate-fade-slide-down">
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 w-full md:w-auto">
                <MemoryFilters onFilterChange={loadMemories} />
                {/* <STMToggle /> */}
              </div>
              <div className="flex items-center">
                <DeepQueryDialog />
              </div>
            </div>
          </div>
          {/* Scrollable Content */}
          <div className="animate-fade-slide-down delay-1">
            <MemoriesSection
              memories={memories}
              totalItems={totalItems}
              isLoading={isLoading}
              onClearFilters={handleClearFilters}
              hasActiveFilters={
                filters.selectedApps.length > 0 ||
                filters.selectedCategories.length > 0 ||
                filters.showArchived
              }
            />
          </div>
        </div>
      </main>
    </div>
    </ProtectedRoute>
  );
}
