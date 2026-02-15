"use client";

/**
 * React hook for source configuration (setup wizard).
 * Falls back to mock data when backend is unavailable.
 */

import { useState, useEffect, useCallback } from "react";
import type { SourcesConfigResponse, SourcesConfigUpdate } from "@/types/contracts";
import type { AsyncState } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { API_MODE } from "@/lib/env";
import { MOCK_SOURCES_CONFIG } from "@/mocks/fixtures";

interface UseConfigReturn extends AsyncState<SourcesConfigResponse> {
  refetch: () => void;
  saveConfig: (update: SourcesConfigUpdate) => Promise<boolean>;
  isSaving: boolean;
}

export function useConfig(): UseConfigReturn {
  const [state, setState] = useState<AsyncState<SourcesConfigResponse>>({
    status: "idle",
    data: null,
    error: null,
  });
  const [isSaving, setIsSaving] = useState(false);

  const fetchConfig = useCallback(async () => {
    setState((prev) => ({ ...prev, status: "loading" }));
    const result = await apiClient.getSourcesConfig();

    if (result.ok) {
      setState({ status: "success", data: result.data, error: null });
    } else {
      if (API_MODE === "mock") {
        setState({ status: "success", data: MOCK_SOURCES_CONFIG, error: null });
      } else {
        setState({ status: "error", data: null, error: result.error });
      }
    }
  }, []);

  const saveConfig = useCallback(
    async (update: SourcesConfigUpdate): Promise<boolean> => {
      setIsSaving(true);
      const result = await apiClient.updateSourcesConfig(update);
      setIsSaving(false);

      if (result.ok) {
        setState({ status: "success", data: result.data, error: null });
        return true;
      }
      return false;
    },
    []
  );

  useEffect(() => {
    const bootstrapTimer = window.setTimeout(() => {
      void fetchConfig();
    }, 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
    };
  }, [fetchConfig]);

  return { ...state, refetch: fetchConfig, saveConfig, isSaving };
}
