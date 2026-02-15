"use client";

/**
 * useInsights — Hook for consuming insights endpoints.
 * Fetches digest, patterns, and all insights from live backend.
 *
 * Source: FE-056 specification, BACKEND_CONTRACT_ALIGNMENT.md
 */

import { useState, useEffect, useCallback } from "react";
import type { InsightItem, DigestResponse, PatternsResponse } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";

interface UseInsightsReturn {
  digest: AsyncState<DigestResponse>;
  patterns: AsyncState<PatternsResponse>;
  allInsights: AsyncState<InsightItem[]>;
  refetch: () => void;
}

export function useInsights(): UseInsightsReturn {
  const [digest, setDigest] = useState<AsyncState<DigestResponse>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [patterns, setPatterns] = useState<AsyncState<PatternsResponse>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [allInsights, setAllInsights] = useState<AsyncState<InsightItem[]>>({
    status: "idle",
    data: null,
    error: null,
  });

  const fetchAll = useCallback(async () => {
    setDigest((prev) => ({ ...prev, status: "loading" }));
    setPatterns((prev) => ({ ...prev, status: "loading" }));
    setAllInsights((prev) => ({ ...prev, status: "loading" }));

    // Fetch all three in parallel
    const [digestResult, patternsResult, allResult] = await Promise.all([
      apiClient.getDigest(),
      apiClient.getPatterns(),
      apiClient.getAllInsights(),
    ]);

    setDigest(
      digestResult.ok
        ? { status: "success", data: digestResult.data, error: null }
        : { status: "error", data: null, error: digestResult.error }
    );

    setPatterns(
      patternsResult.ok
        ? { status: "success", data: patternsResult.data, error: null }
        : { status: "error", data: null, error: patternsResult.error }
    );

    setAllInsights(
      allResult.ok
        ? { status: "success", data: allResult.data, error: null }
        : { status: "error", data: null, error: allResult.error }
    );
  }, []);

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchAll();
    }, 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
    };
  }, [fetchAll]);

  return { digest, patterns, allInsights, refetch: fetchAll };
}
