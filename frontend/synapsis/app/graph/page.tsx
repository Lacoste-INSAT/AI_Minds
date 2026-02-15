"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState, useRef } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
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
import { RefreshCw, Search, ZoomIn, ZoomOut, Maximize2, Loader2 } from "lucide-react";

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
    </div>
  ),
});

interface GraphNode {
  id: string;
  type: string;
  name: string;
  properties?: Record<string, unknown>;
  mention_count: number;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  properties?: Record<string, unknown>;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Color palette for node types
const NODE_COLORS: Record<string, string> = {
  person: "#3b82f6",    // blue
  project: "#22c55e",   // green
  organization: "#f59e0b", // amber
  location: "#ef4444",  // red
  concept: "#8b5cf6",   // purple
  date: "#ec4899",      // pink
  technology: "#06b6d4", // cyan
  default: "#6b7280",   // gray
};

export default function GraphExplorerPage() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);

  const fetchGraphData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/memory/graph?limit=200");
      if (!response.ok) {
        throw new Error(`Failed to fetch graph data: ${response.status}`);
      }
      const data = await response.json();
      setGraphData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load graph");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // Search highlighting
  useEffect(() => {
    if (!graphData || !searchTerm) {
      setHighlightNodes(new Set());
      return;
    }
    const term = searchTerm.toLowerCase();
    const matches = new Set<string>();
    graphData.nodes.forEach((node) => {
      if (node.name.toLowerCase().includes(term) || node.type.toLowerCase().includes(term)) {
        matches.add(node.id);
      }
    });
    setHighlightNodes(matches);
  }, [searchTerm, graphData]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node as GraphNode);
    // Center on node
    if (graphRef.current) {
      graphRef.current.centerAt(node.x, node.y, 1000);
      graphRef.current.zoom(2, 1000);
    }
  }, []);

  const handleZoomIn = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom * 1.5, 300);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom / 1.5, 300);
    }
  };

  const handleFitView = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

  // Transform data for react-force-graph
  const forceGraphData = graphData
    ? {
        nodes: graphData.nodes.map((n) => ({
          ...n,
          val: Math.max(n.mention_count, 1) * 2, // Node size based on mentions
          color: NODE_COLORS[n.type.toLowerCase()] || NODE_COLORS.default,
        })),
        links: graphData.edges.map((e) => ({
          ...e,
          source: e.source,
          target: e.target,
        })),
      }
    : { nodes: [], links: [] };

  // Get node types for legend
  const nodeTypes = graphData
    ? [...new Set(graphData.nodes.map((n) => n.type.toLowerCase()))]
    : [];

  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex flex-col h-screen">
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>Knowledge Graph</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
        </header>

        <div className="flex flex-1 overflow-hidden">
          {/* Main Graph Area */}
          <div className="flex-1 relative">
            {/* Toolbar */}
            <div className="absolute top-4 left-4 z-10 flex gap-2">
              <div className="flex items-center gap-2 bg-background/80 backdrop-blur rounded-lg p-2 shadow-lg border">
                <Search className="w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search nodes..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-48 h-8"
                />
              </div>
              <div className="flex gap-1 bg-background/80 backdrop-blur rounded-lg p-1 shadow-lg border">
                <Button size="icon" variant="ghost" onClick={handleZoomIn} title="Zoom In">
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={handleZoomOut} title="Zoom Out">
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={handleFitView} title="Fit View">
                  <Maximize2 className="w-4 h-4" />
                </Button>
                <Button size="icon" variant="ghost" onClick={fetchGraphData} title="Refresh">
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                </Button>
              </div>
            </div>

            {/* Legend */}
            <div className="absolute bottom-4 left-4 z-10 bg-background/80 backdrop-blur rounded-lg p-3 shadow-lg border">
              <div className="text-xs font-medium mb-2">Node Types</div>
              <div className="flex flex-wrap gap-2">
                {nodeTypes.map((type) => (
                  <div key={type} className="flex items-center gap-1">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: NODE_COLORS[type] || NODE_COLORS.default }}
                    />
                    <span className="text-xs capitalize">{type}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="absolute top-4 right-4 z-10 bg-background/80 backdrop-blur rounded-lg p-3 shadow-lg border">
              <div className="text-xs space-y-1">
                <div>
                  <span className="text-muted-foreground">Nodes:</span>{" "}
                  <span className="font-medium">{graphData?.nodes.length ?? 0}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Edges:</span>{" "}
                  <span className="font-medium">{graphData?.edges.length ?? 0}</span>
                </div>
              </div>
            </div>

            {/* Graph */}
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-full">
                <Card className="w-96">
                  <CardHeader>
                    <CardTitle className="text-destructive">Error</CardTitle>
                    <CardDescription>{error}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button onClick={fetchGraphData}>Retry</Button>
                  </CardContent>
                </Card>
              </div>
            ) : graphData?.nodes.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <Card className="w-96">
                  <CardHeader>
                    <CardTitle>No Data</CardTitle>
                    <CardDescription>
                      No knowledge graph data yet. Add some documents to your watched directories to
                      populate the graph.
                    </CardDescription>
                  </CardHeader>
                </Card>
              </div>
            ) : (
              <ForceGraph2D
                ref={graphRef}
                graphData={forceGraphData}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                nodeLabel={(node: any) => `${node.name} (${node.type})`}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                nodeColor={(node: any) =>
                  highlightNodes.size > 0
                    ? highlightNodes.has(node.id)
                      ? node.color
                      : "#e5e7eb"
                    : node.color
                }
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                nodeVal={(node: any) => node.val}
                linkColor={() => "#94a3b8"}
                linkWidth={1}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                onNodeClick={handleNodeClick}
                enableNodeDrag={true}
                cooldownTicks={100}
                onEngineStop={() => graphRef.current?.zoomToFit(400)}
              />
            )}
          </div>

          {/* Detail Panel */}
          {selectedNode && (
            <div className="w-80 border-l bg-muted/30 p-4 overflow-y-auto">
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <Badge
                      style={{
                        backgroundColor:
                          NODE_COLORS[selectedNode.type.toLowerCase()] || NODE_COLORS.default,
                      }}
                    >
                      {selectedNode.type}
                    </Badge>
                    <Button size="icon" variant="ghost" onClick={() => setSelectedNode(null)}>
                      ×
                    </Button>
                  </div>
                  <CardTitle className="text-lg mt-2">{selectedNode.name}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="text-xs text-muted-foreground mb-1">Mentions</div>
                    <div className="font-medium">{selectedNode.mention_count}</div>
                  </div>
                  {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Properties</div>
                      <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                        {JSON.stringify(selectedNode.properties, null, 2)}
                      </pre>
                    </div>
                  )}
                  {/* Related edges */}
                  {graphData && (
                    <div>
                      <div className="text-xs text-muted-foreground mb-1">Connections</div>
                      <div className="space-y-1">
                        {graphData.edges
                          .filter(
                            (e) => e.source === selectedNode.id || e.target === selectedNode.id
                          )
                          .slice(0, 10)
                          .map((edge) => {
                            const isSource = edge.source === selectedNode.id;
                            const otherId = isSource ? edge.target : edge.source;
                            const otherNode = graphData.nodes.find((n) => n.id === otherId);
                            return (
                              <div
                                key={edge.id}
                                className="text-xs p-2 bg-muted rounded flex items-center gap-2"
                              >
                                <span className="text-muted-foreground">
                                  {isSource ? "→" : "←"}
                                </span>
                                <span className="font-medium">{edge.relationship}</span>
                                <span className="text-muted-foreground">
                                  {isSource ? "→" : "←"}
                                </span>
                                <span
                                  className="truncate cursor-pointer hover:underline"
                                  onClick={() => {
                                    if (otherNode) {
                                      setSelectedNode(otherNode as GraphNode);
                                    }
                                  }}
                                >
                                  {otherNode?.name ?? otherId}
                                </span>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
