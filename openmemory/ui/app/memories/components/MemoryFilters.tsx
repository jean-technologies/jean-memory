"use client";
import { Archive, Pause, Play, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { FiTrash2 } from "react-icons/fi";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "@/store/store";
import { clearSelection } from "@/store/memoriesSlice";
import { useMemoriesApi } from "@/hooks/useMemoriesApi";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter, useSearchParams } from "next/navigation";
import { debounce } from "lodash";
import { useEffect, useRef } from "react";
import FilterComponent from "./FilterComponent";
import { clearFilters } from "@/store/filtersSlice";

export function MemoryFilters({ onFilterChange }: { onFilterChange: () => void }) {
  const dispatch = useDispatch();
  const selectedMemoryIds = useSelector(
    (state: RootState) => state.memories.selectedMemoryIds
  );
  const { deleteMemories, updateMemoryState, fetchMemories } = useMemoriesApi();
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeFilters = useSelector((state: RootState) => state.filters.apps);

  const inputRef = useRef<HTMLInputElement>(null);

  const handleDeleteSelected = async () => {
    try {
      await deleteMemories(selectedMemoryIds);
      dispatch(clearSelection());
    } catch (error) {
      console.error("Failed to delete memories:", error);
    }
  };

  const handleArchiveSelected = async () => {
    try {
      await updateMemoryState(selectedMemoryIds, "archived");
    } catch (error) {
      console.error("Failed to archive memories:", error);
    }
  };

  const handlePauseSelected = async () => {
    try {
      await updateMemoryState(selectedMemoryIds, "paused");
    } catch (error) {
      console.error("Failed to pause memories:", error);
    }
  };

  const handleResumeSelected = async () => {
    try {
      await updateMemoryState(selectedMemoryIds, "active");
    } catch (error) {
      console.error("Failed to resume memories:", error);
    }
  };

  // add debounce
  const handleSearch = debounce(async (query: string) => {
    router.push(`/memories?search=${query}`);
  }, 500);

  useEffect(() => {
    // if the url has a search param, set the input value to the search param
    if (searchParams.get("search")) {
      if (inputRef.current) {
        inputRef.current.value = searchParams.get("search") || "";
        inputRef.current.focus();
      }
    }
  }, []);

  const handleClearAllFilters = async () => {
    dispatch(clearFilters());
    await onFilterChange(); // Use the callback to refetch memories
  };

  const hasActiveFilters =
    activeFilters.selectedApps.length > 0 ||
    activeFilters.selectedCategories.length > 0;

  return (
    <div className="flex flex-col md:flex-row gap-4 mb-4">
      <div className="relative flex-1">
        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={inputRef}
          placeholder="Search memories..."
          className="pl-8 bg-background border-border max-w-[500px]"
          onChange={(e) => handleSearch(e.target.value)}
        />
      </div>
      <div className="flex gap-2">
        <FilterComponent onFilterChange={onFilterChange} />
        {hasActiveFilters && (
          <Button
            variant="outline"
            onClick={handleClearAllFilters}
          >
            Clear Filters
          </Button>
        )}
        {selectedMemoryIds.length > 0 && (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                >
                  Actions
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
              >
                <DropdownMenuItem onClick={handleArchiveSelected}>
                  <Archive className="mr-2 h-4 w-4" />
                  Archive Selected
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handlePauseSelected}>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause Selected
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleResumeSelected}>
                  <Play className="mr-2 h-4 w-4" />
                  Resume Selected
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={handleDeleteSelected}
                  className="text-red-500"
                >
                  <FiTrash2 className="mr-2 h-4 w-4" />
                  Delete Selected
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        )}
      </div>
    </div>
  );
}
