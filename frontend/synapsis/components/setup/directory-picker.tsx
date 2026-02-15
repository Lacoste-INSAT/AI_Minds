"use client";

/**
 * DirectoryPicker — Local directory selection for knowledge sources.
 * Uses File System Access API (showDirectoryPicker) with fallback text input.
 * No upload UI — only directory path selection.
 *
 * Source: ARCHITECTURE.md §Setup, DESIGN_SYSTEM.md
 */

import { useState, useCallback } from "react";
import { FolderOpen, Plus, Trash2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Alert,
  AlertDescription,
} from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

// ── Check API availability ──

type DirectoryPickerWindow = Window & {
  showDirectoryPicker?: (options?: { mode?: "read" | "readwrite" }) => Promise<FileSystemDirectoryHandle>;
};

function hasFileSystemAccess(): boolean {
  const pickerWindow = window as DirectoryPickerWindow;
  return typeof window !== "undefined" && typeof pickerWindow.showDirectoryPicker === "function";
}

function looksLikePath(path: string): boolean {
  const unixLike = path.startsWith("/");
  const windowsLike = /^[A-Za-z]:\\/.test(path);
  return unixLike || windowsLike;
}

// ── Props ──

interface DirectoryPickerProps {
  directories: string[];
  onDirectoriesChange: (dirs: string[]) => void;
  maxDirectories?: number;
  className?: string;
}

export function DirectoryPicker({
  directories,
  onDirectoriesChange,
  maxDirectories = 10,
  className,
}: DirectoryPickerProps) {
  const [manualPath, setManualPath] = useState("");
  const [pickerHint, setPickerHint] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const addDirectory = useCallback(
    (path: string) => {
      const trimmed = path.trim();
      if (!trimmed) return;
      if (!looksLikePath(trimmed)) {
        setError("Please enter a valid absolute directory path.");
        return;
      }
      if (directories.includes(trimmed)) {
        setError("This directory is already added.");
        return;
      }
      if (directories.length >= maxDirectories) {
        setError(`Maximum of ${maxDirectories} directories allowed.`);
        return;
      }
      setError(null);
      setPickerHint(null);
      onDirectoriesChange([...directories, trimmed]);
      setManualPath("");
    },
    [directories, maxDirectories, onDirectoriesChange]
  );

  const removeDirectory = useCallback(
    (path: string) => {
      onDirectoriesChange(directories.filter((d) => d !== path));
      setError(null);
    },
    [directories, onDirectoriesChange]
  );

  const handleBrowse = useCallback(async () => {
    if (!hasFileSystemAccess()) return;
    try {
      const pickerWindow = window as DirectoryPickerWindow;
      const handle = await pickerWindow.showDirectoryPicker?.({
        mode: "read",
      });
      if (!handle) {
        return;
      }
      setPickerHint(handle.name);
      if (!manualPath.trim()) {
        setManualPath(`/${handle.name}`);
      }
    } catch (err) {
      // User cancelled — not an error
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError("Could not access directory. Please enter the path manually.");
    }
  }, [manualPath]);

  const handleManualAdd = useCallback(() => {
    addDirectory(manualPath);
  }, [manualPath, addDirectory]);

  return (
    <div className={cn("space-y-4", className)} role="group" aria-label="Directory selection">
      {/* Directory list */}
      {directories.length > 0 && (
        <div className="space-y-2">
          {directories.map((dir) => (
            <div
              key={dir}
              className="flex items-center justify-between rounded-md border bg-muted/50 px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <FolderOpen className="h-4 w-4 shrink-0 text-primary" aria-hidden />
                <span className="truncate text-sm font-mono">{dir}</span>
              </div>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
                    onClick={() => removeDirectory(dir)}
                    aria-label={`Remove ${dir}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Remove directory</TooltipContent>
              </Tooltip>
            </div>
          ))}
        </div>
      )}

      {/* Add directory section */}
      <div className="flex gap-2">
        {hasFileSystemAccess() && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleBrowse}
            className="gap-1.5"
            disabled={directories.length >= maxDirectories}
          >
            <FolderOpen className="h-4 w-4" />
            Browse
          </Button>
        )}

        <Input
          placeholder={
            hasFileSystemAccess()
              ? "Or enter path manually..."
              : "Enter directory path..."
          }
          value={manualPath}
          onChange={(e) => {
            setManualPath(e.target.value);
            setError(null);
            setPickerHint(null);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleManualAdd();
            }
          }}
          className="h-8 flex-1 text-sm font-mono"
          aria-label="Directory path input"
          disabled={directories.length >= maxDirectories}
        />

        <Button
          variant="secondary"
          size="sm"
          onClick={handleManualAdd}
          disabled={!manualPath.trim() || directories.length >= maxDirectories}
          aria-label="Add directory"
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      {pickerHint && (
        <p className="text-xs text-muted-foreground">
          Picked folder: <span className="font-mono">{pickerHint}</span>. Confirm or edit the
          absolute path before adding.
        </p>
      )}

      {/* Count badge */}
      <div className="flex items-center justify-between">
        <Badge variant="outline" className="text-xs">
          {directories.length} / {maxDirectories} directories
        </Badge>
      </div>

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-sm">{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
