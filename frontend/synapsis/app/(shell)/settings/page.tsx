"use client";

/**
 * Settings page — Manage watched directories, exclusion patterns, and watcher status.
 * Provides day-to-day directory management (vs. the one-time setup wizard).
 */

import { useState, useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  FolderOpen,
  Plus,
  Trash2,
  Save,
  ScanSearch,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Loader2,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useConfig } from "@/hooks/use-config";
import { useIngestionStatus } from "@/hooks/use-ingestion-status";
import { cn } from "@/lib/utils";

function looksLikePath(path: string): boolean {
  return path.startsWith("/") || /^[A-Za-z]:\\/.test(path) || path.startsWith("~");
}

export default function SettingsPage() {
  const router = useRouter();
  const { data: config, status: configStatus, saveConfig, isSaving, refetch: refetchConfig } = useConfig();
  const { data: ingestion, triggerScan } = useIngestionStatus();

  // Local editable state
  const [directories, setDirectories] = useState<string[]>([]);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [newDir, setNewDir] = useState("");
  const [newPattern, setNewPattern] = useState("");
  const [dirError, setDirError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const initializedRef = useRef(false);

  // Seed local state from fetched config
  useEffect(() => {
    if (!config || initializedRef.current) return;
    initializedRef.current = true;
    setDirectories(config.watched_directories.map((d) => d.path));
    setExclusions(config.exclude_patterns);
  }, [config]);

  // Track unsaved changes
  useEffect(() => {
    if (!config) return;
    const origDirs = config.watched_directories.map((d) => d.path);
    const origExcl = config.exclude_patterns;
    const dirsChanged = JSON.stringify(directories) !== JSON.stringify(origDirs);
    const exclChanged = JSON.stringify(exclusions) !== JSON.stringify(origExcl);
    setHasUnsavedChanges(dirsChanged || exclChanged);
  }, [directories, exclusions, config]);

  // ── Directory actions ──

  const addDirectory = useCallback(() => {
    const trimmed = newDir.trim();
    if (!trimmed) return;
    if (!looksLikePath(trimmed)) {
      setDirError("Please enter a valid absolute path (e.g. C:\\Users\\... or ~/Documents).");
      return;
    }
    if (directories.includes(trimmed)) {
      setDirError("This directory is already added.");
      return;
    }
    if (directories.length >= 10) {
      setDirError("Maximum of 10 directories allowed.");
      return;
    }
    setDirError(null);
    setDirectories((prev) => [...prev, trimmed]);
    setNewDir("");
  }, [newDir, directories]);

  const removeDirectory = useCallback((path: string) => {
    setDirectories((prev) => prev.filter((d) => d !== path));
    setDirError(null);
  }, []);

  // ── Exclusion actions ──

  const addPattern = useCallback(() => {
    const trimmed = newPattern.trim();
    if (!trimmed || exclusions.includes(trimmed)) return;
    setExclusions((prev) => [...prev, trimmed]);
    setNewPattern("");
  }, [newPattern, exclusions]);

  const removePattern = useCallback((pattern: string) => {
    setExclusions((prev) => prev.filter((p) => p !== pattern));
  }, []);

  // ── Save ──

  const handleSave = useCallback(async () => {
    setSaveSuccess(false);
    const success = await saveConfig({
      watched_directories: directories,
      exclude_patterns: exclusions,
    });
    if (success) {
      setSaveSuccess(true);
      setHasUnsavedChanges(false);
      initializedRef.current = false; // Allow re-sync from server
      refetchConfig();
      setTimeout(() => setSaveSuccess(false), 3000);
    }
  }, [directories, exclusions, saveConfig, refetchConfig]);

  // ── Scan ──

  const handleScan = useCallback(async () => {
    setIsScanning(true);
    await triggerScan();
    setIsScanning(false);
  }, [triggerScan]);

  if (configStatus === "loading") {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const isWatching = ingestion?.is_watching ?? false;

  return (
    <ScrollArea className="h-full">
      <div className="mx-auto max-w-3xl space-y-6 p-6">
        {/* ── Header ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
            <p className="text-sm text-muted-foreground">
              Manage watched directories and file watcher configuration.
            </p>
          </div>
          <Badge
            variant={isWatching ? "default" : "secondary"}
            className={cn(
              "gap-1.5 px-3 py-1",
              isWatching && "bg-green-600 text-white hover:bg-green-700"
            )}
          >
            {isWatching ? (
              <Eye className="h-3.5 w-3.5" />
            ) : (
              <EyeOff className="h-3.5 w-3.5" />
            )}
            {isWatching ? "Watcher Active" : "Watcher Inactive"}
          </Badge>
        </div>

        {/* ── Watcher Status Card ── */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Ingestion Status</CardTitle>
            <CardDescription>
              Real-time file processing information.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Processed</p>
                <p className="text-2xl font-bold">{ingestion?.files_processed ?? 0}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Queue</p>
                <p className="text-2xl font-bold">{ingestion?.queue_depth ?? 0}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold text-destructive">
                  {ingestion?.files_failed ?? 0}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Skipped</p>
                <p className="text-2xl font-bold">{ingestion?.files_skipped ?? 0}</p>
              </div>
            </div>
            {ingestion?.last_scan_time && (
              <p className="mt-3 text-xs text-muted-foreground">
                Last scan: {new Date(ingestion.last_scan_time).toLocaleString()}
              </p>
            )}
          </CardContent>
        </Card>

        {/* ── Watched Directories ── */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Watched Directories</CardTitle>
            <CardDescription>
              Directories Synapsis monitors for new documents. Changes are applied after saving.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Directory list */}
            {directories.length > 0 ? (
              <div className="space-y-2">
                {directories.map((dir) => (
                  <div
                    key={dir}
                    className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FolderOpen className="h-4 w-4 shrink-0 text-primary" />
                      <span className="truncate text-sm font-mono">{dir}</span>
                    </div>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
                          onClick={() => removeDirectory(dir)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Remove directory</TooltipContent>
                    </Tooltip>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-md border border-dashed p-6 text-center">
                <FolderOpen className="mx-auto h-8 w-8 text-muted-foreground/50" />
                <p className="mt-2 text-sm text-muted-foreground">
                  No directories configured.
                </p>
                <p className="text-xs text-muted-foreground">
                  Add a directory below, or{" "}
                  <button
                    type="button"
                    className="text-primary underline-offset-2 hover:underline"
                    onClick={() => router.push("/setup")}
                  >
                    run the setup wizard
                  </button>
                  .
                </p>
              </div>
            )}

            {/* Add directory */}
            <div className="flex gap-2">
              <Input
                placeholder="Enter directory path (e.g. C:\Users\you\Documents)"
                value={newDir}
                onChange={(e) => {
                  setNewDir(e.target.value);
                  setDirError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addDirectory();
                  }
                }}
                className="h-9 flex-1 text-sm font-mono"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={addDirectory}
                disabled={!newDir.trim()}
                className="h-9 gap-1.5"
              >
                <Plus className="h-4 w-4" />
                Add
              </Button>
            </div>

            {dirError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-sm">{dirError}</AlertDescription>
              </Alert>
            )}

            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">
                {directories.length} / 10 directories
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* ── Exclusion Patterns ── */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Exclusion Patterns</CardTitle>
            <CardDescription>
              Glob patterns for files or folders to skip during ingestion.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="e.g. *.log, node_modules/**, .git/**"
                value={newPattern}
                onChange={(e) => setNewPattern(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addPattern();
                  }
                }}
                className="h-9 flex-1 text-sm font-mono"
              />
              <Button
                variant="secondary"
                size="sm"
                onClick={addPattern}
                disabled={!newPattern.trim()}
                className="h-9"
              >
                Add
              </Button>
            </div>

            {exclusions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {exclusions.map((pattern) => (
                  <Badge
                    key={pattern}
                    variant="secondary"
                    className="gap-1 font-mono text-xs"
                  >
                    {pattern}
                    <button
                      type="button"
                      onClick={() => removePattern(pattern)}
                      className="ml-0.5 rounded-sm hover:text-destructive focus:outline-none focus:ring-1 focus:ring-ring"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Action Bar ── */}
        <div className="flex items-center justify-between rounded-lg border bg-card p-4">
          <div className="flex items-center gap-3">
            <Button
              onClick={handleSave}
              disabled={isSaving || (!hasUnsavedChanges && directories.length > 0)}
              className="gap-1.5"
            >
              {isSaving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              {isSaving ? "Saving..." : "Save & Restart Watcher"}
            </Button>

            <Button
              variant="outline"
              onClick={handleScan}
              disabled={isScanning || directories.length === 0}
              className="gap-1.5"
            >
              {isScanning ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ScanSearch className="h-4 w-4" />
              )}
              {isScanning ? "Scanning..." : "Scan Now"}
            </Button>
          </div>

          {saveSuccess && (
            <div className="flex items-center gap-1.5 text-sm text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              Configuration saved! Watcher restarted.
            </div>
          )}

          {hasUnsavedChanges && !saveSuccess && (
            <Badge variant="outline" className="text-amber-600 border-amber-300">
              Unsaved changes
            </Badge>
          )}
        </div>
      </div>
    </ScrollArea>
  );
}
