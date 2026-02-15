"use client";

import { useTimeline } from "@/hooks/use-timeline";
import { useInsights } from "@/hooks/use-insights";
import { TimelineFiltersBar } from "@/components/timeline/timeline-filters";
import { TimelineFeed } from "@/components/timeline/timeline-feed";
import { InsightsStrip } from "@/components/timeline/insights-strip";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function TimelinePage() {
  const { data, status, filters, setFilters, page, setPage } = useTimeline();
  const { digest } = useInsights();

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  return (
    <div className="flex h-full flex-col gap-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Timeline</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse your memory feed
        </p>
      </div>

      {/* Insights strip (non-blocking) */}
      {digest.data?.insights && (
        <InsightsStrip insights={digest.data.insights} />
      )}

      <TimelineFiltersBar
        filters={filters}
        onFilterChange={setFilters}
        totalItems={data?.total}
      />

      <TimelineFeed
        items={data?.items ?? []}
        isLoading={status === "loading"}
        className="flex-1"
      />

      {/* Pagination */}
      {data && totalPages > 1 && (
        <div className="flex items-center justify-between border-t pt-3">
          <span className="text-xs text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
