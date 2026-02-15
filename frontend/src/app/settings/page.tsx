"use client";
import { useState, useEffect } from "react";
import { useFetch } from "@/lib/hooks";
import { getSources, updateSources } from "@/lib/api";
import { Settings as SettingsIcon, Save, FolderOpen, Filter, Check } from "lucide-react";

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
    <div className="animate-fade-in space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Settings</h2>
          <p className="text-sm text-muted mt-1">Configure Synapsis behaviour and connections</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 bg-accent hover:bg-accent/80 px-4 py-2 rounded-lg font-medium transition disabled:opacity-50"
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saving ? "Saving..." : saved ? "Saved!" : "Save Changes"}
        </button>
      </div>

      {/* Backend connection */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-accent" /> Backend Connection
        </h3>
        <label className="block text-xs text-muted mb-1">API Base URL</label>
        <input
          value={backendUrl}
          onChange={(e) => setBackendUrl(e.target.value)}
          className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono"
        />
        <p className="text-xs text-muted mt-1">Proxied via Next.js rewrites. Change requires restart.</p>
      </div>

      {/* Watched Directories */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-accent" /> Watched Directories
        </h3>
        {loading ? (
          <p className="text-sm text-muted">Loading...</p>
        ) : (
          <div className="space-y-2">
            {dirs.map((d, i) => (
              <div key={i} className="flex gap-2">
                <input
                  value={d}
                  onChange={(e) => updateDir(i, e.target.value)}
                  className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono"
                />
                <button onClick={() => setDirs(dirs.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-300 px-2">×</button>
              </div>
            ))}
            <button
              onClick={() => setDirs([...dirs, ""])}
              className="text-sm text-accent hover:underline"
            >
              + Add directory
            </button>
          </div>
        )}
      </div>

      {/* Exclusion Patterns */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Filter className="w-5 h-5 text-accent" /> Exclusion Patterns
        </h3>
        <div className="space-y-2">
          {excl.map((p, i) => (
            <div key={i} className="flex gap-2">
              <input
                value={p}
                onChange={(e) => updateExcl(i, e.target.value)}
                className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm font-mono"
              />
              <button onClick={() => setExcl(excl.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-300 px-2">×</button>
            </div>
          ))}
          <button
            onClick={() => setExcl([...excl, ""])}
            className="text-sm text-accent hover:underline"
          >
            + Add pattern
          </button>
        </div>
      </div>

      {/* About */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-2">About Synapsis</h3>
        <div className="text-sm text-muted space-y-1">
          <p>Version: 1.0.0-alpha</p>
          <p>Air-gapped personal knowledge AI</p>
          <p>Models: Ollama (phi4-mini / qwen2.5)</p>
          <p>Vector DB: Qdrant (384-dim cosine)</p>
        </div>
      </div>
    </div>
  );
}
