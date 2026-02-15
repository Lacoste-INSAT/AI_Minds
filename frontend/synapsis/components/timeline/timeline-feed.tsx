"use client";

/**
 * TimelineFeed — Grouped, virtualized timeline feed.
 * Groups items by ingestion date and renders KnowledgeCards.
 * Uses react-virtuoso for large-list perf when available.
 *
 * Source: ARCHITECTURE.md §Timeline, DESIGN_SYSTEM.md
 */

import { useMemo } from "react";
import { Clock, Inbox } from "lucide-react";
import { GroupedVirtuoso } from "react-virtuoso";
import { Skeleton } from "@/components/ui/skeleton";
import { KnowledgeCard } from "./knowledge-card";
import { formatRelativeDate, getDateGroupKey, cn } from "@/lib/utils";
import { BRAND_COPY } from "@/lib/constants";
import type { TimelineItem } from "@/types/contracts";
import type { TimelineGroupedItems } from "@/types/ui";

// ── Props ──

interface TimelineFeedProps {
  items: TimelineItem[];
  isLoading: boolean;
  onSelectItem?: (id: string) => void;
  className?: string;
}

/**
 * Group items by date key and produce label for each group.
 */
function groupByDate(items: TimelineItem[]): TimelineGroupedItems[] {
  const map = new Map<string, TimelineItem[]>();

  for (const item of items) {
    const key = getDateGroupKey(item.ingested_at);
    const existing = map.get(key);
    if (existing) {
      existing.push(item);
    } else {
      map.set(key, [item]);
    }
  }

  return Array.from(map.entries())
    .sort((a, b) => b[0].localeCompare(a[0])) // newest first
    .map(([date, groupItems]) => ({
      label: formatRelativeDate(groupItems[0].ingested_at),
      date,
      items: groupItems,
    }));
}

export function TimelineFeed({
  items,
  isLoading,
  onSelectItem,
  className,
}: TimelineFeedProps) {
  const groups = useMemo(() => groupByDate(items), [items]);
  const groupCounts = useMemo(
    () => groups.map((group) => group.items.length),
    [groups]
  );

  // ── Loading skeleton ──
  if (isLoading && items.length === 0) {
    return (
      <div className={cn("space-y-4", className)} aria-busy="true">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-2">
            {i === 0 && <Skeleton className="h-4 w-24" />}
            <Skeleton className="h-32 w-full rounded-lg" />
          </div>
        ))}
      </div>
    );
  }

  // ── Empty state ──
  if (!isLoading && items.length === 0) {
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
        <p className="text-sm text-muted-foreground">{BRAND_COPY.EMPTY_TIMELINE}</p>
      </div>
    );
  }

  // ── Grouped feed ──
  return (
    <div className={cn("h-full", className)} role="feed" aria-label="Knowledge timeline">
      <GroupedVirtuoso
        groupCounts={groupCounts}
        overscan={300}
        groupContent={(groupIndex) => {
          const group = groups[groupIndex];
          return (
            <div className="sticky top-0 z-10 flex items-center gap-2 bg-background/85 px-2 py-1 backdrop-blur-sm">
              <Clock className="h-3.5 w-3.5 text-primary" aria-hidden />
              <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {group.label}
              </h2>
              <div className="h-px flex-1 bg-border" aria-hidden />
              <span className="text-[10px] text-muted-foreground">{group.items.length}</span>
            </div>
          );
        }}
        itemContent={(index, groupIndex) => {
          const item = groups[groupIndex]?.items[index];
          if (!item) return null;

          return (
            <div className="px-1 py-1.5">
              <KnowledgeCard item={item} onSelect={onSelectItem} />
            </div>
          );
        }}
      />
    </div>
  );
}
