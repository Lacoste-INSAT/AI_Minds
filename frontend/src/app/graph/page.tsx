"use client";
import { useEffect, useRef, useState } from "react";
import { useFetch } from "@/lib/hooks";
import { getGraph, getGraphStats, type GraphData, type GraphNode, type GraphEdge } from "@/lib/api";
import { Maximize2, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

// Simple force-directed layout rendered on canvas
function GraphCanvas({ data }: { data: GraphData }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const posRef = useRef<Map<string, { x: number; y: number; vx: number; vy: number }>>(new Map());

  const typeColors: Record<string, string> = {
    person: "#6366f1", organization: "#22c55e", concept: "#f59e0b",
    location: "#3b82f6", event: "#ef4444", technology: "#8b5cf6",
    work_of_art: "#ec4899", group: "#14b8a6", date: "#f97316",
    email: "#06b6d4", url: "#a855f7", phone: "#84cc16",
    default: "#64748b",
  };

  const getColor = (type: string) => typeColors[type.toLowerCase()] || typeColors.default;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data.nodes.length) return;

    const ctx = canvas.getContext("2d")!;
    const W = canvas.width = canvas.clientWidth * window.devicePixelRatio;
    const H = canvas.height = canvas.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;

    // Init positions
    const pos = posRef.current;
    data.nodes.forEach((n) => {
      if (!pos.has(n.id)) {
        pos.set(n.id, {
          x: w / 2 + (Math.random() - 0.5) * w * 0.6,
          y: h / 2 + (Math.random() - 0.5) * h * 0.6,
          vx: 0, vy: 0,
        });
      }
    });

    const edgeIndex = new Map<string, string>();
    data.edges.forEach((e) => edgeIndex.set(e.source + "-" + e.target, e.relationship));

    let frame: number;
    let ticks = 0;

    const simulate = () => {
      ticks++;
      const alpha = Math.max(0.001, 1 - ticks / 300);

      // Repulsion
      const nodes = data.nodes;
      for (let i = 0; i < nodes.length; i++) {
        const a = pos.get(nodes[i].id)!;
        for (let j = i + 1; j < nodes.length; j++) {
          const b = pos.get(nodes[j].id)!;
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1);
          const force = (800 / (dist * dist)) * alpha;
          dx *= force; dy *= force;
          a.vx += dx; a.vy += dy;
          b.vx -= dx; b.vy -= dy;
        }
      }

      // Attraction
      data.edges.forEach((e) => {
        const a = pos.get(e.source);
        const b = pos.get(e.target);
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const force = (dist - 80) * 0.01 * alpha;
        const fx = dx / dist * force;
        const fy = dy / dist * force;
        a.vx += fx; a.vy += fy;
        b.vx -= fx; b.vy -= fy;
      });

      // Center gravity
      nodes.forEach((n) => {
        const p = pos.get(n.id)!;
        p.vx += (w / 2 - p.x) * 0.001 * alpha;
        p.vy += (h / 2 - p.y) * 0.001 * alpha;
      });

      // Apply & dampen
      nodes.forEach((n) => {
        const p = pos.get(n.id)!;
        p.vx *= 0.6; p.vy *= 0.6;
        p.x += p.vx; p.y += p.vy;
        p.x = Math.max(20, Math.min(w - 20, p.x));
        p.y = Math.max(20, Math.min(h - 20, p.y));
      });

      // Draw
      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.translate(offset.x, offset.y);
      ctx.scale(zoom, zoom);

      // Edges
      ctx.strokeStyle = "#1e293b";
      ctx.lineWidth = 1;
      data.edges.forEach((e) => {
        const a = pos.get(e.source);
        const b = pos.get(e.target);
        if (!a || !b) return;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      });

      // Nodes
      nodes.forEach((n) => {
        const p = pos.get(n.id)!;
        const r = Math.min(4 + n.mention_count * 1.5, 16);
        const color = getColor(n.type);
        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        // Label
        ctx.fillStyle = "#94a3b8";
        ctx.font = "10px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(n.name.slice(0, 16), p.x, p.y + r + 12);
      });

      ctx.restore();
      if (ticks < 400) frame = requestAnimationFrame(simulate);
    };

    frame = requestAnimationFrame(simulate);
    return () => cancelAnimationFrame(frame);
  }, [data, zoom, offset]);

  return (
    <div className="relative w-full h-full">
      <canvas ref={canvasRef} className="w-full h-full" />
      <div className="absolute top-3 right-3 flex gap-1">
        <button onClick={() => setZoom((z) => Math.min(3, z + 0.2))} className="bg-card border border-border rounded p-1.5"><ZoomIn className="w-4 h-4" /></button>
        <button onClick={() => setZoom((z) => Math.max(0.3, z - 0.2))} className="bg-card border border-border rounded p-1.5"><ZoomOut className="w-4 h-4" /></button>
        <button onClick={() => { setZoom(1); setOffset({ x: 0, y: 0 }); }} className="bg-card border border-border rounded p-1.5"><RotateCcw className="w-4 h-4" /></button>
      </div>
    </div>
  );
}

export default function GraphPage() {
  const { data, loading } = useFetch(() => getGraph(150));
  const { data: gstats } = useFetch(getGraphStats);

  return (
    <div className="animate-fade-in h-[calc(100vh-6rem)] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold">Knowledge Graph</h2>
          <p className="text-sm text-muted mt-1">
            {data ? `${data.nodes.length} nodes, ${data.edges.length} edges` : "Loading..."}
          </p>
        </div>
      </div>

      <div className="flex-1 bg-card border border-border rounded-xl overflow-hidden">
        {loading || !data ? (
          <div className="flex items-center justify-center h-full text-muted">Loading graph...</div>
        ) : data.nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted">No graph data yet. Ingest some files first.</div>
        ) : (
          <GraphCanvas data={data} />
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-muted flex-wrap">
        {[
          ["person", "#6366f1"], ["organization", "#22c55e"], ["concept", "#f59e0b"],
          ["location", "#3b82f6"], ["event", "#ef4444"], ["technology", "#8b5cf6"],
          ["work_of_art", "#ec4899"], ["group", "#14b8a6"], ["date", "#f97316"],
        ].map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  );
}
