"use client";

/**
 * SourceCitation — Clickable citation badge [Source N].
 * Opens evidence in source panel or hover preview.
 *
 * Source: DESIGN_SYSTEM, ARCHITECTURE Trust UX §6.1
 */

import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import type { ChunkEvidence } from "@/types/contracts";
import { truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface SourceCitationProps {
  index: number;
  source: ChunkEvidence;
  onClick?: () => void;
  className?: string;
}

export function SourceCitation({
  index,
  source,
  onClick,
  className,
}: SourceCitationProps) {
  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <Badge
          variant="secondary"
          className={cn(
            "cursor-pointer font-mono text-xs transition-colors hover:bg-primary hover:text-primary-foreground",
            className
          )}
          onClick={onClick}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              onClick?.();
            }
          }}
        >
          [Source {index + 1}]
        </Badge>
      </HoverCardTrigger>
      <HoverCardContent className="w-80">
        <div className="space-y-2">
          <p className="font-mono text-xs text-muted-foreground">
            {source.file_name}
          </p>
          <p className="text-sm leading-relaxed">
            {truncate(source.snippet, 200)}
          </p>
          <div className="flex gap-3 font-mono text-xs text-muted-foreground">
            <span>Score: {Math.round(source.score_final * 100)}%</span>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
