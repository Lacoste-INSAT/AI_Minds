"use client";

/**
 * React hook for graph data.
 * Falls back to mock data when backend is unavailable.
 */

import { useState, useEffect, useCallback } from "react";
import type { GraphData } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { MOCK_GRAPH } from "@/mocks/fixtures";
import { APP_DEFAULTS } from "@/lib/constants";

export function useGraph(
  limit = APP_DEFAULTS.GRAPH_NODE_LIMIT
): AsyncState<GraphData> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<GraphData>>({
    status: "idle",
    data: null,
    error: null,
  });

  const fetchGraph = useCallback(async () => {
    setState((prev) => ({ ...prev, status: "loading" }));
    const result = await apiClient.getGraph(limit);

    if (result.ok) {
      setState({ status: "success", data: result.data, error: null });
    } else {
      // Fallback to mock
      setState({ status: "success", data: MOCK_GRAPH, error: null });
    }
  }, [limit]);

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchGraph();
    }, 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
    };
  }, [fetchGraph]);

  return { ...state, refetch: fetchGraph };
}
