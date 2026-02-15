"use client";

/**
 * React hook for ingestion status polling.
 * Uses live backend data only.
 */

import { useState, useEffect, useCallback } from "react";
import type { IngestionStatusResponse } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { APP_DEFAULTS } from "@/lib/constants";

export function useIngestionStatus(
  pollInterval = APP_DEFAULTS.INGESTION_POLL_INTERVAL
): AsyncState<IngestionStatusResponse> & {
  refetch: () => void;
  triggerScan: () => Promise<void>;
} {
  const [state, setState] = useState<AsyncState<IngestionStatusResponse>>({
    status: "idle",
    data: null,
    error: null,
  });

  const fetchStatus = useCallback(async () => {
    setState((prev) => ({ ...prev, status: prev.data ? prev.status : "loading" }));
    const result = await apiClient.getIngestionStatus();

    if (result.ok) {
      setState({ status: "success", data: result.data, error: null });
    } else {
      setState({ status: "error", data: null, error: result.error });
    }
  }, []);

  const triggerScan = useCallback(async () => {
    await apiClient.triggerScan();
    void fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchStatus();
    }, 0);
    const pollingTimer = window.setInterval(() => {
      void fetchStatus();
    }, pollInterval);
    return () => {
      window.clearTimeout(bootstrapTimer);
      window.clearInterval(pollingTimer);
    };
  }, [fetchStatus, pollInterval]);

  return { ...state, refetch: fetchStatus, triggerScan };
}
