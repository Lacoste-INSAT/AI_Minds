"use client";

import { useMemo, useState } from "react";
import { ErrorAlert } from "@/components/shared/error-alert";
import { useRuntimeIncidents } from "@/hooks/use-runtime-incidents";
import type { RuntimeIncident } from "@/types/contracts";

function toSeverity(
  severity: RuntimeIncident["severity"]
): "error" | "warning" | "info" {
  if (severity === "critical" || severity === "error") {
    return "error";
  }
  if (severity === "warning") {
    return "warning";
  }
  return "info";
}

export function RuntimeIncidentsBanner() {
  const { incidents, loading, error, refetch } = useRuntimeIncidents(15);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const active = useMemo(
    () => incidents.filter((incident) => !dismissed.has(incident.id)),
    [dismissed, incidents]
  );
  const top = active[0];

  if (loading || !top) {
    return null;
  }

  if (error) {
    return (
      <div className="px-6 pt-3">
        <ErrorAlert
          severity="warning"
          title="Incident feed unavailable"
          message={error}
          onRetry={refetch}
        />
      </div>
    );
  }

  return (
    <div className="px-6 pt-3">
      <ErrorAlert
        severity={toSeverity(top.severity)}
        title={`Runtime incident · ${top.subsystem}`}
        message={`${top.operation}: ${top.reason}`}
        onDismiss={() => {
          setDismissed((prev) => new Set(prev).add(top.id));
        }}
      />
    </div>
  );
}

