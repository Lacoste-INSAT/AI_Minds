"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { connectIngestionStream } from "@/lib/api/ws-client";
import type { RuntimeIncident } from "@/types/contracts";
import { RuntimeIncidentSchema } from "@/lib/api/schemas";

interface UseRuntimeIncidentsResult {
  incidents: RuntimeIncident[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useRuntimeIncidents(limit = 20): UseRuntimeIncidentsResult {
  const [incidents, setIncidents] = useState<RuntimeIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async () => {
    const result = await apiClient.getRuntimeIncidents(limit);
    if (result.ok) {
      setIncidents(result.data.slice().reverse());
      setError(null);
    } else {
      setError(result.error);
    }
    setLoading(false);
  }, [limit]);

  useEffect(() => {
    void fetchIncidents();
    const interval = window.setInterval(() => {
      void fetchIncidents();
    }, 10_000);
    return () => window.clearInterval(interval);
  }, [fetchIncidents]);

  useEffect(() => {
    const cleanup = connectIngestionStream({
      onMessage: (message) => {
        if (message.event !== "incident") {
          return;
        }
        const parsed = RuntimeIncidentSchema.safeParse(message.payload);
        if (!parsed.success) {
          return;
        }
        setIncidents((prev) => [parsed.data as RuntimeIncident, ...prev].slice(0, limit));
      },
      onError: () => {},
      onClose: () => {},
    });
    return cleanup;
  }, [limit]);

  return { incidents, loading, error, refetch: fetchIncidents };
}
