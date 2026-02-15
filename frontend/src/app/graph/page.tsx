"use client";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useFetch } from "@/lib/hooks";
import { getGraph, getGraphStats, type GraphData } from "@/lib/api";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

const TYPE_COLORS: Record<string, string> = {
  person: "#6366f1", organization: "#22c55e", concept: "#f59e0b",
  location: "#3b82f6", event: "#ef4444", technology: "#8b5cf6",
  work_of_art: "#ec4899", group: "#14b8a6", date: "#f97316",
  email: "#06b6d4", url: "#a855f7", phone: "#84cc16",
  default: "#64748b",
};

interface Pos { x: number; y: number; vx: number; vy: number }

function GraphCanvas({ data }: { data: GraphData }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef(0);
  const tickRef = useRef(0);
  const sizeRef = useRef({ w: 800, h: 600 });
  const zoomRef = useRef(1);
  const offsetRef = useRef({ x: 0, y: 0 });
  const posRef = useRef<Map<string, Pos>>(new Map());
  const dragRef = useRef<{ dragging: boolean; lastX: number; lastY: number }>({
    dragging: false, lastX: 0, lastY: 0,
  });
  const [, forceRender] = useState(0);           // only for zoom buttons label

  const getColor = useCallback(
    (type: string) => TYPE_COLORS[type.toLowerCase()] || TYPE_COLORS.default,
    [],
  );

  // ── Stable data refs so the draw loop never depends on React state ──
  const dataRef = useRef(data);
  dataRef.current = data;

  // ── Resize handler ──
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      const w = Math.round(rect.width);
      const h = Math.round(rect.height);
      if (w < 1 || h < 1) return;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      sizeRef.current = { w, h };
    };
    resize();

    const ro = new ResizeObserver(resize);
    ro.observe(container);
    return () => ro.disconnect();
  }, []);

  // ── Init positions whenever data changes ──
  useEffect(() => {
    const { w, h } = sizeRef.current;
    const pos = posRef.current;
    // Clear stale nodes that are no longer in data
    const idSet = new Set(data.nodes.map((n) => n.id));
    for (const key of pos.keys()) {
      if (!idSet.has(key)) pos.delete(key);
    }
    // Add new nodes
    data.nodes.forEach((n) => {
      if (!pos.has(n.id)) {
        pos.set(n.id, {
          x: w / 2 + (Math.random() - 0.5) * w * 0.5,
          y: h / 2 + (Math.random() - 0.5) * h * 0.5,
          vx: 0, vy: 0,
        });
      }
    });
    tickRef.current = 0;  // restart simulation cooling when new data arrives
  }, [data]);

  // ── Main animation loop — runs once, reads everything from refs ──
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let running = true;

    const draw = () => {
      if (!running) return;
      const { nodes, edges } = dataRef.current;
      const pos = posRef.current;
      const { w, h } = sizeRef.current;
      const zoom = zoomRef.current;
      const off = offsetRef.current;
      const dpr = window.devicePixelRatio || 1;

      if (w < 1 || h < 1 || nodes.length === 0) {
        frameRef.current = requestAnimationFrame(draw);
        return;
      }

      // ── Physics step (cool down over 300 ticks) ──
      tickRef.current++;
      const alpha = Math.max(0.002, 1 - tickRef.current / 300);

      // Repulsion (Coulomb)
      for (let i = 0; i < nodes.length; i++) {
        const a = pos.get(nodes[i].id);
        if (!a) continue;
        for (let j = i + 1; j < nodes.length; j++) {
          const b = pos.get(nodes[j].id);
          if (!b) continue;
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          const dist2 = dx * dx + dy * dy;
          const dist = Math.max(Math.sqrt(dist2), 1);
          const force = (1200 / dist2) * alpha;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          a.vx += fx; a.vy += fy;
          b.vx -= fx; b.vy -= fy;
        }
      }

      // Attraction (Hooke along edges)
      edges.forEach((e) => {
        const a = pos.get(e.source);
        const b = pos.get(e.target);
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
        const force = (dist - 100) * 0.008 * alpha;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      });

      // Center gravity
      nodes.forEach((n) => {
        const p = pos.get(n.id);
        if (!p) return;
        p.vx += (w / 2 - p.x) * 0.0015 * alpha;
        p.vy += (h / 2 - p.y) * 0.0015 * alpha;
      });

      // Integrate & clamp
      nodes.forEach((n) => {
        const p = pos.get(n.id);
        if (!p) return;
        p.vx *= 0.55; p.vy *= 0.55;
        p.x += p.vx; p.y += p.vy;
        p.x = Math.max(30, Math.min(w - 30, p.x));
        p.y = Math.max(30, Math.min(h - 30, p.y));
      });

      // ── Draw ──
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);   // reset to DPR scale
      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(off.x, off.y);
      ctx.scale(zoom, zoom);

      // Edges
      ctx.strokeStyle = "rgba(100,116,139,0.35)";
      ctx.lineWidth = 0.8;
      edges.forEach((e) => {
        const a = pos.get(e.source);
        const b = pos.get(e.target);
        if (!a || !b) return;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      });

      // Nodes + labels
      nodes.forEach((n) => {
        const p = pos.get(n.id);
        if (!p) return;
        const r = Math.min(5 + (n.mention_count || 1) * 1.2, 18);
        const color = getColor(n.type);

        // Glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, r + 3, 0, Math.PI * 2);
        ctx.fillStyle = color + "22";
        ctx.fill();

        // Circle
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = color + "88";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Label
        ctx.fillStyle = "#cbd5e1";
        ctx.font = "11px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(n.name.length > 18 ? n.name.slice(0, 16) + "…" : n.name, p.x, p.y + r + 14);
      });

      ctx.restore();
      frameRef.current = requestAnimationFrame(draw);
    };

    frameRef.current = requestAnimationFrame(draw);
    return () => { running = false; cancelAnimationFrame(frameRef.current); };
  }, [getColor]);

  // ── Mouse handlers for drag panning ──
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragRef.current = { dragging: true, lastX: e.clientX, lastY: e.clientY };
  }, []);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragRef.current.dragging) return;
    const dx = e.clientX - dragRef.current.lastX;
    const dy = e.clientY - dragRef.current.lastY;
    offsetRef.current = {
      x: offsetRef.current.x + dx,
      y: offsetRef.current.y + dy,
    };
    dragRef.current.lastX = e.clientX;
    dragRef.current.lastY = e.clientY;
  }, []);

  const onMouseUp = useCallback(() => {
    dragRef.current.dragging = false;
  }, []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    zoomRef.current = Math.max(0.2, Math.min(4, zoomRef.current + delta));
    forceRender((n) => n + 1);
  }, []);

  const handleZoomIn = useCallback(() => {
    zoomRef.current = Math.min(4, zoomRef.current + 0.25);
    forceRender((n) => n + 1);
  }, []);

  const handleZoomOut = useCallback(() => {
    zoomRef.current = Math.max(0.2, zoomRef.current - 0.25);
    forceRender((n) => n + 1);
  }, []);

  const handleReset = useCallback(() => {
    zoomRef.current = 1;
    offsetRef.current = { x: 0, y: 0 };
    tickRef.current = 0;
    forceRender((n) => n + 1);
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full"
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
      onWheel={onWheel}
      style={{ cursor: dragRef.current.dragging ? "grabbing" : "grab" }}
    >
      <canvas ref={canvasRef} />
      <div className="absolute top-3 right-3 flex gap-1">
        <button onClick={handleZoomIn} className="bg-card/80 backdrop-blur border border-border rounded p-1.5 hover:bg-accent/20 transition-colors">
          <ZoomIn className="w-4 h-4" />
        </button>
        <button onClick={handleZoomOut} className="bg-card/80 backdrop-blur border border-border rounded p-1.5 hover:bg-accent/20 transition-colors">
          <ZoomOut className="w-4 h-4" />
        </button>
        <button onClick={handleReset} className="bg-card/80 backdrop-blur border border-border rounded p-1.5 hover:bg-accent/20 transition-colors">
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default function GraphPage() {
  const { data, loading } = useFetch(() => getGraph(200));
  const { data: gstats } = useFetch(getGraphStats);

  const statsLine = useMemo(() => {
    if (!data) return "Loading…";
    const parts = [`${data.nodes.length} nodes`, `${data.edges.length} edges`];
    if (gstats) {
      const gs = gstats as Record<string, unknown>;
      if (gs.connected_components) parts.push(`${gs.connected_components} components`);
    }
    return parts.join(" · ");
  }, [data, gstats]);

  return (
    <div className="animate-fade-in h-[calc(100vh-6rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold">Knowledge Graph</h2>
          <p className="text-sm text-muted mt-1">{statsLine}</p>
        </div>
      </div>

      <div className="flex-1 bg-card border border-border rounded-xl overflow-hidden min-h-0">
        {loading || !data ? (
          <div className="flex items-center justify-center h-full text-muted">Loading graph…</div>
        ) : data.nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted">No graph data yet. Ingest some files first.</div>
        ) : (
          <GraphCanvas data={data} />
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-muted flex-wrap">
        {Object.entries(TYPE_COLORS).filter(([k]) => k !== "default").map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}
