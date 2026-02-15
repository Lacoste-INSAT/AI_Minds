"use client";
import { useFetch } from "@/lib/hooks";
import { getRuntimePolicy, getRuntimeIncidents } from "@/lib/api";
import { ShieldCheck, AlertTriangle, Server, Clock, Info } from "lucide-react";

export default function RuntimePage() {
  const { data: policy, loading: loadingPolicy } = useFetch(getRuntimePolicy);
  const { data: incidents, loading: loadingInc } = useFetch(getRuntimeIncidents);

  const severityColor: Record<string, string> = {
    critical: "text-red-400 bg-red-400/10 ring-red-400/20",
    high: "text-orange-400 bg-orange-400/10 ring-orange-400/20",
    medium: "text-yellow-400 bg-yellow-400/10 ring-yellow-400/20",
    low: "text-blue-400 bg-blue-400/10 ring-blue-400/20",
  };

  return (
    <div className="animate-fade-in space-y-6 max-w-6xl mx-auto w-full relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[400px] h-[400px] rounded-full bg-green-500/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-60 -right-32 w-[350px] h-[350px] rounded-full bg-accent/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(34,197,94,0.08) 0%, rgba(99,102,241,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-green-500/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-breathe" />
            <span className="text-[11px] uppercase tracking-[0.2em] text-green-400/70 font-medium">Model Control</span>
          </div>
          <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-green-200 to-emerald-300 bg-clip-text text-transparent animate-gradient-text">
            Runtime &amp; Policy
          </h2>
          <p className="text-sm text-muted/80 mt-1.5">Dual-model routing, guardrails, and incident log</p>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-green-500/30 to-transparent" />
      </div>

      {/* Policy overview */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-green-400 to-emerald-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Server className="w-4 h-4 text-green-400" /> Active Policy
          </h3>
        </div>
        {loadingPolicy ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Loading...</div>
        ) : policy ? (
          <>
          <div className="grid sm:grid-cols-2 gap-3">
            {[
              ["Fail Fast", policy.fail_fast ? "Enabled" : "Disabled"],
              ["Model Fallback", policy.allow_model_fallback ? "Allowed" : "Denied"],
              ["Outage Policy", policy.outage_policy || "—"],
            ].map(([label, val]) => (
              <div key={label as string} className="bg-white/[0.02] rounded-xl px-4 py-3 ring-1 ring-white/[0.06] hover:ring-green-500/20 transition-all">
                <div className="text-[11px] text-muted mb-0.5 uppercase tracking-wider">{label}</div>
                <div className="text-sm font-medium">{String(val)}</div>
              </div>
            ))}
          </div>
          {policy.lane_assignment && Object.keys(policy.lane_assignment).length > 0 && (
            <div className="mt-5">
              <h4 className="text-[11px] font-semibold text-muted uppercase tracking-wider mb-3">Lane Assignment</h4>
              <div className="grid sm:grid-cols-2 gap-2">
                {Object.entries(policy.lane_assignment).map(([lane, model]) => (
                  <div key={lane} className="flex items-center justify-between bg-white/[0.02] rounded-xl px-4 py-2.5 ring-1 ring-white/[0.06] hover:ring-accent/20 transition-all">
                    <span className="text-sm capitalize">{lane}</span>
                    <span className="text-xs font-mono text-accent-light bg-accent/10 px-2 py-0.5 rounded-md">{model}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <Server className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">No policy configured</p>
          </div>
        )}
      </div>

      {/* Incidents */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-yellow-400 to-orange-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-400" /> Incidents
          </h3>
        </div>
        {loadingInc ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Loading...</div>
        ) : incidents?.length ? (
          <div className="space-y-2">
            {incidents.map((inc, i) => (
              <div key={inc.id || i} className="bg-white/[0.02] rounded-xl p-4 ring-1 ring-white/[0.04] hover:ring-white/[0.1] transition-all flex items-start gap-3 animate-slide-up" style={{ animationDelay: `${i * 60}ms` }}>
                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ring-1 ${severityColor[inc.severity] || "text-muted"}`}>
                  {inc.severity}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{inc.operation} — {inc.subsystem}</p>
                  <p className="text-xs text-muted mt-1">{inc.reason}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-muted">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{inc.timestamp}</span>
                    <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium ${inc.blocked ? "text-red-400 bg-red-400/10" : "text-green-400 bg-green-400/10"}`}>
                      {inc.blocked ? "Blocked" : "Allowed"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
            <Info className="w-8 h-8 text-muted/30 mb-3" />
            <p className="text-sm text-muted">No incidents recorded</p>
          </div>
        )}
      </div>
    </div>
  );
}
