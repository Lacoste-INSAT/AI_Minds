"use client";

import { useState, useMemo, useCallback, useEffect } from "react";
import { Loader2 } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { GraphControls } from "@/components/graph/graph-controls";
import { NodeDetail } from "@/components/graph/node-detail";
import { PatternsPanel } from "@/components/graph/patterns-panel";
import { useGraph } from "@/hooks/use-graph";
import { useInsights } from "@/hooks/use-insights";
import { useIsMobile } from "@/hooks/use-mobile";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import type { GraphNode } from "@/types/contracts";
import type { EntityType, GraphViewState } from "@/types/ui";

const ALL_ENTITY_TYPES: EntityType[] = [
  "person",
  "organization",
  "project",
  "concept",
  "location",
  "datetime",
  "document",
];

export default function GraphPage() {
  const { data, status, refetch } = useGraph();
  const { patterns } = useInsights();
  const isMobile = useIsMobile();
  const graphQuery = useMemo(() => {
    if (typeof window === "undefined") {
      return null;
    }
    return new URLSearchParams(window.location.search).get("q")?.trim().toLowerCase() ?? null;
  }, []);
  const [fallbackNotice, setFallbackNotice] = useState<string | null>(null);

  const [viewState, setViewState] = useState<GraphViewState>({
    dimension: "2d",
    selectedNodeId: null,
    filters: {
      entityTypes: [...ALL_ENTITY_TYPES],
      minMentionCount: 0,
    },
    zoom: 1,
  });

  const updateViewState = useCallback(
    (partial: Partial<GraphViewState>) =>
      setViewState((prev) => ({ ...prev, ...partial })),
    []
  );

  const handleNodeSelect = useCallback(
    (node: GraphNode | null) => {
      updateViewState({ selectedNodeId: node?.id ?? null });
    },
    [updateViewState]
  );

  const handleDimensionFallback = useCallback(() => {
    setFallbackNotice("3D mode is unavailable in this environment. Showing stable 2D mode.");
    updateViewState({ dimension: "2d" });
  }, [updateViewState]);

  useEffect(() => {
    if (!graphQuery || !data) {
      return;
    }
    const matched = data.nodes.find((node) => node.name.toLowerCase().includes(graphQuery));
    if (matched) {
      const deferredSelection = window.setTimeout(() => {
        handleNodeSelect(matched);
      }, 0);
      return () => {
        window.clearTimeout(deferredSelection);
      };
    }
  }, [data, graphQuery, handleNodeSelect]);

  // Apply filters
  const filteredNodes = useMemo(() => {
    if (!data) return [];
    return data.nodes.filter((n) => {
      const type = n.type.toLowerCase() as EntityType;
      if (!viewState.filters.entityTypes.includes(type)) return false;
      if (n.mention_count < viewState.filters.minMentionCount) return false;
      return true;
    });
  }, [data, viewState.filters]);

  const filteredNodeIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes]
  );

  const filteredEdges = useMemo(() => {
    if (!data) return [];
    return data.edges.filter(
      (e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
    );
  }, [data, filteredNodeIds]);

  // Loading
  if (status === "loading" && !data) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="-m-6 flex h-[calc(100vh-3.5rem)] flex-col">
      {/* Header */}
      <div className="border-b px-6 py-4">
        <h1 className="text-2xl font-bold tracking-tight">Knowledge Graph</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Explore connections across your knowledge
        </p>
      </div>

      {/* Controls toolbar */}
      <div className="px-6 py-3">
        <GraphControls
          viewState={viewState}
          onViewStateChange={updateViewState}
          nodeCount={filteredNodes.length}
          edgeCount={filteredEdges.length}
          onRefresh={refetch}
        />
        {fallbackNotice && (
          <p className="mt-2 text-xs text-muted-foreground" role="status" aria-live="polite">
            {fallbackNotice}
          </p>
        )}
        {/* Patterns insights (non-blocking) */}
        {patterns.data?.patterns && (
          <PatternsPanel
            patterns={patterns.data.patterns}
            className="mt-2"
          />
        )}
      </div>

      {/* Graph + detail split */}
      {isMobile ? (
        <>
          <div className="flex-1">
            <GraphCanvas
              nodes={filteredNodes}
              edges={filteredEdges}
              dimension={viewState.dimension}
              onDimensionFallback={handleDimensionFallback}
              selectedNodeId={viewState.selectedNodeId}
              onNodeSelect={handleNodeSelect}
            />
          </div>
          <Sheet
            open={!!viewState.selectedNodeId}
            onOpenChange={(open) => { if (!open) handleNodeSelect(null); }}
          >
            <SheetContent side="bottom" className="h-[70vh]">
              <SheetHeader>
                <SheetTitle>Node Detail</SheetTitle>
              </SheetHeader>
              <NodeDetail
                node={
                  data?.nodes.find((n) => n.id === viewState.selectedNodeId) ??
                  null
                }
                edges={data?.edges ?? []}
                allNodes={data?.nodes ?? []}
                onClose={() => handleNodeSelect(null)}
              />
            </SheetContent>
          </Sheet>
        </>
      ) : (
        <ResizablePanelGroup direction="horizontal" className="flex-1">
          <ResizablePanel defaultSize={viewState.selectedNodeId ? 70 : 100} minSize={50}>
            <GraphCanvas
              nodes={filteredNodes}
              edges={filteredEdges}
              dimension={viewState.dimension}
              onDimensionFallback={handleDimensionFallback}
              selectedNodeId={viewState.selectedNodeId}
              onNodeSelect={handleNodeSelect}
            />
          </ResizablePanel>

          {viewState.selectedNodeId && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={30} minSize={20} maxSize={45}>
                <NodeDetail
                  node={
                    data?.nodes.find((n) => n.id === viewState.selectedNodeId) ??
                    null
                  }
                  edges={data?.edges ?? []}
                  allNodes={data?.nodes ?? []}
                  onClose={() => handleNodeSelect(null)}
                />
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
      )}
    </div>
  );
}
