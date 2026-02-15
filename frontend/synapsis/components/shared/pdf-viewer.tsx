"use client";

import { useState } from "react";
import { FileWarning } from "lucide-react";
import { cn } from "@/lib/utils";

interface PdfViewerProps {
  sourceUrl?: string;
  snippet: string;
  title?: string;
  className?: string;
}

export function PdfViewer({ sourceUrl, snippet, title, className }: PdfViewerProps) {
  const [hasError, setHasError] = useState(false);
  const canRenderPdf = Boolean(sourceUrl) && !hasError;

  if (!canRenderPdf) {
    return (
      <div className={cn("rounded-md border bg-muted/40 p-3", className)}>
        <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
          <FileWarning className="h-3.5 w-3.5" />
          <span>PDF preview unavailable. Showing snippet fallback.</span>
        </div>
        <p className="text-sm text-muted-foreground">{snippet}</p>
      </div>
    );
  }

  return (
    <div className={cn("overflow-hidden rounded-md border", className)}>
      <iframe
        title={title ?? "PDF evidence preview"}
        src={sourceUrl}
        className="h-64 w-full bg-background"
        onError={() => setHasError(true)}
      />
    </div>
  );
}

