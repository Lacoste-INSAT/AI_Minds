"use client";
import { useFetch } from "@/lib/hooks";
import { getRuntimePolicy, getRuntimeIncidents } from "@/lib/api";
import { ShieldCheck, AlertTriangle, Server, Clock, Info } from "lucide-react";

export default function RuntimePage() {
  const { data: policy, loading: loadingPolicy } = useFetch(getRuntimePolicy);
  const { data: incidents, loading: loadingInc } = useFetch(getRuntimeIncidents);

  const severityColor: Record<string, string> = {
    critical: "text-red-400 bg-red-400/10",
    high: "text-orange-400 bg-orange-400/10",
    medium: "text-yellow-400 bg-yellow-400/10",
    low: "text-blue-400 bg-blue-400/10",
  };

  return (
    <div className="animate-fade-in space-y-6 max-w-5xl">
      <h2 className="text-2xl font-bold">Runtime &amp; Model Policy</h2>
      <p className="text-sm text-muted -mt-4">Dual-model routing, guardrails, and incident log</p>

      {/* Policy overview */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5 text-accent" /> Active Policy
        </h3>
        {loadingPolicy ? (
          <p className="text-sm text-muted">Loading...</p>
        ) : policy ? (
          <>
          <div className="grid sm:grid-cols-2 gap-4">
            {[
              ["Fail Fast", policy.fail_fast ? "Enabled" : "Disabled"],
              ["Model Fallback", policy.allow_model_fallback ? "Allowed" : "Denied"],
              ["Outage Policy", policy.outage_policy || "—"],
            ].map(([label, val]) => (
              <div key={label as string} className="bg-background rounded-lg px-4 py-3">
                <div className="text-xs text-muted mb-0.5">{label}</div>
                <div className="text-sm font-medium">{String(val)}</div>
              </div>
            ))}
          </div>
          {policy.lane_assignment && Object.keys(policy.lane_assignment).length > 0 && (
            <div className="mt-4">
              <h4 className="text-xs font-semibold text-muted uppercase mb-2">Lane Assignment</h4>
              <div className="grid sm:grid-cols-2 gap-2">
                {Object.entries(policy.lane_assignment).map(([lane, model]) => (
                  <div key={lane} className="flex items-center justify-between bg-background rounded-lg px-4 py-2">
                    <span className="text-sm capitalize">{lane}</span>
                    <span className="text-xs font-mono text-accent">{model}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          </>
        ) : (
          <p className="text-sm text-muted">No policy configured</p>
        )}
      </div>

      {/* Incidents */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-yellow-400" /> Incidents
        </h3>
        {loadingInc ? (
          <p className="text-sm text-muted">Loading...</p>
        ) : incidents?.length ? (
          <div className="space-y-2">
            {incidents.map((inc, i) => (
              <div key={inc.id || i} className="bg-background rounded-lg p-4 border border-border/50 flex items-start gap-3">
                <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${severityColor[inc.severity] || "text-muted"}`}>
                  {inc.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{inc.operation} — {inc.subsystem}</p>
                  <p className="text-xs text-muted mt-1">{inc.reason}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-muted">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{inc.timestamp}</span>
                    <span className={inc.blocked ? "text-red-400" : "text-green-400"}>
                      {inc.blocked ? "Blocked" : "Allowed"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted">
            <Info className="w-4 h-4" /> No incidents recorded
          </div>
        )}
      </div>
    </div>
  );
}
