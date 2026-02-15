"use client";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import { useFetch } from "@/lib/hooks";
import { getGraph, getGraphStats, type GraphData } from "@/lib/api";
import { RotateCcw, Box, Maximize2 } from "lucide-react";

/* ---------- lazy-load react-force-graph-3d (needs window / WebGL) ---------- */
const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });

/* ---------- colour palette (lowercase-keyed) ---------- */
const TYPE_COLORS: Record<string, string> = {
  person: "#6366f1",
  organization: "#22c55e",
  concept: "#f59e0b",
  location: "#3b82f6",
  event: "#ef4444",
  technology: "#8b5cf6",
  work_of_art: "#ec4899",
  group: "#14b8a6",
  date: "#f97316",
  email: "#06b6d4",
  url: "#a855f7",
  phone: "#84cc16",
  default: "#64748b",
};

const getColor = (type: string) =>
  TYPE_COLORS[type.toLowerCase()] || TYPE_COLORS.default;

/* ======================================================================== */

export default function GraphPage() {
  const { data, loading } = useFetch(() => getGraph(200));
  const { data: gstats } = useFetch(getGraphStats);
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>(null);                // ForceGraph3D instance ref
  const [dims, setDims] = useState({ w: 800, h: 600 });

  /* ---- keep the container's pixel size in state for ForceGraph ---- */
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => {
      const { width, height } = el.getBoundingClientRect();
      if (width > 0 && height > 0) setDims({ w: Math.round(width), h: Math.round(height) });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  /* ---- transform API data → ForceGraph node/link format ---- */
  const graphData = useMemo(() => {
    if (!data) return { nodes: [], links: [] };
    const nodeSet = new Set(data.nodes.map((n) => n.id));
    return {
      nodes: data.nodes.map((n) => ({
        id: n.id,
        name: n.name,
        type: n.type,
        val: Math.max(2, Math.min((n.mention_count || 1) * 1.5, 20)),
        color: getColor(n.type),
      })),
      links: data.edges
        .filter((e) => nodeSet.has(e.source) && nodeSet.has(e.target))
        .map((e) => ({
          source: e.source,
          target: e.target,
          label: e.relationship,
        })),
    };
  }, [data]);

  /* ---- stats line ---- */
  const statsLine = useMemo(() => {
    if (!data) return "Loading…";
    const parts = [`${data.nodes.length} nodes`, `${data.edges.length} edges`];
    if (gstats) {
      const gs = gstats as Record<string, unknown>;
      if (gs.connected_components) parts.push(`${gs.connected_components} components`);
    }
    return parts.join(" · ");
  }, [data, gstats]);

  /* ---- camera helpers ---- */
  const resetCamera = useCallback(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.cameraPosition({ x: 0, y: 0, z: 350 }, { x: 0, y: 0, z: 0 }, 800);
  }, []);

  const zoomToFit = useCallback(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.zoomToFit(600, 60);
  }, []);

  const handleNodeClick = useCallback((node: any) => {
    const fg = fgRef.current;
    if (!fg) return;
    const dist = 80;
    const pos = node;
    fg.cameraPosition(
      { x: pos.x + dist, y: pos.y + dist / 2, z: pos.z + dist },
      { x: pos.x, y: pos.y, z: pos.z },
      600,
    );
  }, []);

  /* ---- custom node painting (sphere + sprite label) ---- */
  const nodeThreeObject = useCallback((node: any) => {
    // We use the default sphere but add a text sprite for the label
    const THREE = require("three");
    const SpriteText = require("three-spritetext").default;

    const group = new THREE.Group();

    // Sphere
    const radius = Math.cbrt(node.val) * 2.2;
    const geo = new THREE.SphereGeometry(radius, 16, 12);
    const mat = new THREE.MeshPhongMaterial({
      color: node.color,
      transparent: true,
      opacity: 0.92,
      shininess: 60,
    });
    const mesh = new THREE.Mesh(geo, mat);
    group.add(mesh);

    // Glow ring
    const glowGeo = new THREE.RingGeometry(radius + 0.6, radius + 1.4, 24);
    const glowMat = new THREE.MeshBasicMaterial({
      color: node.color,
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
    });
    const ring = new THREE.Mesh(glowGeo, glowMat);
    group.add(ring);

    // Label sprite
    const label = node.name.length > 20 ? node.name.slice(0, 18) + "…" : node.name;
    const sprite = new SpriteText(label);
    sprite.color = "#cbd5e1";
    sprite.textHeight = 3.2;
    sprite.backgroundColor = "rgba(15,23,42,0.65)";
    sprite.padding = 1.2;
    sprite.borderRadius = 2;
    sprite.position.y = -(radius + 5);
    group.add(sprite);

    return group;
  }, []);

  /* ---- link appearance ---- */
  const linkColor = useCallback(() => "rgba(100,116,139,0.25)", []);
  const linkWidth = useCallback(() => 0.6, []);

  return (
    <div className="animate-fade-in h-[calc(100vh-6rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Box className="w-6 h-6 text-accent-light" />
            Knowledge Graph
            <span className="text-xs font-normal text-accent-light bg-accent/20 rounded px-2 py-0.5 ml-2">3D</span>
          </h2>
          <p className="text-sm text-muted mt-1">{statsLine}</p>
        </div>
        <div className="flex gap-1.5">
          <button
            onClick={zoomToFit}
            className="bg-card/80 backdrop-blur border border-border rounded-lg px-3 py-1.5 text-xs hover:bg-accent/20 transition-colors flex items-center gap-1.5"
          >
            <Maximize2 className="w-3.5 h-3.5" /> Fit
          </button>
          <button
            onClick={resetCamera}
            className="bg-card/80 backdrop-blur border border-border rounded-lg px-3 py-1.5 text-xs hover:bg-accent/20 transition-colors flex items-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset
          </button>
        </div>
      </div>

      {/* 3D Graph container */}
      <div
        ref={containerRef}
        className="flex-1 bg-card border border-border rounded-xl overflow-hidden min-h-0 relative"
      >
        {loading || !data ? (
          <div className="flex items-center justify-center h-full text-muted">Loading graph…</div>
        ) : data.nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted">
            No graph data yet. Ingest some files first.
          </div>
        ) : (
          <ForceGraph3D
            ref={fgRef}
            width={dims.w}
            height={dims.h}
            graphData={graphData}
            backgroundColor="rgba(0,0,0,0)"
            nodeThreeObject={nodeThreeObject}
            nodeThreeObjectExtend={false}
            linkColor={linkColor}
            linkWidth={linkWidth}
            linkOpacity={0.35}
            linkDirectionalParticles={1}
            linkDirectionalParticleWidth={1.2}
            linkDirectionalParticleSpeed={0.004}
            linkDirectionalParticleColor={linkColor}
            enableNodeDrag={true}
            enableNavigationControls={true}
            showNavInfo={false}
            warmupTicks={80}
            cooldownTicks={200}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
            onNodeClick={handleNodeClick}
          />
        )}

        {/* Controls hint */}
        <div className="absolute bottom-3 left-3 text-[10px] text-muted/50 pointer-events-none">
          Left-drag: rotate · Right-drag: pan · Scroll: zoom · Click node: focus
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-muted flex-wrap">
        {Object.entries(TYPE_COLORS)
          .filter(([k]) => k !== "default")
          .map(([type, color]) => (
            <span key={type} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
              {type}
            </span>
          ))}
      </div>
    </div>
  );
}
