"use client";
import { useState } from "react";
import { useFetch } from "@/lib/hooks";
import { getIngestionStatus, triggerScan, getSources, updateSources, type SourceConfig } from "@/lib/api";
import { FolderOpen, RefreshCw, Play, Check, AlertTriangle, Clock, FileText, Plus, X } from "lucide-react";

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
    <div className="animate-fade-in space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Ingestion Pipeline</h2>
          <p className="text-sm text-muted mt-1">Manage watched directories, trigger scans, and view processing status</p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 bg-accent hover:bg-accent/80 px-4 py-2 rounded-lg font-medium transition disabled:opacity-50"
        >
          {scanning ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {scanning ? "Scanning..." : "Trigger Scan"}
        </button>
      </div>

      {scanResult && (
        <div className="bg-card border border-border rounded-lg p-3 text-sm text-accent">{scanResult}</div>
      )}

      {/* Watched directories */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2"><FolderOpen className="w-5 h-5 text-accent" /> Watched Directories</h3>
        <div className="space-y-2 mb-3">
          {sources?.watched_directories?.length ? sources.watched_directories.map((d) => (
            <div key={d.path} className="flex items-center justify-between bg-background rounded-lg px-3 py-2">
              <span className="text-sm font-mono">{d.path}</span>
              <button onClick={() => removeDir(d.path)} className="text-red-400 hover:text-red-300"><X className="w-4 h-4" /></button>
            </div>
          )) : (
            <p className="text-sm text-muted">No directories configured</p>
          )}
        </div>
        <div className="flex gap-2">
          <input value={newDir} onChange={(e) => setNewDir(e.target.value)} placeholder="Add directory path..." className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm" />
          <button onClick={addDir} className="bg-accent hover:bg-accent/80 px-3 py-2 rounded-lg"><Plus className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Exclusion patterns */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3">Exclusion Patterns</h3>
        <div className="space-y-2 mb-3">
          {sources?.exclude_patterns?.length ? sources.exclude_patterns.map((p: string) => (
            <div key={p} className="flex items-center justify-between bg-background rounded-lg px-3 py-2">
              <span className="text-sm font-mono">{p}</span>
              <button onClick={() => removeExclude(p)} className="text-red-400 hover:text-red-300"><X className="w-4 h-4" /></button>
            </div>
          )) : (
            <p className="text-sm text-muted">No exclusion patterns</p>
          )}
        </div>
        <div className="flex gap-2">
          <input value={newExclude} onChange={(e) => setNewExclude(e.target.value)} placeholder="Add pattern (e.g. *.tmp)..." className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm" />
          <button onClick={addExclude} className="bg-accent hover:bg-accent/80 px-3 py-2 rounded-lg"><Plus className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Processing history */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2"><FileText className="w-5 h-5 text-accent" /> Recent Processing</h3>
        {loading ? (
          <p className="text-sm text-muted">Loading...</p>
        ) : (status as any)?.recent_files?.length ? (
          <div className="space-y-2">
            {(status as any).recent_files.map((f: any, i: number) => (
              <div key={i} className="flex items-center gap-3 bg-background rounded-lg px-3 py-2">
                {statusIcon(f.status)}
                <span className="flex-1 text-sm font-mono truncate">{f.filename || f.path || f.name}</span>
                <span className="text-xs text-muted">{f.modality}</span>
                <span className="text-xs text-muted">{f.chunks ?? "?"} chunks</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">No files processed yet</p>
        )}
      </div>
    </div>
  );
}
