"use client";

/**
 * NodeDetail — Side panel showing details for a selected graph node.
 * Displays entity properties, mention count, and related edges.
 *
 * Source: ARCHITECTURE.md §Knowledge Graph, DESIGN_SYSTEM.md
 */

import { X, Link2, Hash } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { EntityChip } from "@/components/shared/entity-chip";
import { cn } from "@/lib/utils";
import { ENTITY_TYPE_CONFIG } from "@/lib/constants";
import type { GraphNode, GraphEdge } from "@/types/contracts";
import type { EntityType } from "@/types/ui";

// ── Props ──

interface NodeDetailProps {
  node: GraphNode | null;
  edges: GraphEdge[];
  allNodes: GraphNode[];
  onClose: () => void;
  className?: string;
}

export function NodeDetail({
  node,
  edges,
  allNodes,
  onClose,
  className,
}: NodeDetailProps) {
  if (!node) return null;

  // Find connected edges
  const connectedEdges = edges.filter(
    (e) => e.source === node.id || e.target === node.id
  );

  // Find connected node names
  const connectedNodeIds = new Set(
    connectedEdges.flatMap((e) => [e.source, e.target]).filter((id) => id !== node.id)
  );
  const connectedNodes = allNodes.filter((n) => connectedNodeIds.has(n.id));

  const entityType = node.type.toLowerCase() as EntityType;
  const entityCfg = ENTITY_TYPE_CONFIG[entityType];

  return (
    <div
      className={cn(
        "flex h-full flex-col border-l bg-card",
        className
      )}
      role="complementary"
      aria-label={`Details for ${node.name}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold">{node.name}</h3>
          <Badge variant="outline" className="mt-1 text-[10px]">
            {entityCfg?.label ?? node.type}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={onClose}
          aria-label="Close node details"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-4 p-4">
          {/* Stats */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Hash className="h-3.5 w-3.5" aria-hidden />
              <span>{node.mention_count} mentions</span>
            </div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <Link2 className="h-3.5 w-3.5" aria-hidden />
              <span>{connectedEdges.length} connections</span>
            </div>
          </div>

          {/* Properties */}
          {node.properties && Object.keys(node.properties).length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Properties
                </h4>
                <dl className="space-y-1.5">
                  {Object.entries(node.properties).map(([key, value]) => (
                    <div key={key} className="flex items-baseline gap-2 text-sm">
                      <dt className="font-mono text-xs text-muted-foreground">
                        {key}
                      </dt>
                      <dd className="text-foreground">{String(value)}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </>
          )}

          {/* Relationships */}
          {connectedEdges.length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Relationships
                </h4>
                <div className="space-y-2">
                  {connectedEdges.map((edge) => {
                    const isSource = edge.source === node.id;
                    const otherId = isSource ? edge.target : edge.source;
                    const otherNode = allNodes.find((n) => n.id === otherId);
                    return (
                      <div
                        key={edge.id}
                        className="flex items-center gap-2 rounded-md border px-3 py-2 text-xs"
                      >
                        <span className="font-medium text-foreground">
                          {isSource ? node.name : otherNode?.name ?? otherId}
                        </span>
                        <Badge variant="secondary" className="px-1.5 text-[10px]">
                          {edge.relationship}
                        </Badge>
                        <span className="font-medium text-foreground">
                          {isSource ? otherNode?.name ?? otherId : node.name}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {/* Connected entities */}
          {connectedNodes.length > 0 && (
            <>
              <Separator />
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Connected Entities
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {connectedNodes.map((cn) => (
                    <EntityChip
                      key={cn.id}
                      name={cn.name}
                      type={cn.type.toLowerCase() as EntityType}
                      size="sm"
                    />
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
