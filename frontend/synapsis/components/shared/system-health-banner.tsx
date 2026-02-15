"use client";

import { useMemo } from "react";
import { ErrorAlert } from "@/components/shared/error-alert";
import { useHealth } from "@/hooks/use-health";

function listDownServices(health: ReturnType<typeof useHealth>["data"]): string[] {
  if (!health) {
    return [];
  }

  const entries: Array<[string, typeof health.ollama]> = [
    ["Ollama", health.ollama],
    ["Qdrant", health.qdrant],
    ["SQLite", health.sqlite],
  ];

  return entries
    .filter(([, service]) => service.status === "down")
    .map(([name]) => name);
}

export function SystemHealthBanner() {
  const { data, error, refetch } = useHealth();

  const banner = useMemo(() => {
    if (!data && !error) {
      return null;
    }

    if (!data && error) {
      return {
        severity: "error" as const,
        title: "Health service unreachable",
        message: error,
      };
    }

    const health = data as NonNullable<typeof data>;
    const downServices = listDownServices(health);
    const serviceSummary =
      downServices.length > 0
        ? `Affected services: ${downServices.join(", ")}.`
        : "Service details are temporarily unavailable.";

    if (health.status === "healthy" && !error) {
      return null;
    }

    if (health.status === "degraded") {
      return {
        severity: "warning" as const,
        title: "System degraded",
        message: error
          ? `Health service is unreachable. ${serviceSummary}`
          : `Some services are degraded. ${serviceSummary}`,
      };
    }

    return {
      severity: "error" as const,
      title: "System unhealthy",
      message: `Critical services are down. ${serviceSummary}`,
    };
  }, [data, error]);

  if (!banner) {
    return null;
  }

  return (
    <ErrorAlert
      severity={banner.severity}
      title={banner.title}
      message={banner.message}
      onRetry={refetch}
      className="rounded-none border-x-0 border-t-0"
    />
  );
}
