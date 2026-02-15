"use client";

/**
 * GraphCanvas — 2D/3D force-directed graph using react-force-graph.
 * Dynamically imported to avoid SSR issues. Falls back to loading state.
 *
 * Source: ARCHITECTURE.md §Knowledge Graph, DESIGN_SYSTEM.md
 */

import {
  useState,
  useCallback,
  useRef,
  useMemo,
  useEffect,
  type ComponentType,
} from "react";
import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { BRAND_COPY } from "@/lib/constants";
import type { GraphNode, GraphEdge } from "@/types/contracts";
import type { GraphDimension } from "@/types/ui";

// ── Dynamic import react-force-graph (client-only) ──

interface ForceGraphProps {
  graphData: { nodes: GraphNodeRender[]; links: GraphLinkRender[] };
  nodeLabel?: string | ((node: GraphNodeRender) => string);
  nodeColor?: (node: GraphNodeRender) => string;
  nodeVal?: (node: GraphNodeRender) => number;
  linkLabel?: string | ((link: GraphLinkRender) => string);
  linkColor?: () => string;
  linkDirectionalArrowLength?: number;
  linkDirectionalArrowRelPos?: number;
  onNodeClick?: (node: GraphNodeRender) => void;
  width?: number;
  height?: number;
  backgroundColor?: string;
  cooldownTicks?: number;
}

const ForceGraph2D: ComponentType<ForceGraphProps> = dynamic(
  () =>
    import("react-force-graph-2d").then(
      (mod) => mod.default as unknown as ComponentType<ForceGraphProps>
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  }
) as ComponentType<ForceGraphProps>;

const ForceGraph3D: ComponentType<ForceGraphProps> = dynamic(
  () =>
    import("react-force-graph-3d").then(
      (mod) => mod.default as unknown as ComponentType<ForceGraphProps>
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    ),
  }
) as ComponentType<ForceGraphProps>;

// ── Render types ──

interface GraphNodeRender {
  id: string;
  name: string;
  type: string;
  val: number;
  color: string;
}

interface GraphLinkRender {
  source: string;
  target: string;
  relationship: string;
}

// ── Entity-type to color mapping (CSS var → computed) ──

const ENTITY_COLORS: Record<string, string> = {
  person: "#6366f1",
  organization: "#f59e0b",
  project: "#22c55e",
  concept: "#06b6d4",
  location: "#ef4444",
  datetime: "#8b5cf6",
  document: "#64748b",
};

function getNodeColor(type: string): string {
  return ENTITY_COLORS[type.toLowerCase()] ?? "#94a3b8";
}

// ── Props ──

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  dimension?: GraphDimension;
  onNodeSelect?: (node: GraphNode | null) => void;
  onDimensionFallback?: (fallback: GraphDimension) => void;
  selectedNodeId?: string | null;
  className?: string;
}

export function GraphCanvas({
  nodes,
  edges,
  dimension = "2d",
  onNodeSelect,
  onDimensionFallback,
  selectedNodeId,
  className,
}: GraphCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [isReducedMotion, setIsReducedMotion] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });
  const supportsWebGl =
    typeof window !== "undefined" && typeof window.WebGLRenderingContext !== "undefined";

  // Measure container
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        setDimensions({ width: Math.floor(width), height: Math.floor(height) });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }
    const reduceMediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

    const onReduceMotionChange = (event: MediaQueryListEvent) => {
      setIsReducedMotion(event.matches);
    };

    reduceMediaQuery.addEventListener("change", onReduceMotionChange);
    return () => {
      reduceMediaQuery.removeEventListener("change", onReduceMotionChange);
    };
  }, []);

  const renderDimension: GraphDimension =
    dimension === "3d" && !isReducedMotion && supportsWebGl ? "3d" : "2d";

  useEffect(() => {
    if (dimension === "3d" && renderDimension === "2d") {
      onDimensionFallback?.("2d");
    }
  }, [dimension, renderDimension, onDimensionFallback]);

  // Transform to render format
  const graphData = useMemo(() => {
    const renderNodes: GraphNodeRender[] = nodes.map((n) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      val: Math.max(1, Math.min(n.mention_count, 20)),
      color: getNodeColor(n.type),
    }));

    const renderLinks: GraphLinkRender[] = edges.map((e) => ({
      source: e.source,
      target: e.target,
      relationship: e.relationship,
    }));

    return { nodes: renderNodes, links: renderLinks };
  }, [nodes, edges]);

  const handleNodeClick = useCallback(
    (node: GraphNodeRender) => {
      const original = nodes.find((n) => n.id === node.id) ?? null;
      onNodeSelect?.(original);
    },
    [nodes, onNodeSelect]
  );

  // Empty state
  if (nodes.length === 0) {
    return (
      <div
        className={cn(
          "flex h-full items-center justify-center",
          className
        )}
        role="status"
      >
        <p className="text-sm text-muted-foreground">
          {BRAND_COPY.EMPTY_GRAPH}
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn("relative h-full w-full overflow-hidden rounded-lg bg-background", className)}
      role="img"
      aria-label="Knowledge graph visualization"
    >
      {renderDimension === "3d" ? (
        <ForceGraph3D
          graphData={graphData}
          nodeLabel={(node) => `${node.name} (${node.type})`}
          nodeColor={(node) =>
            node.id === selectedNodeId ? "hsl(var(--primary))" : node.color
          }
          nodeVal={(node) => node.val}
          linkLabel={(link) => link.relationship}
          linkColor={() => "hsl(var(--muted-foreground) / 0.3)"}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="transparent"
          cooldownTicks={100}
        />
      ) : (
        <ForceGraph2D
          graphData={graphData}
          nodeLabel={(node) => `${node.name} (${node.type})`}
          nodeColor={(node) =>
            node.id === selectedNodeId ? "hsl(var(--primary))" : node.color
          }
          nodeVal={(node) => node.val}
          linkLabel={(link) => link.relationship}
          linkColor={() => "hsl(var(--muted-foreground) / 0.3)"}
          linkDirectionalArrowLength={4}
          linkDirectionalArrowRelPos={1}
          onNodeClick={handleNodeClick}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="transparent"
          cooldownTicks={100}
        />
      )}
    </div>
  );
}
