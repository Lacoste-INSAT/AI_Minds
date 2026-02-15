"use client";

/**
 * TimelineFilters — Filter bar for timeline view.
 * Provides modality, category, search, and date-range filters.
 *
 * Source: ARCHITECTURE.md §Timeline, DESIGN_SYSTEM.md
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { X, Filter } from "lucide-react";
import { MODALITY_CONFIG } from "@/lib/constants";
import type { TimelineFilters as TimelineFiltersType} from "@/types/ui";
import type { TimelineModality } from "@/types/contracts";
import { cn } from "@/lib/utils";

// ── Common category list (derived from mock data and typical usage) ──

const CATEGORIES = [
  "all",
  "engineering",
  "meetings",
  "research",
  "notes",
  "documentation",
] as const;

// ── Props ──

interface TimelineFiltersProps {
  filters: TimelineFiltersType;
  onFilterChange: (partial: Partial<TimelineFiltersType>) => void;
  totalItems?: number;
  className?: string;
}

export function TimelineFiltersBar({
  filters,
  onFilterChange,
  totalItems,
  className,
}: TimelineFiltersProps) {
  const hasActiveFilters =
    filters.modality !== "all" ||
    filters.category !== "all" ||
    filters.search.length > 0 ||
    Boolean(filters.dateRange.from) ||
    Boolean(filters.dateRange.to);

  const clearFilters = () => {
    onFilterChange({
      modality: "all",
      category: "all",
      search: "",
      dateRange: { from: null, to: null },
    });
  };

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 rounded-lg border bg-card px-4 py-3",
        className
      )}
      role="search"
      aria-label="Timeline filters"
    >
      <Filter className="h-4 w-4 text-muted-foreground" aria-hidden />

      {/* Search input */}
      <Input
        placeholder="Filter items..."
        value={filters.search}
        onChange={(e) => onFilterChange({ search: e.target.value })}
        className="h-8 w-48 text-sm"
        aria-label="Search timeline items"
      />

      {/* Modality select */}
      <Select
        value={filters.modality}
        onValueChange={(v) =>
          onFilterChange({ modality: v as TimelineModality | "all" })
        }
      >
        <SelectTrigger
          className="h-8 w-32 text-sm"
          aria-label="Filter by modality"
        >
          <SelectValue placeholder="Modality" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All types</SelectItem>
          {(Object.keys(MODALITY_CONFIG) as TimelineModality[]).map((mod) => (
            <SelectItem key={mod} value={mod}>
              {MODALITY_CONFIG[mod].label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Category select */}
      <Select
        value={filters.category}
        onValueChange={(v) => onFilterChange({ category: v })}
      >
        <SelectTrigger
          className="h-8 w-36 text-sm"
          aria-label="Filter by category"
        >
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          {CATEGORIES.map((cat) => (
            <SelectItem key={cat} value={cat}>
              {cat === "all"
                ? "All categories"
                : cat.charAt(0).toUpperCase() + cat.slice(1)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Input
        type="date"
        value={filters.dateRange.from ?? ""}
        onChange={(event) =>
          onFilterChange({
            dateRange: {
              ...filters.dateRange,
              from: event.target.value || null,
            },
          })
        }
        className="h-8 w-36 text-sm"
        aria-label="From date"
      />

      <Input
        type="date"
        value={filters.dateRange.to ?? ""}
        onChange={(event) =>
          onFilterChange({
            dateRange: {
              ...filters.dateRange,
              to: event.target.value || null,
            },
          })
        }
        className="h-8 w-36 text-sm"
        aria-label="To date"
      />

      {/* Active filter indicator + clear */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1.5 text-xs text-muted-foreground"
          onClick={clearFilters}
          aria-label="Clear all filters"
        >
          <X className="h-3 w-3" />
          Clear
        </Button>
      )}

      {/* Item count */}
      {totalItems !== undefined && (
        <span className="ml-auto text-xs text-muted-foreground" aria-live="polite">
          {totalItems} {totalItems === 1 ? "item" : "items"}
        </span>
      )}
    </div>
  );
}
