"use client";

/**
 * SearchResults — Displays search results as cards or table.
 * Supports modality, entity, and category filtering.
 *
 * Source: ARCHITECTURE.md §Search, DESIGN_SYSTEM.md
 */

import {
  FileText,
  FileType,
  Image as ImageIcon,
  Headphones,
  Search as SearchIcon,
  Inbox,
} from "lucide-react";
import type { ElementType } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EntityChip } from "@/components/shared/entity-chip";
import { formatRelativeDate, cn } from "@/lib/utils";
import { BRAND_COPY } from "@/lib/constants";
import type { TimelineModality } from "@/types/contracts";
import type { EntityType, SearchResult } from "@/types/ui";

// ── Icon map ──

const MODALITY_ICONS: Record<TimelineModality, ElementType> = {
  text: FileText,
  pdf: FileType,
  image: ImageIcon,
  audio: Headphones,
};

// ── Props ──

interface SearchResultsProps {
  items: SearchResult[];
  isLoading: boolean;
  query: string;
  onSelect?: (result: SearchResult) => void;
  className?: string;
}

/**
 * Simple entity type inference (same as KnowledgeCard).
 */
function inferEntityType(name: string): EntityType {
  const lower = name.toLowerCase();
  if (lower.includes("inc") || lower.includes("corp") || lower.includes("org"))
    return "organization";
  if (lower.includes("project") || lower.includes("system")) return "project";
  return "concept";
}

export function SearchResults({
  items,
  isLoading,
  query,
  onSelect,
  className,
}: SearchResultsProps) {
  // Loading skeletons
  if (isLoading) {
    return (
      <div className={cn("space-y-3", className)} aria-busy="true">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  // No query yet
  if (!query.trim()) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center gap-3 py-16 text-center",
          className
        )}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <SearchIcon className="h-6 w-6 text-muted-foreground" aria-hidden />
        </div>
        <p className="text-sm text-muted-foreground">
          Enter a query to search your knowledge base
        </p>
      </div>
    );
  }

  // Empty results
  if (items.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col items-center justify-center gap-3 py-16 text-center",
          className
        )}
        role="status"
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
          <Inbox className="h-6 w-6 text-muted-foreground" aria-hidden />
        </div>
        <p className="text-sm text-muted-foreground">{BRAND_COPY.EMPTY_SEARCH}</p>
      </div>
    );
  }

  return (
    <div
      className={cn("space-y-3", className)}
      role="list"
      aria-label="Search results"
    >
      <p className="text-xs text-muted-foreground" aria-live="polite">
        {items.length} {items.length === 1 ? "result" : "results"} for &quot;{query}&quot;
      </p>

      {items.map((item) => {
        const ModalityIcon = MODALITY_ICONS[item.modality] ?? FileText;
        return (
          <Card
            key={item.id}
            className="group cursor-pointer transition-colors hover:border-primary/40"
            onClick={() => onSelect?.(item)}
            tabIndex={0}
            role="listitem"
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect?.(item);
              }
            }}
          >
            <CardHeader className="flex flex-row items-start gap-3 space-y-0 pb-2">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                <ModalityIcon className="h-4 w-4 text-primary" aria-hidden />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="line-clamp-1 text-sm font-semibold">{item.title}</h3>
                <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{formatRelativeDate(item.ingested_at)}</span>
                  <span aria-hidden>·</span>
                  <Badge variant="outline" className="px-1.5 py-0 text-[10px]">
                    {item.category}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 pt-0">
              <p className="line-clamp-2 text-sm text-muted-foreground">
                {item.snippet}
              </p>
              {item.entities.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {item.entities.slice(0, 4).map((entity) => (
                    <EntityChip
                      key={entity}
                      name={entity}
                      type={inferEntityType(entity)}
                      size="sm"
                    />
                  ))}
                  {item.entities.length > 4 && (
                    <Badge variant="secondary" className="text-[10px]">
                      +{item.entities.length - 4}
                    </Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
