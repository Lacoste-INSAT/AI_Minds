"use client";

/**
 * useInsights — Hook for consuming insights endpoints.
 * Fetches digest, patterns, or all insights with mock fallback.
 *
 * Source: FE-056 specification, BACKEND_CONTRACT_ALIGNMENT.md
 */

import { useState, useEffect, useCallback } from "react";
import type { InsightItem, DigestResponse, PatternsResponse } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { MOCK_DIGEST, MOCK_PATTERNS, MOCK_INSIGHTS } from "@/mocks/fixtures";

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

    setDigest({
      status: "success",
      data: digestResult.ok ? digestResult.data : MOCK_DIGEST,
      error: null,
    });

    setPatterns({
      status: "success",
      data: patternsResult.ok ? patternsResult.data : MOCK_PATTERNS,
      error: null,
    });

    setAllInsights({
      status: "success",
      data: allResult.ok ? allResult.data : MOCK_INSIGHTS,
      error: null,
    });
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
