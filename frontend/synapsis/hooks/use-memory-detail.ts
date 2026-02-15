"use client";

/**
 * React hook for memory detail (source drill-down).
 */

import { useState, useEffect, useCallback } from "react";
import type { MemoryDetail } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";

export function useMemoryDetail(
  id: string | null
): AsyncState<MemoryDetail> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<MemoryDetail>>({
    status: "idle",
    data: null,
    error: null,
  });

  const fetchDetail = useCallback(async () => {
    if (!id) return;
    setState({ status: "loading", data: null, error: null });
    const result = await apiClient.getMemoryDetail(id);

    if (result.ok) {
      setState({ status: "success", data: result.data, error: null });
    } else {
      setState({ status: "error", data: null, error: result.error });
    }
  }, [id]);

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchDetail();
    }, 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
    };
  }, [fetchDetail]);

  return { ...state, refetch: fetchDetail };
}
