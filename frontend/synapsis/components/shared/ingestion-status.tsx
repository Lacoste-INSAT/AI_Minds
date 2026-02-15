"use client";

/**
 * IngestionStatus — Queue/progress widget for file processing.
 *
 * Source: DESIGN_SYSTEM §5.2, ARCHITECTURE ingestion contract
 */

import { FileCheck, Loader2, AlertCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { IngestionStatusResponse } from "@/types/contracts";
import { cn } from "@/lib/utils";
import { formatRelativeDate } from "@/lib/utils";

interface IngestionStatusProps {
  data: IngestionStatusResponse | null;
  className?: string;
}

export function IngestionStatus({ data, className }: IngestionStatusProps) {
  if (!data) {
    return (
      <div className={cn("flex items-center gap-2 text-xs text-muted-foreground", className)}>
        <Loader2 className="size-3.5 animate-spin" />
        <span>Loading status...</span>
      </div>
    );
  }

  const total = data.files_processed + data.files_failed + data.files_skipped;
  const hasErrors = data.files_failed > 0;
  const isProcessing = data.queue_depth > 0;

  const progress = total > 0
    ? Math.round((data.files_processed / total) * 100)
    : 100;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "flex items-center gap-2 text-xs text-muted-foreground",
            className
          )}
          role="status"
          aria-label={`${data.files_processed} files processed`}
        >
          {isProcessing ? (
            <Loader2 className="size-3.5 animate-spin" />
          ) : hasErrors ? (
            <AlertCircle className="size-3.5 text-destructive" />
          ) : (
            <FileCheck className="size-3.5" />
          )}
          <span>
            {isProcessing
              ? `Processing (${data.queue_depth} in queue)`
              : `${data.files_processed} processed`}
          </span>
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between gap-4">
            <span>Processed:</span>
            <span className="font-mono">{data.files_processed}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span>Failed:</span>
            <span className="font-mono">{data.files_failed}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span>Skipped:</span>
            <span className="font-mono">{data.files_skipped}</span>
          </div>
          {data.last_scan_time && (
            <div className="flex justify-between gap-4">
              <span>Last scan:</span>
              <span>{formatRelativeDate(data.last_scan_time)}</span>
            </div>
          )}
          {isProcessing && <Progress value={progress} className="h-1.5" />}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
