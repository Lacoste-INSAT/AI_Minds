"use client";

/**
 * GraphControls — Toolbar for graph view.
 * Entity type filters, mention-count threshold, reset view.
 *
 * Source: ARCHITECTURE.md §Knowledge Graph, DESIGN_SYSTEM.md
 */

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { RefreshCw } from "lucide-react";
import { ENTITY_TYPE_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { EntityType, GraphDimension, GraphViewState } from "@/types/ui";

// ── Props ──

interface GraphControlsProps {
  viewState: GraphViewState;
  onViewStateChange: (partial: Partial<GraphViewState>) => void;
  nodeCount: number;
  edgeCount: number;
  onRefresh: () => void;
  className?: string;
}

const ENTITY_TYPES = Object.keys(ENTITY_TYPE_CONFIG) as EntityType[];
const GRAPH_DIMENSIONS: GraphDimension[] = ["2d", "3d"];

export function GraphControls({
  viewState,
  onViewStateChange,
  nodeCount,
  edgeCount,
  onRefresh,
  className,
}: GraphControlsProps) {
  const toggleEntityType = (type: EntityType) => {
    const current = viewState.filters.entityTypes;
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    onViewStateChange({
      filters: { ...viewState.filters, entityTypes: next },
    });
  };

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 rounded-lg border bg-card px-4 py-3",
        className
      )}
      role="toolbar"
      aria-label="Graph controls"
    >
      {/* Entity type filters */}
      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by entity type">
        {ENTITY_TYPES.map((type) => {
          const cfg = ENTITY_TYPE_CONFIG[type];
          const active = viewState.filters.entityTypes.includes(type);
          return (
            <Badge
              key={type}
              variant={active ? "default" : "outline"}
              className={cn(
                "cursor-pointer select-none transition-colors",
                active && "bg-primary text-primary-foreground"
              )}
              onClick={() => toggleEntityType(type)}
              role="checkbox"
              aria-checked={active}
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  toggleEntityType(type);
                }
              }}
            >
              {cfg.label}
            </Badge>
          );
        })}
      </div>

      <div className="flex items-center gap-1 rounded-md border p-1" role="group" aria-label="Graph mode">
        {GRAPH_DIMENSIONS.map((mode) => (
          <Button
            key={mode}
            type="button"
            size="sm"
            variant={viewState.dimension === mode ? "default" : "ghost"}
            className="h-7 px-2 text-xs uppercase"
            onClick={() => onViewStateChange({ dimension: mode })}
            aria-pressed={viewState.dimension === mode}
          >
            {mode}
          </Button>
        ))}
      </div>

      {/* Mention count threshold */}
      <div className="flex items-center gap-2">
        <Label htmlFor="mention-slider" className="text-xs text-muted-foreground whitespace-nowrap">
          Min mentions
        </Label>
        <Slider
          id="mention-slider"
          min={0}
          max={20}
          step={1}
          value={[viewState.filters.minMentionCount]}
          onValueChange={([val]) =>
            onViewStateChange({
              filters: { ...viewState.filters, minMentionCount: val },
            })
          }
          className="w-24"
          aria-label="Minimum mention count"
        />
        <span className="w-5 text-center text-xs font-mono text-muted-foreground">
          {viewState.filters.minMentionCount}
        </span>
      </div>

      {/* Stats */}
      <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
        <span>{nodeCount} nodes</span>
        <span aria-hidden>·</span>
        <span>{edgeCount} edges</span>
      </div>

      {/* Refresh */}
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="outline"
            size="icon"
            className="h-7 w-7"
            onClick={onRefresh}
            aria-label="Refresh graph data"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>Refresh graph</TooltipContent>
      </Tooltip>
    </div>
  );
}
