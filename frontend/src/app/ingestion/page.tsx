"use client";
import { useState } from "react";
import { useFetch } from "@/lib/hooks";
import { getIngestionStatus, triggerScan, getSources, updateSources, type SourceConfig } from "@/lib/api";
import { FolderOpen, RefreshCw, Play, Check, AlertTriangle, Clock, FileText, Plus, X, HardDrive } from "lucide-react";

const dirPaths = (dirs: SourceConfig[]) => dirs.map((d) => d.path);

export default function IngestionPage() {
  const { data: status, loading, refetch } = useFetch(getIngestionStatus);
  const { data: sources, refetch: refetchSources } = useFetch(getSources);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [newDir, setNewDir] = useState("");
  const [newExclude, setNewExclude] = useState("");

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const r = await triggerScan();
      setScanResult(`Scan complete — processed ${r.files_processed ?? 0} files`);
      refetch();
    } catch {
      setScanResult("Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const addDir = async () => {
    if (!newDir.trim() || !sources) return;
    try {
      await updateSources({
        watched_directories: [...dirPaths(sources.watched_directories || []), newDir.trim()],
        exclude_patterns: sources.exclude_patterns || [],
      });
      setNewDir("");
      refetchSources();
    } catch {}
  };

  const removeDir = async (dir: string) => {
    if (!sources) return;
    await updateSources({
      watched_directories: dirPaths(sources.watched_directories).filter((d) => d !== dir),
      exclude_patterns: sources.exclude_patterns || [],
    });
    refetchSources();
  };

  const addExclude = async () => {
    if (!newExclude.trim() || !sources) return;
    await updateSources({
      watched_directories: dirPaths(sources.watched_directories || []),
      exclude_patterns: [...(sources.exclude_patterns || []), newExclude.trim()],
    });
    setNewExclude("");
    refetchSources();
  };

  const removeExclude = async (pat: string) => {
    if (!sources) return;
    await updateSources({
      watched_directories: dirPaths(sources.watched_directories || []),
      exclude_patterns: sources.exclude_patterns.filter((p: string) => p !== pat),
    });
    refetchSources();
  };

  const statusIcon = (s: string) => {
    if (s === "completed" || s === "success") return <Check className="w-4 h-4 text-green-400" />;
    if (s === "error" || s === "failed") return <AlertTriangle className="w-4 h-4 text-red-400" />;
    if (s === "processing") return <RefreshCw className="w-4 h-4 text-yellow-400 animate-spin" />;
    return <Clock className="w-4 h-4 text-muted" />;
  };

  return (
    <div className="animate-fade-in space-y-6 max-w-6xl mx-auto w-full relative">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[400px] h-[400px] rounded-full bg-cyan-500/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-60 -right-32 w-[350px] h-[350px] rounded-full bg-accent/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(6,182,212,0.08) 0%, rgba(99,102,241,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-cyan-500/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10 flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400 animate-breathe" />
              <span className="text-[11px] uppercase tracking-[0.2em] text-cyan-400/70 font-medium">Data Pipeline</span>
            </div>
            <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-cyan-200 to-indigo-300 bg-clip-text text-transparent animate-gradient-text">
              Ingestion Pipeline
            </h2>
            <p className="text-sm text-muted/80 mt-1.5">Manage watched directories, trigger scans, and view processing status</p>
          </div>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-2 bg-gradient-to-r from-accent to-cyan-500 hover:from-accent-light hover:to-cyan-400 px-5 py-2.5 rounded-xl font-medium transition-all disabled:opacity-50 shadow-lg shadow-accent/20 hover:shadow-accent/30 hover:translate-y-[-1px]"
          >
            {scanning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {scanning ? "Scanning..." : "Trigger Scan"}
          </button>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
      </div>

      {scanResult && (
        <div className="glass rounded-xl gradient-border p-3 text-sm text-accent-light flex items-center gap-2">
          <Check className="w-4 h-4" /> {scanResult}
        </div>
      )}

      {/* Watched directories */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-cyan-400 to-blue-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2"><FolderOpen className="w-4 h-4 text-cyan-400" /> Watched Directories</h3>
        </div>
        <div className="space-y-2 mb-3">
          {sources?.watched_directories?.length ? sources.watched_directories.map((d) => (
            <div key={d.path} className="flex items-center justify-between bg-white/[0.02] rounded-xl px-4 py-2.5 ring-1 ring-white/[0.06] hover:ring-accent/20 transition-all group">
              <span className="text-sm font-mono">{d.path}</span>
              <button onClick={() => removeDir(d.path)} className="text-red-400/60 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"><X className="w-4 h-4" /></button>
            </div>
          )) : (
            <div className="flex flex-col items-center justify-center py-8 text-center rounded-xl border border-dashed border-white/[0.08]">
              <FolderOpen className="w-8 h-8 text-muted/30 mb-2" />
              <p className="text-sm text-muted">No directories configured</p>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <input value={newDir} onChange={(e) => setNewDir(e.target.value)} placeholder="Add directory path..." className="flex-1 glass ring-1 ring-white/[0.06] focus:ring-accent/40 rounded-lg px-3 py-2 text-sm outline-none transition-all" />
          <button onClick={addDir} className="bg-gradient-to-r from-accent to-cyan-500 hover:from-accent-light hover:to-cyan-400 px-3 py-2 rounded-lg transition-all"><Plus className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Exclusion patterns */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-amber-400 to-orange-500" />
          <h3 className="text-sm font-semibold">Exclusion Patterns</h3>
        </div>
        <div className="space-y-2 mb-3">
          {sources?.exclude_patterns?.length ? sources.exclude_patterns.map((p: string) => (
            <div key={p} className="flex items-center justify-between bg-white/[0.02] rounded-xl px-4 py-2.5 ring-1 ring-white/[0.06] hover:ring-amber-500/20 transition-all group">
              <span className="text-sm font-mono">{p}</span>
              <button onClick={() => removeExclude(p)} className="text-red-400/60 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"><X className="w-4 h-4" /></button>
            </div>
          )) : (
            <div className="flex flex-col items-center justify-center py-8 text-center rounded-xl border border-dashed border-white/[0.08]">
              <p className="text-sm text-muted">No exclusion patterns</p>
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <input value={newExclude} onChange={(e) => setNewExclude(e.target.value)} placeholder="Add pattern (e.g. *.tmp)..." className="flex-1 glass ring-1 ring-white/[0.06] focus:ring-accent/40 rounded-lg px-3 py-2 text-sm outline-none transition-all" />
          <button onClick={addExclude} className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 px-3 py-2 rounded-lg transition-all"><Plus className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Processing history */}
      <div className="glass rounded-2xl gradient-border p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-4 rounded-full bg-gradient-to-b from-accent to-purple-500" />
          <h3 className="text-sm font-semibold flex items-center gap-2"><FileText className="w-4 h-4 text-accent-light" /> Recent Processing</h3>
        </div>
        {loading ? (
          <div className="animate-shimmer rounded-xl p-4 text-sm text-muted">Loading...</div>
        ) : (status as any)?.recent_files?.length ? (
          <div className="space-y-2">
            {(status as any).recent_files.map((f: any, i: number) => (
              <div key={i} className="flex items-center gap-3 bg-white/[0.02] rounded-xl px-4 py-2.5 ring-1 ring-white/[0.04] hover:ring-white/[0.08] transition-all animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
                {statusIcon(f.status)}
                <span className="flex-1 text-sm font-mono truncate">{f.filename || f.path || f.name}</span>
                <span className="text-xs text-muted bg-white/[0.04] px-2 py-0.5 rounded-md">{f.modality}</span>
                <span className="text-xs text-muted font-mono">{f.chunks ?? "?"} chunks</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center rounded-xl border border-dashed border-white/[0.08]">
            <HardDrive className="w-8 h-8 text-muted/30 mb-2" />
            <p className="text-sm text-muted">No files processed yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
