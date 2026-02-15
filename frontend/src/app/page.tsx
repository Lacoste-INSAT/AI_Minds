"use client";
import { useFetch } from "@/lib/hooks";
import { getHealth, getMemoryStats, getIngestionStatus } from "@/lib/api";
import {
  Brain, FileText, Share2, HardDrive, Activity, TrendingUp,
  Zap, Database, Cpu,
} from "lucide-react";

export default function Dashboard() {
  const { data: health } = useFetch(getHealth);
  const { data: stats } = useFetch(getMemoryStats);
  const { data: ingestion } = useFetch(getIngestionStatus);

  const cards = [
    { label: "Documents", value: stats?.total_documents ?? "—", icon: FileText, color: "text-blue-400", gradient: "stat-blue", ring: "ring-blue-500/20" },
    { label: "Chunks", value: stats?.total_chunks ?? "—", icon: HardDrive, color: "text-purple-400", gradient: "stat-purple", ring: "ring-purple-500/20" },
    { label: "Entities", value: stats?.total_nodes ?? "—", icon: Share2, color: "text-emerald-400", gradient: "stat-emerald", ring: "ring-emerald-500/20" },
    { label: "Relationships", value: stats?.total_edges ?? "—", icon: TrendingUp, color: "text-amber-400", gradient: "stat-amber", ring: "ring-amber-500/20" },
    { label: "Files Processed", value: ingestion?.files_processed ?? "—", icon: Activity, color: "text-cyan-400", gradient: "stat-cyan", ring: "ring-cyan-500/20" },
    { label: "System Status", value: health?.status ?? "—", icon: Brain, color: health?.status === "healthy" ? "text-green-400" : "text-amber-400", gradient: health?.status === "healthy" ? "stat-green" : "stat-amber", ring: health?.status === "healthy" ? "ring-green-500/20" : "ring-amber-500/20" },
  ];

  const modalities = stats?.modalities ?? {};
  const categories = stats?.categories ?? {};
  const entityTypes = stats?.entity_types ?? {};

  const svcIcon = { ollama: Cpu, qdrant: Database, sqlite: HardDrive } as const;

  return (
    <div className="space-y-8 animate-fade-in relative">
      {/* ── Background mesh blobs ── */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[500px] h-[500px] rounded-full bg-accent/[0.04] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-40 -right-32 w-[400px] h-[400px] rounded-full bg-purple-500/[0.03] blur-3xl animate-float-delay" />

      {/* ── Hero header ── */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-8 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(139,92,246,0.06) 30%, rgba(6,182,212,0.04) 60%, rgba(17,24,39,0.95) 100%)" }}>
        {/* Animated decorative elements */}
        <div className="absolute top-4 right-8 w-20 h-20 pointer-events-none">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-accent/40 animate-orbit" />
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-400/30 animate-orbit-reverse" />
          </div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-accent/10 animate-breathe" />
          </div>
        </div>

        {/* Scan line */}
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-accent/[0.04] to-transparent animate-scanline pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-accent animate-breathe" />
            <span className="text-[11px] uppercase tracking-[0.2em] text-accent-light/70 font-medium">Command Center</span>
          </div>
          <h2 className="text-4xl font-extrabold bg-gradient-to-r from-white via-indigo-300 via-purple-300 to-cyan-300 bg-clip-text text-transparent animate-gradient-text leading-tight">
            Synapsis Dashboard
          </h2>
          <p className="text-sm text-muted/80 mt-2 max-w-lg">Your personal knowledge base, real-time system pulse, and ingestion analytics — all in one view.</p>

          <div className="flex items-center gap-4 mt-5">
            <div className="flex items-center gap-2 text-xs text-muted bg-white/[0.03] px-3 py-1.5 rounded-lg ring-1 ring-white/[0.06]">
              <Zap className="w-3.5 h-3.5 text-accent-light animate-pulse-slow" />
              <span>{health?.status === "healthy" ? "All systems operational" : "Checking services…"}</span>
            </div>
            {stats && (
              <div className="flex items-center gap-2 text-xs text-muted bg-white/[0.03] px-3 py-1.5 rounded-lg ring-1 ring-white/[0.06]">
                <Brain className="w-3.5 h-3.5 text-purple-400" />
                <span>{(stats.total_documents ?? 0).toLocaleString()} docs indexed</span>
              </div>
            )}
          </div>
        </div>

        {/* decorative bottom gradient line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
      </div>

      {/* ── Stat cards — asymmetric grid ── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map(({ label, value, icon: Icon, color, gradient, ring }, i) => (
          <div
            key={label}
            className={`${gradient} rounded-2xl ring-1 ${ring} p-5 hover:ring-accent/40 transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg hover:shadow-accent/5 animate-slide-up gradient-border`}
            style={{ animationDelay: `${i * 80}ms` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="w-9 h-9 rounded-xl bg-white/[0.05] flex items-center justify-center">
                <Icon className={`w-[18px] h-[18px] ${color}`} />
              </div>
            </div>
            <p className="text-3xl font-bold tracking-tight">
              {typeof value === "number" ? value.toLocaleString() : value}
            </p>
            <p className="text-[11px] text-muted mt-1.5 uppercase tracking-wider">{label}</p>
          </div>
        ))}
      </div>

      {/* ── Middle row — 7/5 split ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Modalities — wider */}
        <div className="lg:col-span-7 glass rounded-2xl gradient-border p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-accent to-purple-500" />
            <h3 className="text-sm font-semibold">Modalities</h3>
          </div>
          {Object.keys(modalities).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(modalities).map(([mod, count]) => {
                const pct = Math.min(100, (count / Math.max(...Object.values(modalities))) * 100);
                return (
                  <div key={mod}>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-sm capitalize font-medium">{mod}</span>
                      <span className="text-xs text-muted tabular-nums">{count}</span>
                    </div>
                    <div className="w-full h-2 bg-white/[0.04] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full progress-gradient transition-all duration-700"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
              <FileText className="w-8 h-8 text-muted/40 mb-3" />
              <p className="text-sm text-muted">No data yet</p>
              <p className="text-xs text-muted/60 mt-1">Ingest some files to get started</p>
            </div>
          )}
        </div>

        {/* Categories — narrower */}
        <div className="lg:col-span-5 glass rounded-2xl gradient-border p-6">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-amber-400 to-orange-500" />
            <h3 className="text-sm font-semibold">Categories</h3>
          </div>
          {Object.keys(categories).length > 0 ? (
            <div className="space-y-2.5">
              {Object.entries(categories).map(([cat, count]) => (
                <div
                  key={cat}
                  className="flex items-center justify-between py-2 px-3 rounded-lg bg-white/[0.02] hover:bg-white/[0.05] transition-colors"
                >
                  <span className="text-sm capitalize">{cat.replace(/_/g, " ")}</span>
                  <span className="text-xs font-mono text-muted bg-white/[0.06] px-2.5 py-1 rounded-md">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
              <Share2 className="w-8 h-8 text-muted/40 mb-3" />
              <p className="text-sm text-muted">No categories yet</p>
              <p className="text-xs text-muted/60 mt-1">Appear after LLM enrichment</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom row — Services + Entity Types ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Services */}
        {health && (
          <div className="lg:col-span-5 glass rounded-2xl gradient-border p-6">
            <div className="flex items-center gap-2 mb-5">
              <div className="w-1 h-4 rounded-full bg-gradient-to-b from-green-400 to-emerald-600" />
              <h3 className="text-sm font-semibold">Services</h3>
            </div>
            <div className="space-y-3">
              {(["ollama", "qdrant", "sqlite"] as const).map((svc) => {
                const s = health[svc];
                const SvcIcon = svcIcon[svc];
                const isUp = s.status === "up";
                return (
                  <div
                    key={svc}
                    className={`flex items-center gap-4 p-3 rounded-xl transition-colors ${
                      isUp ? "bg-green-500/[0.06]" : "bg-red-500/[0.06]"
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      isUp ? "bg-green-500/10" : "bg-red-500/10"
                    }`}>
                      <SvcIcon className={`w-4 h-4 ${isUp ? "text-green-400" : "text-red-400"}`} />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium capitalize">{svc}</p>
                      <p className="text-[11px] text-muted">{isUp ? "Running" : "Down"}</p>
                    </div>
                    <div className={`w-2.5 h-2.5 rounded-full ${
                      isUp ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" : "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]"
                    }`} />
                  </div>
                );
              })}
            </div>
            {health.disk_free_gb !== null && (
              <div className="mt-4 pt-3 border-t border-white/[0.06]">
                <div className="flex items-center justify-between text-xs text-muted">
                  <span>Disk free</span>
                  <span className="font-mono">{health.disk_free_gb.toFixed(1)} GB</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Entity Types */}
        <div className={`${health ? "lg:col-span-7" : "lg:col-span-12"} glass rounded-2xl gradient-border p-6`}>
          <div className="flex items-center gap-2 mb-5">
            <div className="w-1 h-4 rounded-full bg-gradient-to-b from-cyan-400 to-blue-500" />
            <h3 className="text-sm font-semibold">Entity Types</h3>
          </div>
          {Object.keys(entityTypes).length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {Object.entries(entityTypes).map(([type, count]) => (
                <div
                  key={type}
                  className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-white/[0.03] ring-1 ring-white/[0.06] hover:ring-accent/20 transition-all text-sm"
                >
                  <span className="capitalize">{type.replace(/_/g, " ")}</span>
                  <span className="text-[10px] font-mono text-accent-light bg-accent/10 px-1.5 py-0.5 rounded-md">{count}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-center rounded-xl border border-dashed border-white/[0.08]">
              <Brain className="w-8 h-8 text-muted/40 mb-3" />
              <p className="text-sm text-muted">No entities extracted yet</p>
              <p className="text-xs text-muted/60 mt-1">Entities will appear after knowledge ingestion</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
