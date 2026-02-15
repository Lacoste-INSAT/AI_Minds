"use client";
import { useState } from "react";
import { useFetch } from "@/lib/hooks";
import { getTimeline, getMemoryDetail, type TimelineItem, type MemoryDetail } from "@/lib/api";
import { Clock, FileText, Image, Mic, FileCode, ChevronRight, X, Tag, Database } from "lucide-react";

const modalityIcon = (m: string) => {
  if (m === "text") return <FileText className="w-4 h-4" />;
  if (m === "pdf") return <FileCode className="w-4 h-4" />;
  if (m === "image") return <Image className="w-4 h-4" />;
  if (m === "audio") return <Mic className="w-4 h-4" />;
  return <FileText className="w-4 h-4" />;
};

export default function MemoryPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<MemoryDetail | null>(null);
  const { data, loading, refetch } = useFetch(() => getTimeline(page, 20, search ? { search } : undefined), [page, search]);

  const openDetail = async (id: string) => {
    try {
      const d = await getMemoryDetail(id);
      setDetail(d);
    } catch { /* ignore */ }
  };

  return (
    <div className="animate-fade-in relative max-w-6xl mx-auto w-full">
      {/* Background blobs */}
      <div className="pointer-events-none absolute -top-20 -left-20 w-[400px] h-[400px] rounded-full bg-purple-500/[0.03] blur-3xl animate-float" />
      <div className="pointer-events-none absolute top-60 -right-32 w-[350px] h-[350px] rounded-full bg-accent/[0.03] blur-3xl animate-float-delay" />

      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl gradient-border p-6 mb-6 animate-hero-reveal"
           style={{ background: "linear-gradient(135deg, rgba(139,92,246,0.08) 0%, rgba(99,102,241,0.04) 50%, rgba(17,24,39,0.95) 100%)" }}>
        <div className="absolute top-0 h-full w-[20%] bg-gradient-to-r from-transparent via-purple-500/[0.04] to-transparent animate-scanline pointer-events-none" />
        <div className="relative z-10 flex items-end justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-2 h-2 rounded-full bg-purple-400 animate-breathe" />
              <span className="text-[11px] uppercase tracking-[0.2em] text-purple-400/70 font-medium">Knowledge Store</span>
            </div>
            <h2 className="text-3xl font-extrabold bg-gradient-to-r from-white via-purple-200 to-indigo-300 bg-clip-text text-transparent animate-gradient-text">
              Memory Timeline
            </h2>
            <p className="text-sm text-muted/80 mt-1.5">All your ingested knowledge, chronologically organized</p>
          </div>
          <div className="flex items-center gap-3">
            {data && (
              <div className="flex items-center gap-2 text-xs text-muted bg-white/[0.03] px-3 py-1.5 rounded-lg ring-1 ring-white/[0.06]">
                <Database className="w-3.5 h-3.5 text-purple-400" />
                <span>{data.total} memories</span>
              </div>
            )}
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search memories..."
              className="glass ring-1 ring-white/[0.06] focus:ring-accent/40 rounded-lg px-3 py-2 text-sm w-64 outline-none transition-all"
            />
          </div>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-purple-500/30 to-transparent" />
      </div>

      {loading && <div className="glass rounded-xl p-4 text-sm text-muted animate-shimmer">Loading memories...</div>}

      <div className="space-y-3">
        {data?.items.map((item, i) => (
          <button
            key={item.id}
            onClick={() => openDetail(item.id)}
            className="w-full text-left glass rounded-2xl gradient-border p-4 hover:ring-1 hover:ring-accent/20 transition-all duration-300 hover:translate-y-[-1px] flex items-center gap-4 group animate-slide-up"
            style={{ animationDelay: `${i * 50}ms` }}
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent/20 to-purple-500/10 flex items-center justify-center text-accent-light shrink-0 ring-1 ring-accent/10">
              {modalityIcon(item.modality)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium truncate">{item.title}</h3>
                <span className="text-[10px] uppercase tracking-wider text-muted bg-white/[0.04] px-1.5 py-0.5 rounded ring-1 ring-white/[0.06]">{item.modality}</span>
                {item.category && <span className="text-[10px] uppercase tracking-wider text-accent-light bg-accent/10 px-1.5 py-0.5 rounded">{item.category}</span>}
              </div>
              {item.summary && <p className="text-xs text-muted mt-1 line-clamp-1">{item.summary}</p>}
              <div className="flex items-center gap-2 mt-1.5">
                <Clock className="w-3 h-3 text-muted" />
                <span className="text-[11px] text-muted">{new Date(item.ingested_at).toLocaleString()}</span>
                {item.entities.length > 0 && (
                  <>
                    <span className="text-muted/40">·</span>
                    <Tag className="w-3 h-3 text-muted" />
                    <span className="text-[11px] text-muted">{item.entities.slice(0, 3).join(", ")}</span>
                  </>
                )}
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-muted group-hover:text-accent-light group-hover:translate-x-0.5 transition-all" />
          </button>
        ))}
      </div>

      {data && data.total > 20 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="px-3 py-1.5 text-sm glass rounded-lg ring-1 ring-white/[0.06] hover:ring-accent/20 disabled:opacity-30 transition-all">Prev</button>
          <span className="text-sm text-muted">Page {page} of {Math.ceil(data.total / 20)}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={page >= Math.ceil(data.total / 20)} className="px-3 py-1.5 text-sm glass rounded-lg ring-1 ring-white/[0.06] hover:ring-accent/20 disabled:opacity-30 transition-all">Next</button>
        </div>
      )}

      {/* Detail modal */}
      {detail && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setDetail(null)}>
          <div className="glass rounded-2xl gradient-border max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6 animate-slide-up" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent">{detail.filename}</h3>
              <button onClick={() => setDetail(null)} className="w-8 h-8 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] flex items-center justify-center transition-colors"><X className="w-4 h-4 text-muted hover:text-foreground" /></button>
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              <span className="text-xs bg-accent/10 text-accent-light px-2.5 py-1 rounded-lg ring-1 ring-accent/20">{detail.modality}</span>
              <span className="text-xs bg-white/[0.04] text-muted px-2.5 py-1 rounded-lg ring-1 ring-white/[0.06]">{detail.status}</span>
              {detail.category && <span className="text-xs bg-accent/10 text-accent-light px-2.5 py-1 rounded-lg ring-1 ring-accent/20">{detail.category}</span>}
            </div>
            {detail.summary && <p className="text-sm text-muted mb-4">{detail.summary}</p>}
            {detail.entities.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1 h-3 rounded-full bg-gradient-to-b from-accent to-purple-500" />
                  <p className="text-xs font-semibold">Entities</p>
                </div>
                <div className="flex flex-wrap gap-1.5">{detail.entities.map((e) => <span key={e} className="text-[10px] bg-white/[0.04] text-muted px-2 py-1 rounded-lg ring-1 ring-white/[0.06]">{e}</span>)}</div>
              </div>
            )}
            {detail.action_items.length > 0 && (
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-1 h-3 rounded-full bg-gradient-to-b from-amber-400 to-orange-500" />
                  <p className="text-xs font-semibold">Action Items</p>
                </div>
                <ul className="list-disc list-inside text-sm text-muted">{detail.action_items.map((a, i) => <li key={i}>{a}</li>)}</ul>
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-1 h-3 rounded-full bg-gradient-to-b from-cyan-400 to-blue-500" />
                <p className="text-xs font-semibold">Chunks ({detail.chunks.length})</p>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {detail.chunks.map((c) => (
                  <div key={c.id} className="bg-white/[0.02] rounded-xl p-3 text-xs text-muted ring-1 ring-white/[0.04]">
                    <span className="text-accent-light font-mono">#{c.chunk_index}</span>
                    <p className="mt-1 whitespace-pre-wrap">{c.content.slice(0, 300)}{c.content.length > 300 ? "…" : ""}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
