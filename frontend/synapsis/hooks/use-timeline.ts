"use client";

/**
 * React hook for paginated timeline data.
 * Uses live backend data only.
 */

import { useState, useEffect, useCallback } from "react";
import type { TimelineResponse } from "@/types/contracts";
import type { AsyncState, TimelineFilters } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { APP_DEFAULTS } from "@/lib/constants";

interface UseTimelineReturn extends AsyncState<TimelineResponse> {
  filters: TimelineFilters;
  setFilters: (filters: Partial<TimelineFilters>) => void;
  page: number;
  setPage: (page: number) => void;
  refetch: () => void;
}

const DEFAULT_FILTERS: TimelineFilters = {
  modality: "all",
  category: "all",
  search: "",
  dateRange: { from: null, to: null },
};

export function useTimeline(): UseTimelineReturn {
  const [state, setState] = useState<AsyncState<TimelineResponse>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [filters, setFiltersState] = useState<TimelineFilters>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);

  const setFilters = useCallback((partial: Partial<TimelineFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...partial }));
    setPage(1); // Reset to first page on filter change
  }, []);

  const fetchTimeline = useCallback(async () => {
    setState((prev) => ({ ...prev, status: "loading" }));
    const result = await apiClient.getTimeline(
      page,
      APP_DEFAULTS.TIMELINE_PAGE_SIZE,
      {
        modality: filters.modality !== "all" ? filters.modality : undefined,
        category: filters.category !== "all" ? filters.category : undefined,
        search: filters.search || undefined,
        date_from: filters.dateRange.from || undefined,
        date_to: filters.dateRange.to || undefined,
      }
    );

    if (result.ok) {
      setState({ status: "success", data: result.data, error: null });
    } else {
      setState({ status: "error", data: null, error: result.error });
    }
  }, [page, filters]);

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchTimeline();
    }, 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
    };
  }, [fetchTimeline]);

  return {
    ...state,
    filters,
    setFilters,
    page,
    setPage,
    refetch: fetchTimeline,
  };
}
