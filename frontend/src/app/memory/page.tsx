"use client";
import { useState } from "react";
import { useFetch } from "@/lib/hooks";
import { getTimeline, getMemoryDetail, type TimelineItem, type MemoryDetail } from "@/lib/api";
import { Clock, FileText, Image, Mic, FileCode, ChevronRight, X, Tag } from "lucide-react";

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
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">Memory Timeline</h2>
          <p className="text-sm text-muted mt-1">All your ingested knowledge, chronologically</p>
        </div>
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search memories..."
          className="bg-card border border-border rounded-lg px-3 py-2 text-sm w-64 outline-none focus:border-accent/50"
        />
      </div>

      {loading && <p className="text-muted text-sm">Loading...</p>}

      <div className="space-y-3">
        {data?.items.map((item) => (
          <button
            key={item.id}
            onClick={() => openDetail(item.id)}
            className="w-full text-left bg-card border border-border rounded-xl p-4 hover:border-accent/30 transition-colors flex items-center gap-4 group"
          >
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center text-accent-light shrink-0">
              {modalityIcon(item.modality)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium truncate">{item.title}</h3>
                <span className="text-[10px] uppercase tracking-wider text-muted bg-background px-1.5 py-0.5 rounded">{item.modality}</span>
                {item.category && <span className="text-[10px] uppercase tracking-wider text-accent-light bg-accent/10 px-1.5 py-0.5 rounded">{item.category}</span>}
              </div>
              {item.summary && <p className="text-xs text-muted mt-1 line-clamp-1">{item.summary}</p>}
              <div className="flex items-center gap-2 mt-1.5">
                <Clock className="w-3 h-3 text-muted" />
                <span className="text-[11px] text-muted">{new Date(item.ingested_at).toLocaleString()}</span>
                {item.entities.length > 0 && (
                  <>
                    <span className="text-muted">·</span>
                    <Tag className="w-3 h-3 text-muted" />
                    <span className="text-[11px] text-muted">{item.entities.slice(0, 3).join(", ")}</span>
                  </>
                )}
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-muted group-hover:text-foreground transition-colors" />
          </button>
        ))}
      </div>

      {data && data.total > 20 && (
        <div className="flex items-center justify-center gap-3 mt-6">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="px-3 py-1.5 text-sm bg-card border border-border rounded-lg disabled:opacity-30">Prev</button>
          <span className="text-sm text-muted">Page {page} of {Math.ceil(data.total / 20)}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={page >= Math.ceil(data.total / 20)} className="px-3 py-1.5 text-sm bg-card border border-border rounded-lg disabled:opacity-30">Next</button>
        </div>
      )}

      {/* Detail modal */}
      {detail && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setDetail(null)}>
          <div className="bg-card border border-border rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold">{detail.filename}</h3>
              <button onClick={() => setDetail(null)}><X className="w-5 h-5 text-muted hover:text-foreground" /></button>
            </div>
            <div className="flex flex-wrap gap-2 mb-3">
              <span className="text-xs bg-accent/10 text-accent-light px-2 py-0.5 rounded">{detail.modality}</span>
              <span className="text-xs bg-background text-muted px-2 py-0.5 rounded">{detail.status}</span>
              {detail.category && <span className="text-xs bg-accent/10 text-accent-light px-2 py-0.5 rounded">{detail.category}</span>}
            </div>
            {detail.summary && <p className="text-sm text-muted mb-4">{detail.summary}</p>}
            {detail.entities.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-medium mb-1">Entities</p>
                <div className="flex flex-wrap gap-1">{detail.entities.map((e) => <span key={e} className="text-[10px] bg-background text-muted px-1.5 py-0.5 rounded">{e}</span>)}</div>
              </div>
            )}
            {detail.action_items.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-medium mb-1">Action Items</p>
                <ul className="list-disc list-inside text-sm text-muted">{detail.action_items.map((a, i) => <li key={i}>{a}</li>)}</ul>
              </div>
            )}
            <div>
              <p className="text-xs font-medium mb-2">Chunks ({detail.chunks.length})</p>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {detail.chunks.map((c) => (
                  <div key={c.id} className="bg-background rounded-lg p-3 text-xs text-muted">
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
