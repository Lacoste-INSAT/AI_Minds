"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MODALITY_CONFIG } from "@/lib/constants";
import type { TimelineModality } from "@/types/contracts";
import type { SearchFilters as SearchFiltersState } from "@/types/ui";

const SEARCH_CATEGORIES = ["all", "engineering", "meetings", "research", "documentation"] as const;

interface SearchFiltersProps {
  filters: SearchFiltersState;
  onFilterChange: (filters: Partial<SearchFiltersState>) => void;
}

export function SearchFilters({ filters, onFilterChange }: SearchFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border bg-card px-4 py-3">
      <Search className="h-4 w-4 text-muted-foreground" aria-hidden />
      <Input
        placeholder="Search your knowledge base..."
        value={filters.query}
        onChange={(event) => onFilterChange({ query: event.target.value })}
        className="h-8 min-w-[200px] flex-1 text-sm"
        aria-label="Search query"
        autoFocus
      />

      <Select
        value={filters.modality}
        onValueChange={(value) =>
          onFilterChange({ modality: value as TimelineModality | "all" })
        }
      >
        <SelectTrigger className="h-8 w-32 text-sm" aria-label="Filter by modality">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All types</SelectItem>
          {(Object.keys(MODALITY_CONFIG) as TimelineModality[]).map((modality) => (
            <SelectItem key={modality} value={modality}>
              {MODALITY_CONFIG[modality].label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.category}
        onValueChange={(value) => onFilterChange({ category: value })}
      >
        <SelectTrigger className="h-8 w-40 text-sm" aria-label="Filter by category">
          <SelectValue placeholder="All categories" />
        </SelectTrigger>
        <SelectContent>
          {SEARCH_CATEGORIES.map((category) => (
            <SelectItem key={category} value={category}>
              {category === "all"
                ? "All categories"
                : category.charAt(0).toUpperCase() + category.slice(1)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

