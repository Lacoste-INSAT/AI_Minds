"use client";

/**
 * React hook for health status polling.
 * Uses live backend data only.
 */

import { useState, useEffect, useCallback } from "react";
import type { HealthResponse } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { APP_DEFAULTS } from "@/lib/constants";

export function useHealth(
  pollInterval = APP_DEFAULTS.HEALTH_POLL_INTERVAL
): AsyncState<HealthResponse> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<HealthResponse>>({
    status: "idle",
    data: null,
    error: null,
  });

  const fetchHealth = useCallback(async () => {
    setState((prev) => ({ ...prev, status: prev.data ? prev.status : "loading" }));
    const result = await apiClient.getHealth();

    if (result.ok) {
      setState({ status: "success", data: result.data, error: null });
    } else {
      setState({ status: "error", data: null, error: result.error });
    }
  }, []);

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchHealth();
    }, 0);
    const pollingTimer = window.setInterval(() => {
      void fetchHealth();
    }, pollInterval);
    return () => {
      window.clearTimeout(bootstrapTimer);
      window.clearInterval(pollingTimer);
    };
  }, [fetchHealth, pollInterval]);

  return { ...state, refetch: fetchHealth };
}
