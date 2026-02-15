"use client";
import { useState, useEffect } from "react";
import { useFetch } from "@/lib/hooks";
import { getSources, updateSources } from "@/lib/api";
import { Settings as SettingsIcon, Save, FolderOpen, Filter, Check, Info } from "lucide-react";

export default function SettingsPage() {
  const { data: sources, loading, refetch } = useFetch(getSources);
  const [dirs, setDirs] = useState<string[]>([]);
  const [excl, setExcl] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [backendUrl, setBackendUrl] = useState("http://127.0.0.1:8000");

  useEffect(() => {
    if (sources) {
      setDirs(sources.watched_directories?.map((d) => d.path) || []);
      setExcl(sources.exclude_patterns || []);
    }
  }, [sources]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateSources({ watched_directories: dirs, exclude_patterns: excl });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      refetch();
    } catch {} finally {
      setSaving(false);
    }
  };

  const updateDir = (i: number, val: string) => {
    const next = [...dirs];
    next[i] = val;
    setDirs(next);
  };

  const updateExcl = (i: number, val: string) => {
    const next = [...excl];
    next[i] = val;
    setExcl(next);
  };

  return (
    <div className="animate-fade-in space-y-6 max-w-3xl relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[400px] h-[400px] rounded-full bg-accent/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-60 -right-32 w-[350px] h-[350px] rounded-full bg-purple-500/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(139,92,246,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-accent/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-accent animate-breathe" />
              <span className="text-[11px] uppercase tracking-[0.2em] text-accent-light/70 font-medium">Configuration</span>
            </div>
            <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-indigo-200 to-purple-300 bg-clip-text text-transparent animate-gradient-text">
              Settings
            </h2>
            <p className="text-sm text-muted/80 mt-1.5">Configure Synapsis behaviour and connections</p>
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-gradient-to-r from-accent to-purple-600 hover:from-accent/90 hover:to-purple-500 px-5 py-2.5 rounded-xl font-medium transition-all disabled:opacity-50 shadow-lg shadow-accent/20"
          >
            {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
          </button>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
      </div>

      {/* Backend connection */}
      <div className="glass rounded-2xl gradient-border p-6 animate-slide-up" style={{ animationDelay: "60ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-accent to-purple-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <SettingsIcon className="w-4 h-4 text-accent-light" /> Backend Connection
          </h3>
        </div>
        <label className="block text-[11px] text-muted uppercase tracking-wider mb-1.5">API Base URL</label>
        <input
          value={backendUrl}
          onChange={(e) => setBackendUrl(e.target.value)}
          className="w-full glass rounded-xl px-4 py-2.5 text-sm font-mono ring-1 ring-white/[0.06] focus:ring-accent/30 focus:outline-none transition-all"
        />
        <p className="text-xs text-muted mt-2">Proxied via Next.js rewrites. Change requires restart.</p>
      </div>

      {/* Watched Directories */}
      <div className="glass rounded-2xl gradient-border p-6 animate-slide-up" style={{ animationDelay: "120ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-cyan-400 to-blue-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-cyan-400" /> Watched Directories
          </h3>
        </div>
        {loading ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Loading...</div>
        ) : (
          <div className="space-y-2">
            {dirs.map((d, i) => (
              <div key={i} className="flex gap-2 animate-slide-up" style={{ animationDelay: `${i * 40}ms` }}>
                <input
                  value={d}
                  onChange={(e) => updateDir(i, e.target.value)}
                  className="flex-1 glass rounded-xl px-4 py-2.5 text-sm font-mono ring-1 ring-white/[0.06] focus:ring-cyan-500/30 focus:outline-none transition-all"
                />
                <button onClick={() => setDirs(dirs.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-300 hover:bg-red-400/10 px-3 rounded-xl transition-all">×</button>
              </div>
            ))}
            <button
              onClick={() => setDirs([...dirs, ""])}
              className="text-sm text-accent-light hover:text-white transition-colors"
            >
              + Add directory
            </button>
          </div>
        )}
      </div>

      {/* Exclusion Patterns */}
      <div className="glass rounded-2xl gradient-border p-6 animate-slide-up" style={{ animationDelay: "180ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-amber-400 to-orange-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Filter className="w-4 h-4 text-amber-400" /> Exclusion Patterns
          </h3>
        </div>
        <div className="space-y-2">
          {excl.map((p, i) => (
            <div key={i} className="flex gap-2 animate-slide-up" style={{ animationDelay: `${i * 40}ms` }}>
              <input
                value={p}
                onChange={(e) => updateExcl(i, e.target.value)}
                className="flex-1 glass rounded-xl px-4 py-2.5 text-sm font-mono ring-1 ring-white/[0.06] focus:ring-amber-500/30 focus:outline-none transition-all"
              />
              <button onClick={() => setExcl(excl.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-300 hover:bg-red-400/10 px-3 rounded-xl transition-all">×</button>
            </div>
          ))}
          <button
            onClick={() => setExcl([...excl, ""])}
            className="text-sm text-accent-light hover:text-white transition-colors"
          >
            + Add pattern
          </button>
        </div>
      </div>

      {/* About */}
      <div className="glass rounded-2xl gradient-border p-6 animate-slide-up" style={{ animationDelay: "240ms" }}>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-emerald-400 to-green-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Info className="w-4 h-4 text-emerald-400" /> About Synapsis
          </h3>
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          {[
            ["Version", "1.0.0-alpha"],
            ["Type", "Air-gapped personal knowledge AI"],
            ["Models", "Ollama (phi4-mini / qwen2.5)"],
            ["Vector DB", "Qdrant (384-dim cosine)"],
          ].map(([label, value]) => (
            <div key={label} className="bg-white/[0.02] rounded-xl px-4 py-3 ring-1 ring-white/[0.06]">
              <div className="text-[11px] text-muted uppercase tracking-wider mb-0.5">{label}</div>
              <div className="text-sm font-medium">{value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
