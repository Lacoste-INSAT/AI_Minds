"use client";

/**
 * KnowledgeCard — Renders a single timeline item.
 * Displays title, summary, modality icon, entities, and ingestion time.
 *
 * Source: ARCHITECTURE.md §Timeline, DESIGN_SYSTEM.md §Cards
 */

import { memo } from "react";
import {
  FileText,
  FileType,
  Image as ImageIcon,
  Headphones,
  FileJson,
  ExternalLink,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { EntityChip } from "@/components/shared/entity-chip";
import { formatRelativeDate, cn } from "@/lib/utils";
import { MODALITY_CONFIG } from "@/lib/constants";
import type { TimelineItem, TimelineModality } from "@/types/contracts";
import type { EntityType } from "@/types/ui";

// ── Icon resolver ──

const MODALITY_ICONS: Record<TimelineModality, React.ElementType> = {
  text: FileText,
  pdf: FileType,
  image: ImageIcon,
  audio: Headphones,
  json: FileJson,
};

// ── Props ──

interface KnowledgeCardProps {
  item: TimelineItem;
  onSelect?: (id: string) => void;
  className?: string;
}

function KnowledgeCardInner({ item, onSelect, className }: KnowledgeCardProps) {
  const ModalityIcon = MODALITY_ICONS[item.modality] ?? FileText;
  const modalityCfg = MODALITY_CONFIG[item.modality];

  return (
    <Card
      className={cn(
        "group transition-colors hover:border-primary/40 focus-within:ring-2 focus-within:ring-ring",
        className
      )}
      tabIndex={0}
      role="article"
      aria-label={item.title}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect?.(item.id);
        }
      }}
      onClick={() => onSelect?.(item.id)}
    >
      <CardHeader className="flex flex-row items-start gap-3 space-y-0 pb-2">
        {/* Modality icon */}
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
              <ModalityIcon className="h-4 w-4 text-primary" aria-hidden />
            </div>
          </TooltipTrigger>
          <TooltipContent side="top">{modalityCfg?.label ?? item.modality}</TooltipContent>
        </Tooltip>

        <div className="min-w-0 flex-1">
          <CardTitle className="line-clamp-1 text-sm font-semibold leading-tight">
            {item.title}
          </CardTitle>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
            <span>{formatRelativeDate(item.ingested_at)}</span>
            <span aria-hidden>·</span>
            <Badge variant="outline" className="px-1.5 py-0 text-[10px]">
              {item.category ?? "Uncategorized"}

            </Badge>
          </div>
        </div>

        {/* Open source link */}
        {item.source_uri && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 focus:opacity-100"
                aria-label="Open source file"
                onClick={(e) => {
                  e.stopPropagation();
                  // In production this would open a local file viewer
                }}
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="top">Open source</TooltipContent>
          </Tooltip>
        )}
      </CardHeader>

      <CardContent className="space-y-2 pt-0">
        {/* Summary */}
        <p className="line-clamp-2 text-sm text-muted-foreground">
          {item.summary ?? "No summary available"}

        </p>

        {/* Entity chips */}
        {item.entities.length > 0 && (
          <div className="flex flex-wrap gap-1" aria-label="Mentioned entities">
            {item.entities.slice(0, 5).map((entity) => (
              <EntityChip
                key={entity}
                name={entity}
                type={inferEntityType(entity)}
                size="sm"
              />
            ))}
            {item.entities.length > 5 && (
              <Badge variant="secondary" className="text-[10px]">
                +{item.entities.length - 5}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Simple heuristic to infer entity type from entity name.
 * In production, entity type would come from the backend.
 */
function inferEntityType(name: string): EntityType {
  const lower = name.toLowerCase();
  if (lower.includes("inc") || lower.includes("corp") || lower.includes("org"))
    return "organization";
  if (lower.includes("project") || lower.includes("system"))
    return "project";
  // Default to concept
  return "concept";
}

export const KnowledgeCard = memo(KnowledgeCardInner);
