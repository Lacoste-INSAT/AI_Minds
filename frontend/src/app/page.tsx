"use client";
import { useFetch } from "@/lib/hooks";
import { getHealth, getMemoryStats, getIngestionStatus } from "@/lib/api";
import { Brain, FileText, Share2, HardDrive, Activity, TrendingUp } from "lucide-react";

export default function Dashboard() {
  const { data: health } = useFetch(getHealth);
  const { data: stats } = useFetch(getMemoryStats);
  const { data: ingestion } = useFetch(getIngestionStatus);

  const cards = [
    { label: "Documents", value: stats?.total_documents ?? "—", icon: FileText, color: "text-blue-400" },
    { label: "Chunks", value: stats?.total_chunks ?? "—", icon: HardDrive, color: "text-purple-400" },
    { label: "Entities", value: stats?.total_nodes ?? "—", icon: Share2, color: "text-emerald-400" },
    { label: "Relationships", value: stats?.total_edges ?? "—", icon: TrendingUp, color: "text-amber-400" },
    { label: "Files Processed", value: ingestion?.files_processed ?? "—", icon: Activity, color: "text-cyan-400" },
    { label: "System Status", value: health?.status ?? "—", icon: Brain, color: health?.status === "healthy" ? "text-green-400" : "text-amber-400" },
  ];

  const modalities = stats?.modalities ?? {};
  const categories = stats?.categories ?? {};

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-2xl font-bold">Dashboard</h2>
        <p className="text-sm text-muted mt-1">Overview of your personal knowledge base</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-card rounded-xl border border-border p-4 hover:border-accent/30 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <p className="text-2xl font-bold">{typeof value === "number" ? value.toLocaleString() : value}</p>
            <p className="text-xs text-muted mt-1">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold mb-4">Modalities</h3>
          {Object.keys(modalities).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(modalities).map(([mod, count]) => (
                <div key={mod} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{mod}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-32 h-2 bg-background rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full" style={{ width: `${Math.min(100, (count / Math.max(...Object.values(modalities))) * 100)}%` }} />
                    </div>
                    <span className="text-xs text-muted w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted">No data yet. Ingest some files to get started.</p>}
        </div>
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold mb-4">Categories</h3>
          {Object.keys(categories).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(categories).map(([cat, count]) => (
                <div key={cat} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{cat.replace(/_/g, " ")}</span>
                  <span className="text-xs text-muted bg-background px-2 py-0.5 rounded">{count}</span>
                </div>
              ))}
            </div>
          ) : <p className="text-sm text-muted">Categories appear after LLM enrichment.</p>}
        </div>
      </div>

      {health && (
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold mb-4">Services</h3>
          <div className="grid grid-cols-3 gap-4">
            {(["ollama", "qdrant", "sqlite"] as const).map((svc) => {
              const s = health[svc];
              return (
                <div key={svc} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${s.status === "up" ? "bg-green-500" : "bg-red-500"}`} />
                  <div>
                    <p className="text-sm font-medium capitalize">{svc}</p>
                    <p className="text-xs text-muted">{s.status}</p>
                  </div>
                </div>
              );
            })}
          </div>
          {health.disk_free_gb !== null && (
            <p className="text-xs text-muted mt-3">Disk free: {health.disk_free_gb.toFixed(1)} GB</p>
          )}
        </div>
      )}
    </div>
  );
}
